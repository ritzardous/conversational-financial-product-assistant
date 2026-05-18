"""
LLM prompt builder. The LLM only does ONE job: turn structured context into
a natural-sounding reply string. All logic (eligibility, missing fields,
matched products) is already computed and handed in.
"""

import json
from .products import PRODUCTS


PRODUCTS_BLOCK = json.dumps(PRODUCTS, indent=2)


def build_phrasing_prompt(user_message: str, logic_context: dict, profile: dict) -> str:
    """
    Builds the user-turn message sent to the LLM.
    The LLM receives: the product catalogue, the pre-computed logic result,
    the user's known profile, and the raw user message.
    It must ONLY return a JSON object with a single key: "reply".
    """
    return f"""
## Product Catalogue (ground truth — do not invent anything outside this)
{PRODUCTS_BLOCK}

## User's Known Profile
{json.dumps(profile, indent=2)}

## Pre-computed Logic Result
{json.dumps(logic_context, indent=2)}

## User's Message
"{user_message}"

## Your Task
Write a helpful, conversational reply to the user based ONLY on the pre-computed logic result and the product catalogue above. Do not re-evaluate eligibility or invent any product details — the logic result is authoritative.

Rules:
- If requires_more_info is true, ask only for the fields listed in missing_fields.
- If eligible is false for a product, name the specific failing criteria from failed_fields.
- If intent is out_of_scope, politely decline and say you only cover the three listed products.
- If intent is comparison, compare the matched_products side by side on benefits, fees, and eligibility thresholds.
- Keep tone friendly and concise.
- Ground every factual claim in the product catalogue.

Respond with ONLY valid JSON, no markdown fences:
{{"reply": "<your natural language reply here>"}}
"""


SYSTEM_PROMPT = """You are a financial assistant for Kyma. You help users understand three financial products.
You will receive pre-computed logic results. Your ONLY job is to phrase a clear, friendly reply based on those results.
Never invent product details. Never re-evaluate eligibility yourself — trust the logic result provided.
Always respond with ONLY a JSON object: {"reply": "..."}"""