"""
Pure Python logic layer — no LLM involved.
Handles: slot extraction, intent detection, eligibility, product matching, missing fields.
"""

import re
from .products import PRODUCTS, PRODUCTS_BY_ID, PRODUCT_REQUIRED_FIELDS

# ---------------------------------------------------------------------------
# Slot extraction
# ---------------------------------------------------------------------------

def extract_slots(text: str) -> dict:
    """
    Pull age, monthly_income, credit_score out of free text using regex.
    Returns only the fields that were actually found.
    """
    found = {}
    t = text.lower()

    # Age: "I am 26", "age is 26", "26 years old", "i'm 26"
    age_patterns = [
        r"i(?:'m| am)\s+(\d{2})\b",
        r"\bage(?:\s+is)?\s*[:\-]?\s*(\d{2})\b",
        r"(\d{2})\s+years?\s+old",
    ]
    for pat in age_patterns:
        m = re.search(pat, t)
        if m:
            found["age"] = int(m.group(1))
            break

    # Monthly income: "earn 60000", "income is 60000", "salary 60000", "make 60000"
    income_patterns = [
        r"(?:earn|salary|income|make|making|get|getting|paid)\s*(?:is|of|about|around|:)?\s*(?:rs\.?|inr|₹)?\s*(\d[\d,]+)",
        r"(?:rs\.?|inr|₹)\s*(\d[\d,]+)\s*(?:per\s+month|pm|monthly|\/month)?",
        r"monthly\s+income\s*(?:is|of|:)?\s*(?:rs\.?|inr|₹)?\s*(\d[\d,]+)",
        r"income\s*(?:is|of|:)?\s*(?:rs\.?|inr|₹)?\s*(\d[\d,]+)",
    ]
    for pat in income_patterns:
        m = re.search(pat, t)
        if m:
            raw = m.group(1).replace(",", "")
            found["monthly_income"] = int(raw)
            break

    # Credit score: "credit score is 720", "cibil 720", "score 720"
    score_patterns = [
        r"(?:credit\s+score|cibil|score)\s*(?:is|of|:)?\s*(\d{3})\b",
        r"(\d{3})\s+(?:credit\s+score|cibil)",
    ]
    for pat in score_patterns:
        m = re.search(pat, t)
        if m:
            val = int(m.group(1))
            if 300 <= val <= 900:          # plausible credit score range
                found["credit_score"] = val
                break

    return found


# ---------------------------------------------------------------------------
# Intent detection
# ---------------------------------------------------------------------------

CARD_KEYWORDS = {
    "travel_card":   ["travel", "lounge", "airport", "flight", "forex", "trip", "traveller", "traveling"],
    "cashback_card": ["cashback", "cash back", "online shopping", "grocery", "groceries", "bill", "daily spend"],
    "personal_loan": ["loan", "personal loan", "borrow", "cash need", "collateral", "lend"],
}

COMPARISON_PHRASES = ["compare", "comparison", "vs", "versus", "difference between", "which is better"]
ELIGIBILITY_PHRASES = ["eligible", "eligibility", "qualify", "can i get", "do i qualify", "am i"]
FEE_PHRASES = ["fee", "fees", "annual fee", "charge", "cost", "processing fee"]

OUT_OF_SCOPE_KEYWORDS = [
    "stock", "share", "equity", "crypto", "bitcoin", "mutual fund",
    "mortgage", "tax", "insurance", "fd", "fixed deposit", "nps",
    "trading", "invest", "portfolio",
]


def detect_intent(text: str) -> dict:
    """
    Returns:
        {
          "intent": one of "product_info" | "eligibility" | "comparison" | "fees" | "out_of_scope" | "general",
          "mentioned_products": [list of product_ids],
        }
    """
    t = text.lower()

    # Out-of-scope check first
    if any(kw in t for kw in OUT_OF_SCOPE_KEYWORDS):
        return {"intent": "out_of_scope", "mentioned_products": []}

    mentioned = []
    for pid, kws in CARD_KEYWORDS.items():
        if any(kw in t for kw in kws):
            mentioned.append(pid)

    if any(p in COMPARISON_PHRASES for p in [t] + [t[i:] for i in range(len(t))]):
        # crude substring check
        if any(phrase in t for phrase in COMPARISON_PHRASES) and len(mentioned) >= 1:
            if len(mentioned) == 1:
                # user said "compare travel card and cashback card" — both should be caught by keywords
                # if only one detected, add the other common pair
                pass
            return {"intent": "comparison", "mentioned_products": mentioned}

    if any(phrase in t for phrase in FEE_PHRASES):
        return {"intent": "fees", "mentioned_products": mentioned}

    if any(phrase in t for phrase in ELIGIBILITY_PHRASES):
        return {"intent": "eligibility", "mentioned_products": mentioned}

    if mentioned:
        return {"intent": "product_info", "mentioned_products": mentioned}

    return {"intent": "general", "mentioned_products": []}


# ---------------------------------------------------------------------------
# Eligibility engine
# ---------------------------------------------------------------------------

def check_eligibility(product_id: str, profile: dict) -> dict:
    """
    Returns:
        {
          "missing_fields": [...],   # fields we don't have yet
          "failed_fields": {...},    # fields we have but fail the threshold
          "eligible": bool | None    # None means we can't determine yet
        }
    """
    required = PRODUCT_REQUIRED_FIELDS.get(product_id, [])
    product = PRODUCTS_BY_ID[product_id]
    elig = product["eligibility"]

    missing = [f for f in required if profile.get(f) is None]
    if missing:
        return {"missing_fields": missing, "failed_fields": {}, "eligible": None}

    failed = {}

    if "age" in required:
        age = profile["age"]
        if "min_age" in elig and age < elig["min_age"]:
            failed["age"] = f"minimum age is {elig['min_age']}, yours is {age}"
        if "max_age" in elig and age > elig["max_age"]:
            failed["age"] = f"maximum age is {elig['max_age']}, yours is {age}"

    if "monthly_income" in required:
        inc = profile["monthly_income"]
        if inc < elig["min_monthly_income"]:
            failed["monthly_income"] = f"minimum income is ₹{elig['min_monthly_income']}, yours is ₹{inc}"

    if "credit_score" in required:
        cs = profile.get("credit_score")
        if cs is not None and cs < elig["min_credit_score"]:
            failed["credit_score"] = f"minimum credit score is {elig['min_credit_score']}, yours is {cs}"

    eligible = len(failed) == 0
    return {"missing_fields": [], "failed_fields": failed, "eligible": eligible}


# ---------------------------------------------------------------------------
# High-level decision function (called by app.py)
# ---------------------------------------------------------------------------

def process_message(user_message: str, profile: dict) -> dict:
    """
    Pure logic pass. Returns a structured context dict that app.py
    will pass to the LLM for phrasing.

    Returns:
    {
      "intent": str,
      "mentioned_products": [str],
      "eligibility_results": {product_id: {missing, failed, eligible}},
      "requires_more_info": bool,
      "missing_fields": [str],
      "matched_products": [str],
      "new_slots": {field: value},   # slots extracted from this message
    }
    """
    new_slots = extract_slots(user_message)
    merged_profile = {**profile, **new_slots}   # latest value wins

    intent_data = detect_intent(user_message)
    intent = intent_data["intent"]
    mentioned = intent_data["mentioned_products"]

    # Default result shape
    result = {
        "intent": intent,
        "mentioned_products": mentioned,
        "eligibility_results": {},
        "requires_more_info": False,
        "missing_fields": [],
        "matched_products": [],
        "new_slots": new_slots,
        "merged_profile": merged_profile,
    }

    if intent == "out_of_scope":
        return result

    if intent == "eligibility":
        targets = mentioned if mentioned else list(PRODUCTS_BY_ID.keys())
        all_missing = []
        elig_results = {}
        for pid in targets:
            er = check_eligibility(pid, merged_profile)
            elig_results[pid] = er
            all_missing.extend(er["missing_fields"])

        # deduplicate while preserving order
        seen = set()
        deduped_missing = []
        for f in all_missing:
            if f not in seen:
                seen.add(f)
                deduped_missing.append(f)

        result["eligibility_results"] = elig_results
        result["missing_fields"] = deduped_missing
        result["requires_more_info"] = len(deduped_missing) > 0
        result["matched_products"] = targets
        return result

    if intent == "comparison":
        result["matched_products"] = mentioned if len(mentioned) >= 2 else ["travel_card", "cashback_card"]
        return result

    if intent == "fees":
        result["matched_products"] = mentioned
        return result

    if intent == "product_info":
        result["matched_products"] = mentioned
        return result

    # general — let LLM handle
    return result