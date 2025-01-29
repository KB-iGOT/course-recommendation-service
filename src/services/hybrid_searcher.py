from qdrant_client import QdrantClient
from qdrant_client.http.models.models import Filter, FieldCondition, MatchText, MatchValue
import time
from src.core.config import QDRANT_URL


class HybridSearcher:
    DENSE_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    SPARSE_MODEL = "prithivida/Splade_PP_en_v1"
    def __init__(self, collection_name: str | None = None):
        self.collection_name = collection_name
        # initialize Qdrant client
        self.qdrant_client = QdrantClient(QDRANT_URL)
        self.qdrant_client.set_model(self.DENSE_MODEL)
        # comment this line to use dense vectors only
        self.qdrant_client.set_sparse_model(self.SPARSE_MODEL)

    def search(self, collection_name: str, text: str | None = None, filter_: any = None, limit = 5):
        print("collection_name :", collection_name)
        start_time = time.time()

        if not text and filter_:
            search_result = self.qdrant_client.query_points(
                collection_name=f"{collection_name}_hybrid",
                query_filter=filter_,  # If you don't want any filters for now
                limit=limit,  # 5 the closest results
            ).points
        else:
            search_result = self.qdrant_client.query(
                collection_name=f"{collection_name}_hybrid",
                query_text=text,
                query_filter=filter_ if filter_ else None,  # If you don't want any filters for now
                limit=limit,  # 5 the closest results
            )
        # `search_result` contains found vector ids with similarity scores 
        # along with the stored payloads
        # Select and return metadata
        results = []
        for hit in search_result:
            results.append({"score": hit.score, "metadata": hit.payload if "payload" in hit else hit.metadata})
        print(f"Search took {time.time() - start_time} seconds")
        return results
    


if __name__ == "__main__":
    hybrid_searcher = HybridSearcher()
    results = hybrid_searcher.search(filter_= Filter(
                must=[
                    FieldCondition(
                        key="metadata.department",
                        match=MatchText(text="Ministry of power"),
                    ),
                    FieldCondition(
                        key="page_content",
                        match=MatchValue(value="Under Secretary"),
                    )
                ]), text="Sorting of mails", collection_name="role_designation_hybrid")
    print(results)