import argparse
import os
from typing import Any, Dict, List, Tuple
import pandas as pd
from qdrant_client import QdrantClient
from qdrant_client import models
from tqdm import tqdm
import uuid

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Qdrant Indexing and Embedding")
    
    # Add arguments
    parser.add_argument("--collection_name", type=str,required=True, help="Name of the collection")
    parser.add_argument("--csv_folder_path", type=str,required=True, help="Path to the folder containing CSV files")
    parser.add_argument("--index_field_name", type=str,required=True, help="Comma-separated field names for indexing")
    parser.add_argument("--text_field_name", type=str,required=True, help="Comma-separated field names for text indexing")
    parser.add_argument("--keyword_field_name", type=str,required=False, help="Comma-separated field names for keyword indexing")

    return parser.parse_args()

def create_qdrant_collection(client: QdrantClient, collection_name: str):
    """Create Qdrant collection if it doesn't exist."""
    if not client.collection_exists(collection_name):
        print(f"Creating collection: {collection_name}...")
        client.create_collection(
            collection_name=collection_name,
            vectors_config=client.get_fastembed_vector_params(),
            # comment this line to use dense vectors only
            sparse_vectors_config=client.get_fastembed_sparse_vector_params(),  
        )

def create_payload_indices(client: QdrantClient, collection_name: str, text_field_names: List[str], keyword_field_names: List[str]):
    """Create payload indices for text and keyword fields."""
    # Create text indices
    for text_field in text_field_names:
        if text_field:
            print(f"Creating text index for field: {text_field}")
            client.create_payload_index(
                collection_name=collection_name,
                field_name=f"metadata.{text_field}",
                field_schema=models.TextIndexParams(
                    type=models.TextIndexType.TEXT,
                    tokenizer=models.TokenizerType.WORD,
                    min_token_len=2,
                    max_token_len=20,
                    lowercase=True,
                )
            )

    # Create keyword indices
    for keyword_field in keyword_field_names:
        if keyword_field:
            print(f"Creating keyword index for field: {keyword_field}")
            client.create_payload_index(
                collection_name=collection_name,
                field_name=f"metadata.{keyword_field}",
                field_schema=models.PayloadSchemaType.KEYWORD,
            )

def df_to_documents(df: pd.DataFrame, index_field_names: List[str]) -> Tuple[List[str], List[Dict[str, Any]]]:
    """Convert DataFrame rows into a list of Document objects."""
    documents = []
    metadatas = []
    for _, row in df.iterrows():
        # Create a dictionary of metadata from the row
        metadata = row.to_dict()

        # Combine the index fields into a single page_content string
        page_content = "; ".join(str(row[field]) for field in index_field_names if field in row)

        # Remove the index fields from the metadata
        # for index_field in index_field_names:
        #     metadata.pop(index_field, None)

        # Append the Document with the combined page_content and the remaining metadata
        documents.append(page_content)
        metadatas.append(metadata)

    return documents, metadatas

class Document:
    """Class to represent a document with content and metadata."""
    def __init__(self, page_content, metadata):
        self.page_content = page_content
        self.metadata = metadata

def process_csv_file(file_path: str, index_field_names: List[str]) -> Tuple[List[str], List[Dict[str, Any]]]:
    """Process a single CSV file to generate embeddings and prepare points."""
    data = pd.read_csv(file_path, skipinitialspace=True)
    data.dropna(subset=index_field_names, inplace=True)

    # Remove empty columns
    nan_value = float("NaN")
    data.replace("", nan_value, inplace=True)
    data.dropna(how='all', axis=1, inplace=True)

    documents, metadatas = df_to_documents(data, index_field_names)
    return documents, metadatas

def main():
    # Parse command line arguments
    args = parse_args()

    # Convert comma-separated string arguments to lists
    COLLECTION_NAME = args.collection_name
    CSV_FOLDER_PATH = args.csv_folder_path
    INDEX_FIELD_NAMES = args.index_field_name.split(",") # Convert to list
    TEXT_FIELD_NAMES = args.text_field_name.split(",") if args.text_field_name else []   # Convert to list
    KEYWORD_FIELD_NAMES = args.keyword_field_name.split(",") if args.keyword_field_name else []  # Convert to list or empty if no value

    QDRANT_URL = os.environ.get("QDRANT_URL")
    DENSE_MODEL = os.environ.get("QDRANT_DENSE_MODEL")
    SPARSE_MODEL= os.environ.get("QDRANT_SPARSE_MODEL")

    # Init Qdrant client
    client = QdrantClient(QDRANT_URL)
    
    # Set Embedding models
    client.set_model(DENSE_MODEL)
    client.set_sparse_model(SPARSE_MODEL)

    # Create Qdrant collection if it doesn't exist
    create_qdrant_collection(client, COLLECTION_NAME)

    # Create payload indices (text and keyword fields)
    create_payload_indices(client, COLLECTION_NAME, TEXT_FIELD_NAMES, KEYWORD_FIELD_NAMES)

    # Loop through all CSV files in the provided folder
    for csv_file in os.listdir(CSV_FOLDER_PATH):
        if csv_file.endswith(".csv"):
            print(f"Processing file: {csv_file}")
            file_path = os.path.join(CSV_FOLDER_PATH, csv_file)

            # Process the current CSV file and generate points
            documents, metadatas = process_csv_file(file_path, INDEX_FIELD_NAMES)

            # Upload points to Qdrant
            client.add(
                collection_name=COLLECTION_NAME,
                documents=documents,
                batch_size=256, 
                metadata=metadatas,
                # parallel=4,  # Use all available CPU cores to encode data. 
                ids=tqdm([str(uuid.uuid4()) for _ in range(len(documents))])
            )

if __name__ == "__main__":
    main()
