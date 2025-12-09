def fallback_node(state: dict) -> dict:
    return {**state, "response": "Sorry, I didn't understand. Try asking about projects or say 'help'."}
