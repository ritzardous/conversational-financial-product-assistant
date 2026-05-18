"""Integration tests — Flask server must be running on localhost:5000 before running pytest."""
import requests
import uuid
import pytest

BASE = "http://localhost:5000"

def chat(user_id, message):
    response = requests.post(f"{BASE}/chat", json={"user_id": user_id, "message": message})
    response.raise_for_status()
    return response.json()

def reset(user_id):
    response = requests.post(f"{BASE}/reset", json={"user_id": user_id})
    response.raise_for_status()

def test_product_suggestion():
    user_id = str(uuid.uuid4())
    try:
        response = chat(user_id, "I travel a lot. Which product is useful for me?")
        assert "travel_card" in response["matched_products"]
        assert response["requires_more_info"] is False
    finally:
        reset(user_id)

def test_eligibility_missing_slots():
    user_id = str(uuid.uuid4())
    try:
        response = chat(user_id, "Am I eligible for the travel card?")
        assert response["requires_more_info"] is True
        assert "age" in response["missing_fields"]
        assert "monthly_income" in response["missing_fields"]
    finally:
        reset(user_id)

def test_multi_turn_memory():
    user_id = str(uuid.uuid4())
    try:
        # Turn 1
        chat(user_id, "I am 26 years old and earn 60000 per month.")
        
        # Turn 2
        response = chat(user_id, "Am I eligible for the travel card?")
        assert response["requires_more_info"] is False
        assert "travel_card" in response["matched_products"]
    finally:
        reset(user_id)

def test_negative_eligibility():
    user_id = str(uuid.uuid4())
    try:
        # Turn 1
        chat(user_id, "My age is 19 and my monthly income is 20000.")
        
        # Turn 2
        response = chat(user_id, "Am I eligible for the cashback card?")
        assert response["requires_more_info"] is False
        
        reply_lower = response["reply"].lower()
        substrings = [
            "not eligible",
            "below",
            "do not qualify",
            "doesn't meet",
            "does not meet",
            "minimum"
        ]
        assert any(sub in reply_lower for sub in substrings)
    finally:
        reset(user_id)

def test_comparison():
    user_id = str(uuid.uuid4())
    try:
        response = chat(user_id, "Compare travel card and cashback card.")
        assert "travel_card" in response["matched_products"]
        assert "cashback_card" in response["matched_products"]
        assert response["requires_more_info"] is False
    finally:
        reset(user_id)

def test_fees_lookup():
    user_id = str(uuid.uuid4())
    try:
        response = chat(user_id, "What is the fee for the cashback card?")
        assert "cashback_card" in response["matched_products"]
        assert response["requires_more_info"] is False
        assert response["missing_fields"] == []
    finally:
        reset(user_id)

def test_out_of_scope():
    user_id = str(uuid.uuid4())
    try:
        response = chat(user_id, "What is the best stock to buy today?")
        assert response["matched_products"] == []
        assert response["requires_more_info"] is False
    finally:
        reset(user_id)

def test_per_user_isolation():
    user_a = str(uuid.uuid4())
    user_b = str(uuid.uuid4())
    
    try:
        # Turn 1 user_a
        chat(user_a, "I am 30 years old and earn 70000 per month.")
        
        # Turn 2 user_b
        response = chat(user_b, "Am I eligible for the travel card?")
        assert response["requires_more_info"] is True
    finally:
        reset(user_a)
        reset(user_b)
