import os
import time
from typing import List
from vertexai.language_models import TextEmbeddingInput, TextEmbeddingModel, TextEmbedding
import vertexai
from qdrant_client import QdrantClient
from qdrant_client.http.models.models import Filter, FieldCondition, MatchText, MatchValue
from src.core.config import QDRANT_URL, GOOGLE_LOCATION,  GOOGLE_PROJECT_ID, TEXT_EMBEDDING_MODEL_ID

GOOGLE_PROJECT_ID = GOOGLE_PROJECT_ID
GOOGLE_LOCATION = GOOGLE_LOCATION
MODEL_ID = TEXT_EMBEDDING_MODEL_ID

vertexai.init(project=GOOGLE_PROJECT_ID, location=GOOGLE_LOCATION)

class NeuralSearcher:

    def __init__(self, collection_name: str | None = None):
        self.collection_name = collection_name
        self.qdrant_client = QdrantClient(QDRANT_URL)
        self.model = TextEmbeddingModel.from_pretrained(MODEL_ID)
        # self.qdrant_client.set_model(EMBEDDINGS_MODEL)

    def embed_text(self, text) -> List[TextEmbedding]:
        """Embeds texts with a pre-trained, foundational model.

        Returns:
            A list of lists containing the embedding vectors for each input text
        """
        # The dimensionality of the output embeddings.
        dimensionality = 768
        # The task type for embedding. Check the available tasks in the model's documentation.
        task = "RETRIEVAL_QUERY"

        
        inputs = [TextEmbeddingInput(text, task)]
        kwargs = dict(output_dimensionality=dimensionality) if dimensionality else {}
        embeddings = self.model.get_embeddings(inputs, **kwargs)
        return embeddings

    def search(self, collection_name: str, text: str | None = None, filter_: any = None, limit = 5) -> List[dict]:
        print("collection_name :", collection_name)
        start_time = time.time()
        hits = self.qdrant_client.query_points(
            collection_name=collection_name,
            query= self.embed_text(text)[0].values if text else text,
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