from app.llms.runnable.llm_provider import get_chain_llm
from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser
from langchain_core.documents import Document
from app.core.config import settings
from langchain_pinecone import PineconeVectorStore
from app.models.parsers.work_request_models import (
    WorkRequestModel,
    LUMSUM_TYPE_ENUMS,
    DISCIPLINE_ENUMS,
    PROJECT_TYPE_ENUMS,
    PROJECT_CHECKLIST_ENUMS,
    QUOTATION_TYPE_ENUMS,
)
from app.graphs.nodes.prompts.work_request_prompt import SYSTEM_MESSAGE
from langchain_community.embeddings import HuggingFaceEmbeddings
import json
import re
import logging

log = logging.getLogger("work_request_node")


async def work_request_node(state: Dict[str, Any]) -> Dict[str, Any]:
    pinecone_index_name = "horizon-work-order-scopes"

    log.info("******* Entered work_request_node ********")
    log.info(f"work_request_node: incoming state keys -> {list(state.keys())}")

    user_query = state.get("user_input")

    embeddings = HuggingFaceEmbeddings(model_name=settings.HG_EMBEDDING_MODEL)
    vectorstore = PineconeVectorStore(
        index_name=pinecone_index_name,
        embedding=embeddings,
        text_key="project_title",
        pinecone_api_key=settings.PINECONE_API_KEY,
    )

    log.info("work_request_node: converting vectorstore to retriever (k=5)")
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
    llm = get_chain_llm()

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
            f"{k}: {v}" for k, v in d.metadata.items() if v is not None and v != ""
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
        "\n\n---\n\n".join(context_chunks)
        if context_chunks
        else "No similar projects found."
    )
    log.info(
        "work_request_node: final retrieved_context length -> %s",
        len(retrieved_context),
    )

    # -------------------------
    #  Prepare enums as prompt text
    # -------------------------
    log.info(
        "work_request_node: building project_type_table_str from PROJECT_TYPE_ENUMS"
    )
    project_type_table_str = "\n".join(
        f"- ID {item['id']}: {item['name']}" for item in PROJECT_TYPE_ENUMS
    )

    log.info("work_request_node: building discipline_table_str from DISCIPLINE_ENUMS")
    discipline_table_str = "\n".join(
        f"- ID {item['id']}: {item['name']}" for item in DISCIPLINE_ENUMS
    )

    log.info("work_request_node: building lumsum_table_str from LUMSUM_TYPE_ENUMS")
    lumsum_table_str = "\n".join(
        f"- ID {item['id']}: {item['name']}" for item in LUMSUM_TYPE_ENUMS
    )

    log.info("work_request_node: building quotation_type_table_str from QUOTATION_TYPE_ENUMS")
    quotation_type_table_str = "\n".join(
        f"- ID {item['id']}: {item['name']}" for item in QUOTATION_TYPE_ENUMS
    )

    log.info("work_request_node: building project_checklist_table_str from PROJECT_CHECKLIST_ENUMS")
    project_checklist_table_str = "\n".join(
        f"- ID {item['id']}: {item['name']}" for item in PROJECT_CHECKLIST_ENUMS
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
            MessagesPlaceholder("chat_history"),
            (
                "human",
                (
                    "User description of the required work request:\n"
                    "{user_query}\n\n"
                    "Retrieved similar projects (scopes + metadata):\n"
                    "{retrieved_context}\n\n"
                    "Follow these format instructions exactly (do NOT repeat them):\n"
                    "<FORMAT_START>\n"
                    "{format_instructions}\n"
                    "<FORMAT_END>\n\n"
                    "Your reply MUST be only a single minified JSON object. "
                    "Do NOT include code fences or any schema keys such as $defs, properties, required, type, additionalProperties."
                ),
            ),
        ]
    )

    # -------------------------
    #   Build chain (Runnable)
    # -------------------------
    log.info("work_request_node: building LCEL chain with prompt -> llm -> parser")

    chain = prompt | llm | parser

    chain_input = {
        "user_query": user_query,
        "retrieved_context": retrieved_context,
        "project_type_table": project_type_table_str,
        "discipline_table": discipline_table_str,
        "lumsum_table": lumsum_table_str,
        "quotation_type_table": quotation_type_table_str,
        "project_checklist_table": project_checklist_table_str,
        "format_instructions": format_instructions,
        "chat_history": state.get("chat_history") or [],
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

    # -------------------------
    #  Quotation type mapping based on user intent (GO/General Offer)
    # -------------------------
    def _user_requested_general_offer(text: str) -> bool:
        if not text:
            return False
        # Match explicit "general offer" (any case)
        if re.search(r"\bgeneral[\s\-]*offer(s)?\b", text, flags=re.IGNORECASE):
            return True
        # Match uppercase token "GO" (avoid lowercase 'go' verbs)
        if re.search(r"(?<![A-Za-z])GO(?![A-Za-z])", text):
            return True
        return False

    try:
        if _user_requested_general_offer(user_query or ""):
            data["quotation_type_id"] = 5  # General Offer
        else:
            # Ensure default is valid (1 = Kyndrl Offer)
            if not isinstance(data.get("quotation_type_id"), int):
                data["quotation_type_id"] = 1
            elif data["quotation_type_id"] not in {1, 5}:
                data["quotation_type_id"] = 1
    except Exception:
        # Fallback: keep schema default if anything odd happens
        data.setdefault("quotation_type_id", 1)

    # -------------------------
    #  Extract site name using LLM if missing (structured, rules-driven)
    # -------------------------
    if not data.get("site_name"):
        site_system_prompt_text = (
            "Your job is to extract structured information from user input.\n\n"
            "Rules for identifying the site_name:\n"
            "- A real site name is usually a proper noun (Example: 'Witting Group', 'ABC Tower').\n"
            "- Do NOT consider generic words like: 'site mentioned', 'the site', 'specific site', "
            "'any site', or anything that is not a proper noun.\n"
            "- If the user mentions a real site name, extract it.\n"
            "- If no real site name is provided, return null.\n\n"
            "Return ONLY minified JSON without code fences or extra text, exactly one of:\n"
            "{\"site_name\": \"NAME\"}\n"
            "{\"site_name\": null}"
        )
        site_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", site_system_prompt_text),
                ("human", "User input:\n{user_query}"),
            ]
        )
        llm_site = get_chain_llm()
        site_chain = site_prompt | llm_site | StrOutputParser()
        extracted_site_name: str = ""
        try:
            site_raw = (site_chain.invoke({"user_query": user_query or ""}) or "").strip()
            if site_raw.startswith("```"):
                site_raw = re.sub(r"^```(?:json)?\s*", "", site_raw, flags=re.IGNORECASE)
                site_raw = re.sub(r"\s*```$", "", site_raw)
            obj = json.loads(site_raw)
            val = obj.get("site_name")
            if isinstance(val, str) and val.strip():
                extracted_site_name = val.strip()
        except Exception:
            pass
        if extracted_site_name:
            data["site_name"] = extracted_site_name
            log.info("work_request_node: LLM-extracted site_name=%r", extracted_site_name)

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
