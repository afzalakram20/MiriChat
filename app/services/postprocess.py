from typing import Dict


def basic_redact(text: str) -> str:
    return text.replace("secret", "[redacted]")