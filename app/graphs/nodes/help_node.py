def help_node(state: dict) -> dict:
    msg = (
        "I can help with:\n"
        "- Project data queries (readonly, MySQL)\n"
        "- Excel exports\n"
        "- Emailing reports\n"
        "Try: 'List top 10 closed projects and email to ops@abc.com'"
    )
    return {**state, "response": msg}
