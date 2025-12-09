from typing import Literal


def classify_domain(query: str) -> Literal["general", "projects", "finance"]:
    q = query.lower()
    if any(w in q for w in ["project", "milestone", "portfolio", "rfi", "rfp"]):
      return "projects"
    if any(w in q for w in ["budget", "invoice", "cost", "po "]):
     return "finance"
    return "general"