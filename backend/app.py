import os
import json
import re
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from groq import Groq

from .logic import process_message
from .memory import get_user_state, update_profile, append_message, reset_user
from .prompts import build_phrasing_prompt, SYSTEM_PROMPT

# Load environment variables
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

app = Flask(__name__)
CORS(app)

# Initialize Groq client
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400

        user_id = data.get("user_id")
        message = data.get("message")

        # Validation: Return HTTP 400 JSON error if either field is missing or empty string
        if not user_id or not message or not isinstance(user_id, str) or not isinstance(message, str):
            return jsonify({"error": "Missing or empty user_id or message"}), 400
        
        user_id = user_id.strip()
        message = message.strip()
        if not user_id or not message:
            return jsonify({"error": "Missing or empty user_id or message"}), 400

        # 1. Get user state
        state = get_user_state(user_id)

        # 2. Compute logic context
        logic_context = process_message(message, state["profile"])

        # 3. Update profile
        update_profile(user_id, logic_context["new_slots"])

        # 4. Append user message
        append_message(user_id, "user", message)

        # 5. Build enriched prompt
        enriched_prompt = build_phrasing_prompt(
            message,
            logic_context,
            logic_context["merged_profile"]
        )

        # 6. Construct llm_messages
        # (This replaces the raw user message just appended with the enriched prompt for the LLM)
        llm_messages = state["messages"][:-1] + [{
            "role": "user",
            "content": enriched_prompt
        }]

        # 7. Call Groq chat completions
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + llm_messages

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.2,
            max_tokens=512,
        )

        response_content = completion.choices[0].message.content

        # 8. Robustly parse the LLM response
        cleaned_content = response_content.strip()
        cleaned_content = re.sub(r"^```(?:json)?\s*", "", cleaned_content, flags=re.IGNORECASE)
        cleaned_content = re.sub(r"\s*```$", "", cleaned_content)

        try:
            parsed_json = json.loads(cleaned_content)
            reply = parsed_json.get("reply")
            if not reply:
                reply = "I'm sorry, I couldn't process that. Please try again."
        except json.JSONDecodeError:
            reply = "I'm sorry, I couldn't process that. Please try again."

        # 9. Append assistant reply
        append_message(user_id, "assistant", reply)

        # 10. Return HTTP 200
        return jsonify({
            "reply": reply,
            "matched_products": logic_context.get("matched_products", []),
            "requires_more_info": logic_context.get("requires_more_info", False),
            "missing_fields": logic_context.get("missing_fields", [])
        }), 200

    except Exception as e:
        print(f"Error in /chat endpoint: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/reset", methods=["POST"])
def reset():
    data = request.get_json()
    if not data or "user_id" not in data or not str(data["user_id"]).strip():
        return jsonify({"error": "Missing user_id"}), 400
        
    user_id = str(data["user_id"]).strip()
    reset_user(user_id)
    return jsonify({"status": "ok"}), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(debug=True, port=5000)
