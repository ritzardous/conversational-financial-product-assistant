"""
In-memory store for per-user state.
Each user gets:
  {
    "messages": [{"role": "user"|"assistant", "content": "..."}],
    "profile":  {"age": int|None, "monthly_income": int|None, "credit_score": int|None}
  }
"""

_store: dict = {}


def get_user_state(user_id: str) -> dict:
    if user_id not in _store:
        _store[user_id] = {
            "messages": [],
            "profile": {"age": None, "monthly_income": None, "credit_score": None},
            "last_logic_context": None
        }
    return _store[user_id]


def get_last_logic_context(user_id: str):
    return get_user_state(user_id).get("last_logic_context")


def set_last_logic_context(user_id: str, logic_context: dict) -> None:
    get_user_state(user_id)["last_logic_context"] = logic_context


def update_profile(user_id: str, new_slots: dict) -> None:
    state = get_user_state(user_id)
    for field, value in new_slots.items():
        if value is not None:
            state["profile"][field] = value


def append_message(user_id: str, role: str, content: str) -> None:
    get_user_state(user_id)["messages"].append({"role": role, "content": content})


def reset_user(user_id: str) -> None:
    _store.pop(user_id, None)