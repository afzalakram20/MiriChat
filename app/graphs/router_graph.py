from typing import Dict, Any
from app.services.classify import classify_domain
from app.services.rag import retrieve_contexts
from app.services.mcp_client import mcp_list_top_projects


class RouterGraph:
    def __init__(self, request_id: str, tenant: str):
        self.request_id = request_id
        self.tenant = tenant


def run(self, query: str) -> Dict[str, Any]:
# 1) classify
    domain = classify_domain(query)


# 2) decide tools
    tools = {}
    if domain == "projects" and "top" in query.lower() and "project" in query.lower():
     tools["projects"] = mcp_list_top_projects(tenant=self.tenant, limit=10)


# 3) RAG (optional)
    namespace = f"{self.tenant}:{domain}"
    contexts = retrieve_contexts(query, namespace=namespace, k=3)


    # 4) Compose prompt (simple)
    prompt = f"You are a helpful {domain} assistant. Question: {query}\nUse contexts: {contexts}"
    return {"domain": domain, "prompt": prompt, "contexts": contexts, "tools": tools}