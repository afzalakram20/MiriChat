from app.core.config import settings
import json
import re
from typing import Any, Dict, List
from fastapi import APIRouter, Query
from bs4 import BeautifulSoup
from pathlib import Path
from app.models.llm.factory import get_llm

router = APIRouter(prefix="/preprocess", tags=["Data Preprocessing"])

# ==========================
#   Utility Functionsa
# ==========================
RAW_DATA_PATH = Path("app/data/work-generation/raw-data.json")
RAG_OUTPUT_PATH = Path("app/data/project_rag_data.json")
FINE_TUNE_DATASET_PATH = Path("app/data/work-generation/stage1.json")
WORK_GNE_RAW_DATA_PATH = Path("app/data/work-generation/raw-data.json")


def clean_html(text: str) -> str:
    """Remove HTML tags and decode HTML entities safely."""
    if not text:
        return ""
    text = text.replace("&nbsp;", " ").replace("<br>", "\n").replace("<br/>", "\n")
    soup = BeautifulSoup(text, "html.parser")
    cleaned = soup.get_text(separator=" ", strip=True)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


async def generate_short_command(full_scope: str) -> str:
    """
    Use LLM to create a realistic short 'user_command'
    from a detailed project scope.
    Example:
      Input: "Specialist contractor to attend site and carry out degas of Greenford Chillers 1-6..."
      Output: "degas Greenford chillers"
    """
    llm = get_llm()
    prompt = f"""
You are a construction project assistant helping to create realistic short queries.
Given the following detailed project scope, generate a short natural command (3–12 words)
that a manager might type to describe this task informally.

Rules:
- Avoid punctuation and titles.
- Use simple lowercase wording.
- Keep it clear and human-like.

Full scope:
\"\"\"{full_scope}\"\"\"

Short user command:
"""
    try:
        short_text = await llm.complete(prompt)
        short_text = clean_html(short_text)
        short_text = re.sub(r"[^A-Za-z0-9\s\-&]", "", short_text).strip()
        if len(short_text.split()) > 15:
            short_text = " ".join(short_text.split()[:12])
        return short_text
    except Exception as e:
        print(f"⚠️ Command generation failed: {e}")
        return full_scope[:50]


async def preprocess_project(project: dict, generate_short: bool = True) -> list:
    """
    Prepare a project into one or two fine-tuning records:
      - Full 'scope_of_works' as user_command
      - Short LLM-generated command (if generate_short=True)
    Returns a list of JSONL records.
    """
    scope_clean = clean_html(project.get("scope_of_works", ""))
    problem_clean = clean_html(project.get("problem_statement", ""))
    justifications_clean = clean_html(project.get("justifications", ""))
    effect_clean = clean_html(project.get("effect_of_non_approval", ""))

    checklist_items = project.get("project_checklists", [])
    if isinstance(checklist_items, list) and checklist_items:
        checklist_summary = [
            {"label": item.get("label"), "value": item.get("value")}
            for item in checklist_items
            if item and isinstance(item, dict)
        ]
        # output["checklist_summary"] = checklist_summary

    output = {
        "reasoning": f" ",
        "scope_of_works": scope_clean,
        "problem_statement": problem_clean,
        "justifications": justifications_clean,
        "effect_of_non_approval": effect_clean,
        "discipline_name": project.get("discipline_name"),
        "request_type_name": project.get("request_type_name"),
        "lumsum_type_name": project.get("lumsum_type_name"),
        "contract_name": project.get("contract_name"),
        "quotation_type_name": project.get("quotation_type_name"),
        "managing_office_name": project.get("managing_office_name"),
        "project_title": project.get("project_title"),
        "cbre_interal_work_order": project.get("cbre_interal_work_order"),
        "checklist_summary": checklist_summary,
    }

    # 🧱 Create both records
    records = []

    records.append(output)

    # 1️⃣ Full scope version
    # records.append(
    #     {
    #         "messages": [
    #             {
    #                 "role": "system",
    #                 "content": "You are an AI assistant trained for multi task enterprise workflows. Your current task is: Work Request Generation. You must return a structured JSON with fields such as scope_of_works, problem_statement, justifications,lumsum_type_name, disciplien_name   etc.",
    #             },
    #             {
    #                 "role": "user",
    #                 "content": f" [TASK: Work Request Generation]\n\n{scope_clean}",
    #             },
    #             {
    #                 "role": "assistant",
    #                 "content": json.dumps(output, ensure_ascii=False),
    #             },
    #         ]
    #     }
    # )

    # 2️⃣ Short synthetic version
    # if generate_short and scope_clean:
    #     short_cmd = await generate_short_command(scope_clean)
    #     records.append(
    #         {
    #             "messages": [
    #                 {
    #                     "role": "system",
    #                     "content": "You are an AI assistant trained for multi task enterprise workflows. Your current task is: Work Request Generation. You must return a structured JSON with fields such as scope_of_works, problem_statement, justifications,lumsum_type_name, disciplien_name   etc.",
    #                 },
    #                 {
    #                     "role": "user",
    #                     "content": f" [TASK: Work Request Generation]\n\n{short_cmd}",
    #                 },
    #                 {
    #                     "role": "assistant",
    #                     "content": json.dumps(output, ensure_ascii=False),
    #                 },
    #             ]
    #         }
    #     )

    return records


@router.get("/generate-work-requst-stage1")
async def generate_refined_jsonl(
    include_short: bool = Query(
        default=True,
        description="Include both full and short commands for each project",
    )
):
    """
    Reads data from 'projects_query_results.json',
    cleans fields, generates both full + short user commands (if enabled),
    and saves to 'refined_projects_data.jsonl' for fine-tuning.
    """
    input_path = WORK_GNE_RAW_DATA_PATH
    if not input_path.exists():
        return {"error": f"Input file not found: {input_path}"}

    raw = input_path.read_text(encoding="utf-8")
    try:
        data = json.loads(raw)

    except json.JSONDecodeError as e:
        return {
            "error": "File is not valid JSON.",
            "details": f"{e.msg} at line {e.lineno} col {e.colno}",
        }

    projects = data
    if isinstance(data, dict) and "projects_json" in data:
        inner = data["projects_json"]
        print(len(inner))
        if isinstance(inner, str):
            try:
                projects = json.loads(inner)  # parse the inner JSON string
                print(f"iioo=== {len(projects)}")
            except json.JSONDecodeError as e:
                return {
                    "error": "`projects_json` contains invalid JSON.",
                    "details": f"{e.msg} at line {e.lineno} col {e.colno}",
                    "snippet": inner[:200],
                }
        else:
            projects = inner  # assume already a list/dict

    # projects =projects[:100]
    if not isinstance(projects, list):
        return {
            "error": "Invalid JSON format. Expected a list of project objects.",
            "got_type": type(projects).__name__,
        }

    refined_records = []
    print(len(projects))
    for project in projects:
        try:
            new_records = await preprocess_project(
                project, generate_short=include_short
            )
            refined_records.extend(new_records)
        except Exception as e:
            print(f"⚠️ Error processing project ID {project.get('id')}: {e}")

    # Write JSONL
    FINE_TUNE_DATASET_PATH.parent.mkdir(parents=True, exist_ok=True)

    # with open(FINE_TUNE_DATASET_PATH, "w", encoding="utf-8") as out:
    #     for record in refined_records:
    #         out.write(json.dumps(record, ensure_ascii=False) + "\n")

    # for orignal JSON
    # Write standard JSON array instead of JSONL
    with open(FINE_TUNE_DATASET_PATH, "w", encoding="utf-8") as out:
        json.dump(refined_records, out, ensure_ascii=False, indent=2)

    return {
        "message": "✅ Fine-tune dataset generated successfully.",
        "include_short_versions": include_short,
        "input_file": str(input_path),
        "output_file": str(FINE_TUNE_DATASET_PATH),
        "total_records": len(refined_records),
        "unique_projects": len(projects),
    }


####################################################################################################
########################  RAG WORKING STARTED HERE    ##############################################
####################################################################################################


import os
import json
from typing import List, Dict, Any

from bs4 import BeautifulSoup
from pinecone import Pinecone, ServerlessSpec


# === Config ===
# DATA_DIR = Path("app/data/projects")
RAW_DATA_PATH = Path("app/data/projects_query_results.json")
RAG_OUTPUT_PATH = Path("app/data/project_rag_data.json")

# HuggingFace embedding model
EMBED_MODEL_NAME = "sentence-transformers/all-mpnet-base-v2"

# Pinecone index setup
PINECONE_API_KEY = (
    "pcsk_7UpRMd_UehAZXxXFDW6EPVsiZGtVmDkwcLo3ZPJ4XKTHkFxYVT6VjY4Dr64GQQAL66zB8R"
)
PINECONE_INDEX_NAME = "horizon-work-order-scopes"
PINECONE_ENV = os.getenv("PINECONE_ENV", "us-east-1")

# === Initialize Pinecone ===
pc = Pinecone(api_key=PINECONE_API_KEY)
if PINECONE_INDEX_NAME not in [i["name"] for i in pc.list_indexes().get("indexes", [])]:
    pc.create_index(
        name=PINECONE_INDEX_NAME,
        dimension=768,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region=PINECONE_ENV),
    )
index = pc.Index(PINECONE_INDEX_NAME)


@router.get("/rag-generate-data")
def prepare_and_upload():
    """Pipeline entrypoint."""
    if not RAW_DATA_PATH.exists():
        raise FileNotFoundError(f"{RAW_DATA_PATH} not found")

    with open(RAW_DATA_PATH, "r", encoding="utf-8") as f:
        outer = json.load(f)
    print(f"project list outer=={outer}")
    projects_list = json.loads(
        outer["projects_json"]
    )  # <- inner parse (string -> list[dict])
    print(f"project list=={projects_list}")
    refined = process_projects_for_rag(projects_list)

    with open(RAG_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(refined, f, ensure_ascii=False, indent=2)
    create_project_embeddings(refined)
    print(f"📁 Saved processed RAG data to {RAG_OUTPUT_PATH}")


# === Initialize Embedding Model ===
embedder = SentenceTransformer(settings.HG_EMBEDDING_MODEL)


# === Utilities ===
def clean_html(text: str) -> str:
    """Remove HTML tags and excessive whitespace."""
    if not text:
        return ""
    return " ".join(BeautifulSoup(text, "lxml").text.split())


def build_project_context(project: Dict[str, Any]) -> str:
    """Combine major descriptive fields into one text block."""
    sections = {
        "Problem Statement": clean_html(project.get("problem_statement", "")),
        "Scope of Works": clean_html(project.get("scope_of_works", "")),
        "Justifications": clean_html(project.get("justifications", "")),
        "Effect of Non-Approval": clean_html(project.get("effect_of_non_approval", "")),
    }
    context = "\n\n".join([f"{k}: {v}" for k, v in sections.items() if v])
    return context.strip()


# === Process and Embed ===
def process_projects_for_rag(raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    refined = []
    for proj in raw_data:
        try:
            context_text = build_project_context(proj)
            if not context_text:
                continue  # skip empty
            metadata = {
                "project_id": proj.get("id"),
                "project_title": proj.get("project_title"),
                "discipline": proj.get("discipline_name") or "",
                "request_type": proj.get("request_type_name") or "",
                "contract_name": proj.get("contract_name") or "",
                "quotation_type": proj.get("quotation_type_name") or "",
                "lumsum_type": proj.get("lumsum_type_name") or "",
                "is_cbre_funded": proj.get("is_cbre_funded") or "",
                "appro_number": proj.get("appro_number") or "",
            }
            refined.append(
                {
                    "id": str(proj.get("id")),
                    "context": context_text,
                    "metadata": metadata,
                }
            )
        except Exception as e:
            print(f"⚠️ Error processing project {proj.get('id')}: {e}")
    return refined


def create_project_embeddings(projects: List[Dict[str, Any]]):
    """Embed and push project-level data to Pinecone."""
    for proj in projects:
        vector = embedder.encode(proj["context"], show_progress_bar=False).tolist()
        index.upsert(
            vectors=[
                {
                    "id": str(proj["id"]),
                    "values": vector,
                    "metadata": proj["metadata"],
                }
            ]
        )
    print(
        f"✅ {len(projects)} project embeddings uploaded to Pinecone index '{PINECONE_INDEX_NAME}'."
    )
