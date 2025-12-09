from app.models.llm.factory import get_llm

SUMMARY_PROMPT = """
You are a helpful analyst. Based on the SQL and rows returned, summarize the key findings in 3-6 concise bullet points.
Format as plain text.
"""

async def summarize_results(user_question: str, sql: str, rows: list[dict]) -> str:
    llm = get_llm()
    content = (
        SUMMARY_PROMPT +
        f"\nUser question: {user_question}\nSQL: {sql}\nRows (first 10): {rows[:10]}\nSummary:"
    )
    return await llm.complete(content)
  