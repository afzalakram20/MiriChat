from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.documents import Document
from app.llms.runnable.llm_provider import get_chain_llm
from app.core.config import settings
from langchain_pinecone import PineconeVectorStore
from langchain_community.embeddings import HuggingFaceEmbeddings
import logging

log = logging.getLogger("app_info_node")


async def app_info_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Answers 'app_info' intent questions using RAG over the 'horizon-app-flow' Pinecone index.
    Keeps output concise and step-focused. Falls back gracefully when info is not found.
    """
    index_name = "horizon-app-flow"
    user_query = state.get("user_input") or ""

    log.info("app_info_node: start, index=%s", index_name)

    # Retriever
    embeddings = HuggingFaceEmbeddings(model_name=settings.HG_EMBEDDING_MODEL)
    vectorstore = PineconeVectorStore(
        index_name=index_name,
        embedding=embeddings,
        text_key="text",
        pinecone_api_key=settings.PINECONE_API_KEY,
    )
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
    docs: List[Document] = retriever.invoke(user_query)
    log.info("app_info_node: retrieved %d docs", len(docs))

    # Build minimal context
    context_chunks = []
    for idx, d in enumerate(docs):
        meta = d.metadata or {}
        src = meta.get("source") or meta.get("filename") or ""
        context_chunks.append(
            f"[DOC {idx+1} | {src}]\n{(d.page_content or '').strip()}"
        )
    retrieved_context = (
        "\n\n---\n\n".join(context_chunks)
        if context_chunks
        else "No relevant context found."
    )

    # LLM
    llm = get_chain_llm()
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a concise app help assistant. Answer ONLY using the provided context.\n"
                "If the exact answer is not clearly present, say you cannot find that exact information, then provide the closest relevant guidance if available.\n"
                "Do NOT mention 'docs' or 'documentation'. Map user wording to the app's terms when obvious (e.g., 'project request' -> 'Work Request').\n"
                "Do NOT SAY 'I can’t find exact step-by-step clicks for ...'"
                "Prefer step-by-step instructions and bullet lists.",
            ),
            MessagesPlaceholder("chat_history"),
            (
                "human",
                "User question:\n{question}\n\nContext:\n{context}\n\nAnswer:",
            ),
        ]
    )

    chain = prompt | llm
    try:
        answer = chain.invoke({
            "question": user_query,
            "context": retrieved_context,
            "chat_history": state.get("chat_history") or [],
        })
        # Some models return a message object; ensure string
        if hasattr(answer, "content"):
            answer = answer.content
        answer = (answer or "").strip()
    except Exception as e:
        log.exception("app_info_node: LLM failed")
        answer = (
            "Sorry, I couldn’t retrieve that information from the app documentation."
        )

    state["response"] = answer
    return state


from app.models.llm.factory import get_llm
import json


async def rag_workflow_node(state):
    llm = get_llm()
    query = state["user_input"]
    rag_answer = query
    # rag_answer = run_rag(query)  # your existing RAG pipeline
    state["response"] = rag_answer
    return state
