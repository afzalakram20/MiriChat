import os
import json
from fastapi import APIRouter, HTTPException
from pathlib import Path
import logging

log = logging.getLogger("app.controllers.summary")

router = APIRouter(prefix="/preprocess1", tags=["Data Preprocessingone"])


@router.post("/summarization-jsonl-generation")
async def generate_jsonl_from_projects(
    input_dir: str = "app/data/summarization/stage-1/uk",
    output_file: str = "app/data/summarization/stage-2/project-summarization-uk.jsonl",
):
    """
    Reads multiple JSON files from a directory.
    Each file contains a list of project dicts with 'input' and 'output'.
    Converts them to JSONL for fine-tuning with a task label [TASK: Project Summarization].
    """
    log.info("Starting summarization-jsonl-generation")
    input_path = Path(input_dir)
    output_path = Path(output_file)

    if not input_path.exists():
        raise HTTPException(
            status_code=404, detail=f"Input directory not found: {input_dir}"
        )

    records = []
    files_processed = 0
    total_projects_raw = 0
    total_projects_used = 0

    # Iterate through all .json files in directory
    for file_path in input_path.glob("*.json"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, list):
                raise ValueError(
                    f"File {file_path} must contain a list of project objects."
                )

            files_processed += 1
            file_raw_count = len(data)
            file_used_count = 0
            total_projects_raw += file_raw_count

            log.info(f"{file_path.name} -> raw projects: {file_raw_count}")

            # 🔑 One record per project
            for project in data:
                input_text = project.get("input")
                output_text = project.get("output")

                # Skip incomplete entries (optional)
                if input_text is None or output_text is None:
                    continue

                file_used_count += 1
                total_projects_used += 1
                log.warning(f"the type of Input is ---> {type(input_text) }")
                log.warning(f"the main Input is ---> { input_text }")
                if isinstance(input_text, dict):
                    print("input_text is a Python dict")
                elif isinstance(input_text, str):
                    print("input_text is a string (already JSON text)")
                else:
                    print("input_text is something else:", type(input_text))
                # If input/output are JSON objects, dump them to strings
                # (Fine-tuning API expects message.content to be a string)
             

                record = {
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                """ You are an expert project summarization model used in the Horizon Extra Works tool
                                Your task is: Project Summarization
                                You strictly follow these rules:
                                1. Rewrite scope fields (notes, problem, scope, justification, non-approval-effect) into short summarized and clean human language.
                                2. When you got no data for output field then simply mention N/A
                                3. Never copy text word-for-word unless required (e.g., financial values).
                                4. Summaries must be factual, fluent, and business-professional.
                                5. Follow the exact output structure:
                                    - reasoning
                                    - overview
                                    - project_scope
                                    - status_history
                                    - project_financials
                                    - epic_form
                                    - pors
                                    - close_out
                                    - blockers[]
                                    - next_steps[]
                                6. The “reasoning” field must explain HOW you transformed the input into structured summaries so smaller models can learn the summarization policy.
                                7. Blockers are the missing things in project completion and next steps are their implementation steps
                                """
                            ),
                        },
                        {
                            "role": "user",
                            "content": "[Task:Project Summarization] Summarize the following project data into the required structured format:\n\n"
                            + json.dumps(input_text, ensure_ascii=False, indent=2),
                        },
                        {
                            "role": "assistant",
                            "content": json.dumps(
                                output_text, ensure_ascii=False, indent=2
                            ),
                        },
                    ]
                }
                log.info(f"message retrieved {record}")
                records.append(record)

        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error processing {file_path}: {str(e)}"
            )

    # Ensure output directory exists
    os.makedirs(output_path.parent, exist_ok=True)

    # Write as JSONL
    with open(output_path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False))
            f.write("\n")

    return {
        "status": "success",
        "files_processed": files_processed,
        "raw_projects": total_projects_raw,
        "records_generated": len(records),
        "projects_used_after_filter": total_projects_used,
        "output_file": str(output_path.resolve()),
    }
