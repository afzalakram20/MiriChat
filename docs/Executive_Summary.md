## Executive Summary

This document provides a high-level, system-specific overview of the technologies, architectural patterns, and core innovations in the AI-driven project assistant used across Horizon Extra Works (Ew AI Agent). The platform unifies Natural Language Processing (NLP), multi‑provider LLMs, LangGraph‑based orchestration, Retrieval‑Augmented Generation (RAG), and deterministic validators to convert unstructured requests into actionable outputs: optimized SQL, structured work requests, project summaries, and contextual help.

By combining automation, analytics, and natural language interfaces, the system reduces manual effort, accelerates decision-making, and improves operational visibility across projects, approvals, costs, and resource planning. The design is modular, scalable, and production‑ready for large enterprise environments.


## Key Capabilities

- Intent understanding and routing (work request, SQL analytics, project summary, app help).
- SQL generation and execution over enterprise schemas with safety and formatting guarantees.
- Structured Work Request generation with strict Pydantic schema validation and enum enforcement.
- RAG‑powered app help using Pinecone vector search with HuggingFace embeddings.
- Capital planning workflows: materials extraction, price summarization, and best‑price selection.
- Conversation memory with Redis/Mongo and first‑class chat history injection in prompts.
- Multi‑LLM provider abstraction (OpenAI / Bedrock) with consistent LCEL/Chain patterns.


## Architecture Overview

- Orchestration: LangGraph state machine (`app/graphs/horizon_brain_graph.py`) routes by intent and composes task nodes.
- Nodes (selected):
  - `intent_node`: Classifies primary workflow using a strict JSON parser and uses chat history to resolve follow‑ups.
  - `sqlgen_node` → `sqlexec_node`: Two‑step Text‑to‑SQL (module selection → SQL generation), optional execution via Laravel API.
  - `work_request_node`: RAG context + PydanticOutputParser for `WorkRequestModel` with full enum/size validation.
  - `project_summary_node`: Extracts target (ref_id/title), calls service APIs, summarizes into a structured JSON.
  - `app_info_node`: RAG over app knowledge base (Pinecone) for how‑to and process guidance.
- Prompts: Parameterized with ChatPromptTemplate and MessagesPlaceholder for chat history; system prompts include concrete guardrails and formatting rules.


## Orchestration & Flow Control

- Graph entrypoint receives `user_input`, `chat_id`, and preformatted `chat_history` (LangChain messages).
- `intent_node` sets `state.intent` then the graph dispatches to the appropriate main task node.
- After a task completes, results are attached to `state` (e.g., `work_request_payload`, `rows_data`, `project_summary_data`, or `response`).
- Service layer (`HorizonService`) persists user/assistant turns and payloads to memory.


## Language Model Layer

- Provider abstraction in `app/llms/runnable/llm_provider.py` returns a chain‑ready LLM regardless of backing vendor (OpenAI/Bedrock).
- All LLM interactions use LCEL (Runnable) style: `prompt | llm | parser` for deterministic parsing where applicable.
- System prompts explicitly forbid schema echo, enforce JSON‑only output, and guide follow‑up handling using conversation history.


## Data & RAG

- Vector store: Pinecone (HuggingFace embeddings) provides semantic retrieval for app help and work request context.
- RAG chains pass retrieved documents into prompts; answers are restricted to provided context for factuality.


## Structured Outputs & Validation

- `WorkRequestModel` (Pydantic) strictly enforces:
  - Exact checklist coverage and id/label match from `PROJECT_CHECKLIST_ENUMS`.
  - Valid enum IDs/names for types and disciplines.
  - Optional `site_name` normalization (rejects generic placeholders).
  - Aliases/validation_alias for tolerant casing (e.g., “Scope Of Works”).
- LangChain `PydanticOutputParser` ensures the LLM returns valid, minified JSON conforming to the model.


## Memory & Chat History

- MemoryManager orchestrates Redis (fast cache) and Mongo (source of truth) persistence.
- `load_context_messages(chat_id)` returns LangChain `HumanMessage`/`AIMessage` for first‑class history in prompts.
- History is injected with `MessagesPlaceholder("chat_history")` in nodes (intent, sql gen, project summary, work request, app info) to support follow‑ups like “add filter” or “change step 2” without re‑specifying the entire context.


## SQL Generation & Execution Pipeline

- Step 1 (modules): `FIRST_SYSTEM_PROMPT` returns JSON `{"modules": [...]}` determining required schema modules.
- Step 2 (SQL): `SECOND_SYSTEM_PROMPT` generates JSON `{"sql": "<SELECT ...>"}` with strict safety rules:
  - Read‑only SELECT; no DDL/DML.
  - No `SELECT *`; use explicit columns.
  - Join and display rules (e.g., always include human‑readable status where available).
  - History‑aware follow‑ups (“same query, add filter/sort/include field”).
- Execution: `sqlexec_node` can call Laravel’s `execute-sql` endpoint; responses normalized into `rows_data` with error resilience.


## Work Request Generation

- Context: Retrieves similar scopes via Pinecone; prompts include enums tables for types, disciplines, quotation and checklist.
- Output: Strict JSON parsed into `WorkRequestModel`; enums auto‑corrected; `site_name` extracted or inferred when provided.
- Quote type: Heuristics map “GO/General Offer” in user input to `quotation_type_id=5`; else default `1`.


## Capital Planning & Cost Estimation

- Materials extraction: LCEL prompt produces `MaterialExtractionResult` with purchasable items only.
- Price summarization: Aggregates Tavily search results into normalized pricing structures.
- Best selection: LLM selects the most reliable price per category (history‑aware and JSON‑only).


## Integrations

- Laravel API: Schema tool, SQL execution, and project data endpoints with `X-API-KEY` support.
- Pinecone Vector Store (RAG) and Tavily Search for pricing sources.


## Safety, Reliability, and Observability

- Strict JSON schemas and parsing prevent prompt injection and schema echo.
- Defensive validation in models (ids/labels, alias normalization) and nodes (error handling, fallbacks).
- Logging across services and nodes; memory auditing via Mongo payloads.


## Performance & Scalability

- Stateless nodes with externalized memory and vector store.
+- Provider‑agnostic LLM layer enables right‑sizing models per task (cost/latency vs accuracy).


## Roadmap (Illustrative)

- Fine‑grained role‑based safety policies on top of Text‑to‑SQL.
- Automatic query caching and results memoization.
- Prompt/chain telemetry dashboards for drift detection and continuous improvement.


## Outcome

The Ew AI Agent operationalizes a robust, history‑aware assistant that turns natural language into precise, validated outputs for analytics, project documentation, and operational workflows. With modular graphs, strict validators, and RAG‑augmented reasoning, it delivers a tangible reduction in manual effort, faster decision cycles, and higher confidence in results across enterprise project operations.


