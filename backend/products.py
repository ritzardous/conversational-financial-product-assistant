PRODUCTS = [
    {
        "id": "travel_card",
        "name": "Travel Credit Card",
        "description": "Useful for frequent travellers. Offers airport lounge access, reward points on flights, travel insurance, and low forex markup.",
        "eligibility": {"min_age": 21, "max_age": 60, "min_monthly_income": 50000},
        "fees": "Annual fee ₹2,999",
        "benefits": [
            "4 lounge visits per quarter",
            "5x rewards on flights",
            "Travel insurance",
            "1% forex markup",
        ],
    },
    {
        "id": "cashback_card",
        "name": "Cashback Credit Card",
        "description": "Useful for online shopping, groceries, bill payments, and daily spends.",
        "eligibility": {"min_age": 21, "max_age": 60, "min_monthly_income": 30000},
        "fees": "Annual fee ₹999",
        "benefits": [
            "5% cashback online",
            "1% cashback offline",
            "Fuel surcharge waiver",
        ],
    },
    {
        "id": "personal_loan",
        "name": "Personal Loan",
        "description": "Useful for short-term cash needs. No collateral required.",
        "eligibility": {"min_monthly_income": 40000, "min_credit_score": 700},
        "fees": "Processing fee 1.5%",
        "benefits": ["Instant approval", "Flexible tenure", "No collateral"],
    },
]

# Fields each product actually needs for eligibility checks
PRODUCT_REQUIRED_FIELDS = {
    "travel_card":    ["age", "monthly_income"],
    "cashback_card":  ["age", "monthly_income"],
    "personal_loan":  ["monthly_income", "credit_score"],
}

# Map product_id -> product dict for quick lookup
PRODUCTS_BY_ID = {p["id"]: p for p in PRODUCTS}