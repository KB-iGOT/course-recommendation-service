

# Qdrant Indexing and Embedding Tool

This tool enables efficient embedding and indexing of text data stored in CSV files into a Qdrant collection. It supports batch processing, parallel execution, 

## Usage

### Command-Line Arguments

| Argument              | Description                                    | Required | Example                                  |
|-----------------------|------------------------------------------------|----------|------------------------------------------|
| `--collection_name`   | Name of the Qdrant collection                  | Yes      | `my_collection`                         |
| `--csv_folder_path`   | Path to the folder containing CSV files        | Yes      | `/path/to/csv/folder`                   |
| `--index_field_name`  | Comma-separated field names for indexing       | Yes      | `title,description`                     |
| `--text_field_name`   | Comma-separated field names for text indexing  | No       | `content`                               |
| `--keyword_field_name`| Comma-separated field names for keyword indexing| No       | `category,tag`                          |

### Run the Script

Execute the script with the required arguments:
```bash
python index_documents.py \
  --collection_name my_collection \
  --csv_folder_path /path/to/csv/folder \
  --index_field_name title,description \
  --text_field_name content \
  --keyword_field_name category,tag 
```

---

## Workflow

1. **Initialize Qdrant**:
   - The script checks if the specified Qdrant collection exists.
   - If not, it creates the collection with appropriate vector configurations.

2. **CSV Processing**:
   - Reads CSV files from the specified folder.
   - Converts rows into document objects with metadata.

3. **Embedding Generation**:
   - Generates embeddings in batches using Google API.
   - Points are prepared with metadata and vector embeddings.

4. **Upload to Qdrant**:
   - The generated points are uploaded to the Qdrant collection.

---

## Example

Given the following CSV:

| title       | description           | content               | category |
|-------------|-----------------------|-----------------------|----------|
| Sample Doc  | Example description   | This is sample text.  | Example  |

The script will:

1. Create vector embeddings for the `content` field.
2. Index `title` and `description` as searchable text.
3. Index `category` as a keyword.

---

## Notes

- Ensure the CSV files contain the specified index fields.
- Invalid rows (e.g., missing index fields) will be ignored.

---