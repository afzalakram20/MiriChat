from typing import List, Dict
from app.models.embeddings import MockEmbedder
from app.clients.pinecone_client import PineconeClientMock


_embedder = MockEmbedder()
_pc = PineconeClientMock(index_name="projects-rag")


def retrieve_contexts(query: str, namespace: str, k: int = 5) -> List[Dict]:
    vec = _embedder.embed_query(query)
    return _pc.similarity_search(vec, k=k, namespace=namespace)