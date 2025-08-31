from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

QDRANT_URL = "http://localhost:6333"
COLLECTION = 'dairy_exports'
EMBED_MODEL = "BAAI/bge-small-en-v1.5"

@dataclass
class Hit:
    score: float
    payload: Dict[str, Any]

class Retriever:
    def __init__(self, collection: str = COLLECTION, model_name: str = EMBED_MODEL, url: str = QDRANT_URL):
        self.collection = collection
        self.client = QdrantClient(url=url)
        self.model = SentenceTransformer(model_name)

    def search(self, query: str, top_k: int = 5, filters: Optional[Dict[str, Any]] = None) -> List[Hit]:
        qvec = self.model.encode(query).tolist()
        qfilter = None
        if filters:
            must = []
            for k, v in filters.items():
                must.append(FieldCondition(key=k, match=MatchValue(value=v)))
            qfilter = Filter(must=must)

        hits = self.client.search(
            collection_name=self.collection,
            query_vector=qvec,
            limit=top_k,
            query_filter=qfilter
        )
        return [Hit(score=h.score, payload=h.payload) for h in hits]