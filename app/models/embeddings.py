from typing import List


class MockEmbedder:
    def embed_query(self, text: str) -> List[float]:
    # Deterministic toy embedding for mocks
     return [float((sum(map(ord, text)) % 97) / 97.0)] * 8   