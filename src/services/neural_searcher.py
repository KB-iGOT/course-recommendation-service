import os
import time
from typing import List
import openai
from qdrant_client import QdrantClient
from qdrant_client.http.models.models import Filter, FieldCondition, MatchText, MatchValue
from src.core.config import QDRANT_URL

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_EMBEDDING_MODEL = os.environ.get("OPENAI_EMBEDDING_MODEL")

# OpenAI Embedding
embedding_model = OPENAI_EMBEDDING_MODEL
openai_client = openai.Client(api_key=OPENAI_API_KEY)

class NeuralSearcher:

    def __init__(self, collection_name: str | None = None):
        self.collection_name = collection_name
        self.qdrant_client = QdrantClient(QDRANT_URL)
        # self.qdrant_client.set_model(EMBEDDINGS_MODEL)

    def search(self, collection_name: str, text: str | None = None, filter_: any = None, limit = 5) -> List[dict]:
        print("collection_name :", collection_name)
        start_time = time.time()
        hits = self.qdrant_client.query_points(
            collection_name=collection_name,
            query= openai_client.embeddings.create(
                input=text,
                model=embedding_model,
            ).data[0].embedding if text else text,
            query_filter=filter_ if filter_ else None,
            limit=limit,
        ).points
        results = []
        # print(hits)
        for hit in hits:
            # print(hit.payload['metadata'], "score:", hit.score)
            results.append({"score": hit.score, "metadata": hit.payload["metadata"]})
        print(f"Search took {time.time() - start_time} seconds")
        return results
    
    
if __name__ == "__main__":
    neural_searcher = NeuralSearcher()
    results = neural_searcher.search(filter_= Filter(
                must=[
                    FieldCondition(
                        key="metadata.department",
                        match=MatchText(text="Ministry of power"),
                    ),
                    FieldCondition(
                        key="page_content",
                        match=MatchValue(value="Under Secretary"),
                    )
                ]), collection_name="designation_course")
    print(results)