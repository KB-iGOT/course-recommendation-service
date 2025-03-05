import os
import time
from typing import List
import requests
from qdrant_client import QdrantClient
from qdrant_client.http.models.models import Filter, FieldCondition, MatchText, MatchValue
from src.core.config import (QDRANT_URL, OPENAI_API_KEY, OPENAI_EMBEDDING_MODEL, 
                             KB_CR_BASE_URL, KB_CR_AUTHORIZATION_TOKEN)

class NeuralSearcher:

    def __init__(self, collection_name: str | None = None):
        self.collection_name = collection_name
        self.qdrant_client = QdrantClient(QDRANT_URL)
        # self.qdrant_client.set_model(EMBEDDINGS_MODEL)


    def embed_text(self, text):
        url = f"{KB_CR_BASE_URL}/api/serviceregistry/v1/callExternalApi"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"{KB_CR_AUTHORIZATION_TOKEN}"
        }
        data = {
            "serviceCode": "openai-text-embedding-api",
            "requestBody": {
                "input": text,
                "model": OPENAI_EMBEDDING_MODEL,
                "encoding_format": "float"
            },
            "headerMap": {
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "content-type":"application/json"
            }
        }
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error while generating embedding: {response.text}")
            print(f"Error status code: {response.status_code}")

    def search(self, collection_name: str, text: str | None = None, filter_: any = None, limit = 5) -> List[dict]:
        print("collection_name :", collection_name)
        start_time = time.time()
        hits = self.qdrant_client.query_points(
            collection_name=collection_name,
            query= self.embed_text(text)['data'][0]['embedding'] if text else text,
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