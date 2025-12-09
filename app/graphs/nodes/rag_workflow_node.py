from app.models.llm.factory import get_llm

async def rag_qa_node(state):
    llm = get_llm()
    query = state["user_input"]
    rag_answer = query
    # rag_answer = run_rag(query)  # your existing RAG pipeline
    state["response"] = rag_answer
    return state
