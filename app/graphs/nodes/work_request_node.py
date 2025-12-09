
from app.llms.runnable.llm_provider import get_chain_llm 
from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.documents import Document
from app.core.config import settings
from langchain_pinecone import PineconeVectorStore
from app.models.parsers.work_request_models import WorkRequestModel,LUMSUM_TYPE_ENUMS,DISCIPLINE_ENUMS,PROJECT_TYPE_ENUMS
from app.graphs.nodes.prompts.work_request_prompt import SYSTEM_MESSAGE
from langchain_community.embeddings import HuggingFaceEmbeddings
import logging
log = logging.getLogger("work_request_node")


 
async def work_request_node(state: Dict[str, Any]) -> Dict[str, Any]:
    pinecone_index_name ="horizon-work-order-scopes" 
  
    log.info("******* Entered work_request_node ********") 
    log.info(f"work_request_node: incoming state keys -> {list(state.keys())}")

   
    user_query = state.get("user_input")

    embeddings = HuggingFaceEmbeddings( model_name=settings.HG_EMBEDDING_MODEL)
    vectorstore = PineconeVectorStore(
        index_name=pinecone_index_name,
        embedding=embeddings,
        text_key="project_title",
        pinecone_api_key=settings.PINECONE_API_KEY, 
    )

    log.info("work_request_node: converting vectorstore to retriever (k=5)")
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
    llm=get_chain_llm() 
 
    parser = PydanticOutputParser(pydantic_object=WorkRequestModel)

    # -------------------------
    # Retrieve similar projects from Pinecone
    # -------------------------
    log.info("work_request_node: invoking retriever with user_query")
    docs: List[Document] = retriever.invoke(user_query)
    log.info(f"work_request_node: retrieved {len(docs)} docs from Pinecone")

    context_chunks = []
    for idx, d in enumerate(docs):
        meta_str = ", ".join(
            f"{k}: {v}"
            for k, v in d.metadata.items()
            if v is not None and v != ""
        )
        chunk = f"PROJECT #{idx + 1}\nSCOPE OF WORK:\n{d.page_content}\nMETADATA:\n{meta_str}"
        context_chunks.append(chunk)
        log.info(
            "work_request_node: built context chunk #%s with page_content_len=%s, metadata_keys=%s",
            idx + 1,
            len(d.page_content or ""),
            list(d.metadata.keys()),
        )

    retrieved_context = (
        "\n\n---\n\n".join(context_chunks) if context_chunks else "No similar projects found."
    )
    log.info(
        "work_request_node: final retrieved_context length -> %s",
        len(retrieved_context),
    )

    # -------------------------
    #  Prepare enums as prompt text
    # -------------------------
    log.info("work_request_node: building project_type_table_str from PROJECT_TYPE_ENUMS")
    project_type_table_str = "\n".join(
        f"- ID {item['id']}: {item['name']}"
        for item in PROJECT_TYPE_ENUMS
    )

    log.info("work_request_node: building discipline_table_str from DISCIPLINE_ENUMS")
    discipline_table_str = "\n".join(
        f"- ID {item['id']}: {item['name']}"
        for item in DISCIPLINE_ENUMS
    )

    log.info("work_request_node: building lumsum_table_str from LUMSUM_TYPE_ENUMS")
    lumsum_table_str = "\n".join(
        f"- ID {item['id']}: {item['name']}"
        for item in LUMSUM_TYPE_ENUMS
    )

    # -------------------------
    #  Prompt template
    # -------------------------
    log.info("work_request_node: fetching format_instructions from parser")
    format_instructions = parser.get_format_instructions()
    log.info(
        "work_request_node: format_instructions length -> %s",
        len(format_instructions),
    )

    log.info("work_request_node: constructing ChatPromptTemplate")
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_MESSAGE),
            ("human",
                (
                    "User description of the required work request:\n"
                    "{user_query}\n\n"
                    "Retrieved similar projects (scopes + metadata):\n"
                    "{retrieved_context}\n\n"
                    "Follow these format instructions exactly:\n"
                    "{format_instructions}"
                ),
            ),
        ]
    )

    # -------------------------
    #   Build chain (Runnable)
    # -------------------------
    log.info("work_request_node: building LCEL chain with prompt -> llm -> parser")

    chain = (
        prompt
        | llm
        | parser
    )

 
    chain_input = {
        "user_query": user_query,
        "retrieved_context": retrieved_context,
        "project_type_table": project_type_table_str,
        "discipline_table": discipline_table_str,
        "lumsum_table": lumsum_table_str,
        "format_instructions": format_instructions,
    }

    log.info(
        "work_request_node: invoking chain with user_query_len=%s, retrieved_context_len=%s",
        len(user_query),
        len(retrieved_context),
    )

    try:
        model_obj: WorkRequestModel = chain.invoke(chain_input)
        log.info("work_request_node: chain.invoke completed successfully")
    except Exception as e:
        log.exception("work_request_node: LLM or parser failed")
        raise

    # -------------------------
    #  Post-process & enforce enums on IDs
    # -------------------------
    log.info("work_request_node: converting WorkRequestModel to dict (with aliases)")
    data = model_obj.dict(by_alias=True)

    log.info(
        "work_request_node: raw model data keys -> %s",
        list(data.keys()),
    )

    

   
    

     
    qt_name = data.get("request_type_name")
    if qt_name: 
        for item in PROJECT_TYPE_ENUMS:
            if item["name"] == qt_name:
                data["request_type_id"] = item["id"] 
                break
        else:
            log.warning(
                "work_request_node: request_type_name %r not found in PROJECT_TYPE_ENUMS",
                qt_name,
            )

 
    ls_name = data.get("lumsum_type_name")
    if ls_name: 
        for item in LUMSUM_TYPE_ENUMS:
            if item["name"] == ls_name:
                data["lumsum_type_id"] = item["id"]
                log.info(
                    "work_request_node: lumsum_type matched enum -> id=%s",
                    item["id"],
                )
                break
        else:
            log.warning(
                "work_request_node: lumsum_type_name %r not found in LUMSUM_TYPE_ENUMS",
                ls_name,
            )

   
    d_name = data.get("discipline_name")
    if d_name: 
        for item in DISCIPLINE_ENUMS:
            if item["name"] == d_name:
                data["discipline_id"] = item["id"]
                log.info(
                    "work_request_node: discipline matched enum -> id=%s",
                    item["id"],
                )
                break
        else:
            log.warning(
                "work_request_node: discipline_name %r not found in DISCIPLINE_ENUMS",
                d_name,
            )

   


    # -------------------------
    #  Attach to state & return
    # -------------------------
    state["work_request_payload"] = data
    log.info(
        "work_request_node: work_request_payload attached to state with keys=%s",
        list(data.keys()),
    )
    log.error(f"STATE BEFORE RETURN: {state}")

    log.info("work_request_node: completed successfully, returning updated state")
    return state
