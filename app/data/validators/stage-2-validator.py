import json
import re
import logging
import sys
from typing import List, Tuple, Dict, Any

REQUIRED_OUTPUT_FIELDS = [
    "reasoning",
    "overview",
    "project_scope",
    "status_history",
    "project_financials",
    "epic_form",
    "pors",
    "close_out",
    "blockers",
    "next_steps"
]

logger = logging.getLogger("dataset_validator")


def setup_logger(log_file: str = "validation.log"):
    """Configure logger to write both to file and console."""
    logger.setLevel(logging.DEBUG)

    # Clear any existing handlers (important if re-running in same process)
    logger.handlers.clear()

    # File handler (detailed log)
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.DEBUG)

    # Console handler (optional, more concise)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)


def load_jsonl(path: str) -> List[Tuple[int, Dict[str, Any]]]:
    lines = []
    with open(path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                lines.append((line_no, obj))
            except json.JSONDecodeError as e:
                logger.error(f"Line {line_no}: Invalid JSONL → {e}")
    return lines


def validate_messages(msgs, line_no: int) -> bool:
    if not isinstance(msgs, list):
        logger.error(f"Line {line_no}: 'messages' must be a list.")
        return False

    roles = [m.get("role") for m in msgs]
    if roles != ["system", "user", "assistant"]:
        logger.error(
            f"Line {line_no}: messages must contain roles in order: "
            f"system → user → assistant. Got: {roles}"
        )
        return False

    for idx, m in enumerate(msgs):
        if "content" not in m:
            logger.error(f"Line {line_no}: Message {idx} missing 'content'.")
            return False

        if not isinstance(m["content"], str):
            logger.error(
                f"Line {line_no}: Message {idx} content must be string, "
                f"got {type(m['content'])}."
            )
            return False

    return True


def detect_double_escaped_json(text: str) -> bool:
    # Detect patterns like  "{\"project\":\"abc\"}"
    return bool(re.search(r'\\"', text))


def extract_json_from_text(text: str):
    """
    Extract the first JSON object from text (between first '{' and last '}').
    Returns dict or None.
    """
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        substring = text[start:end]
        return json.loads(substring)
    except Exception:
        return None


def validate_assistant_output(output_json: Dict[str, Any], line_no: int) -> bool:
    # Ensure all required fields exist
    ok = True
    for field in REQUIRED_OUTPUT_FIELDS:
        if field not in output_json:
            logger.error(
                f"Line {line_no}: Missing field in assistant output → '{field}'"
            )
            ok = False

    # Type checks
    if "blockers" in output_json and not isinstance(output_json["blockers"], list):
        logger.error(f"Line {line_no}: 'blockers' must be a list.")
        ok = False

    if "next_steps" in output_json and not isinstance(output_json["next_steps"], list):
        logger.error(f"Line {line_no}: 'next_steps' must be a list.")
        ok = False

    return ok


def validate_missing_fields_with_na(
    input_json: Dict[str, Any],
    output_json: Dict[str, Any],
    line_no: int
):
    """
    If input says things like:
        "No EPIC form data"
    Then assistant must output:
        "epic_form": "N/A"
    Similar rules for PORs and closeout info.
    """
    checks = [
        ("epic_form", ["No EPIC form data", "No EPIC", "No EPIC form", "No data"]),
        ("pors", ["No Purchase Order Requests", "No POR", "No purchase order", "No data"]),
        ("close_out", ["No project closeout", "No project close-out",
                       "No closeout", "No close-out", "No closeout and billing", "No data"])
    ]

    # Flatten input values (including nested keys if needed)
    # For now, just top-level, which matches your current structure.
    input_strings = []
    for key, val in input_json.items():
        if isinstance(val, str):
            input_strings.append(val)
        elif isinstance(val, dict):
            # check nested dict values too (e.g., "closeout_billing")
            for sub_key, sub_val in val.items():
                if isinstance(sub_val, str):
                    input_strings.append(sub_val)

    for out_field, keywords in checks:
        # Did input imply "no data" for this field?
        triggered = False
        for text in input_strings:
            lower_val = text.lower()
            for k in keywords:
                if k.lower() in lower_val:
                    triggered = True
                    break
            if triggered:
                break

        if triggered:
            out_val = output_json.get(out_field)
            if out_val not in ["N/A", "n/a", "NA", "Na", "NaN"]:
                logger.warning(
                    f"Line {line_no}: Output field '{out_field}' should likely be 'N/A' "
                    f"because input text implies missing data."
                )


def validate_jsonl(path: str):
    lines = load_jsonl(path)
    logger.info(f"Loaded {len(lines)} records from: {path}")

    valid = True

    for line_no, obj in lines:
        if "messages" not in obj:
            logger.error(f"Line {line_no}: Missing top-level 'messages'.")
            valid = False
            continue

        msgs = obj["messages"]

        if not validate_messages(msgs, line_no):
            valid = False
            continue

        system_msg, user_msg, assistant_msg = msgs

        # Detect double-escaped JSON in user content
        if detect_double_escaped_json(user_msg["content"]):
            logger.error(
                f"Line {line_no}: User content appears to contain double-escaped JSON (\\\")."
            )
            valid = False

        # Extract input JSON from user message
        input_json = extract_json_from_text(user_msg["content"])
        if not input_json:
            logger.error(
                f"Line {line_no}: Could not extract valid JSON from user message content."
            )
            valid = False
            continue

        # Validate assistant output JSON
        try:
            output_json = json.loads(assistant_msg["content"])
        except json.JSONDecodeError as e:
            logger.error(f"Line {line_no}: Assistant output invalid JSON → {e}")
            valid = False
            continue

        if not validate_assistant_output(output_json, line_no):
            valid = False

        # Check N/A consistency rules
        validate_missing_fields_with_na(input_json, output_json, line_no)

    if valid:
        logger.info("🎉 All records are valid! Dataset is ready for finetuning.")
    else:
        logger.info("⚠ Dataset has errors. Check logs above and fix before training.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python validate_dataset.py <dataset.jsonl> [log_file]")
        sys.exit(1)

    dataset_path = sys.argv[1]
    log_file = sys.argv[2] if len(sys.argv) >= 3 else "validation.log"

    setup_logger(log_file)
    logger.info(f"Starting validation for dataset: {dataset_path}")
    logger.info(f"Logging to: {log_file}")
    validate_jsonl(dataset_path)
    
    
    
    
    
# # Custom log file name
# python validate_dataset.py train.jsonl project_validation.log
# python app/data/validators/stage-2-validator.py app/data/summarization/stage-2/project-summarization-cananda.jsonl  logs/app.log