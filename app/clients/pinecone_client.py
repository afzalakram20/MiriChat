from typing import List, Dict


class PineconeClientMock:
    def __init__(self, index_name: str):
     self.index_name = index_name


def similarity_search(self, vector, k=5, namespace="default") -> List[Dict]:
# Return mock documents with scores
    return [
    {"id": f"doc-{i}", "score": 0.9 - i*0.05, "text": f"Mock context {i} for {namespace}", "metadata": {"source": "mock"}}
    for i in range(k)
    ]