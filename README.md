# Course Recommendation Service

## Overview
This service provides a personalized recommendation system for government employees, helping them find relevant training courses. The API includes chat functionalities, recommendations, and feedback mechanisms.

## Dependencies
Before you begin, ensure you have the following installed on your system:
- **Python 3.11+**
- **Redis**
- **Qdrant**
- **PostgreSQL**
- **Docker** (optional for containerized deployment)


## Setup Instructions
### 1. Clone the Repository
```bash
git clone https://github.com/KB-iGOT/course-recommendation-service.git
cd course-recommendation-service
```

### 2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

### 3. Install Dependencies
```bash
poetry install
```

### 4. Rename `.env.example` to `.env` and update environment variables
```bash
mv .env.example .env
```
Edit the `.env` file and update the necessary variables.

### 5. Start the FastAPI Server
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
Access the API at http://localhost:8000/docs.

## API Endpoints

### Health Check
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Check API service health |

### Chat APIs
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chat/session/start` | Start a chat session |
| POST | `/api/chat/session/{session_id}` | Continue chat in a session |
| POST | `/api/chat/message/feedback` | Submit message feedback |
| POST | `/api/chat/message/content/feedback` | Submit content feedback |

### Recommendation APIs
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/recommendation/create` | Generate recommendation |
| GET | `/api/recommendation/read/{recommendation_id}` | Get recommendation with feedback |
| POST | `/api/recommendation/feedback` | Submit recommendation feedback |

## Running with Docker
### 1. Build the Docker Image
```bash
docker build -t course-recommendation:latest .
```
### 2. Run the Container
```bash
docker run -d -p 8000:8000 --env-file .env --name course-recommendation-container course-recommendation:latest
```

## For Qdrant Setup

To get started with Qdrant, please follow these steps:

1. **Download the latest Qdrant image from Dockerhub:**

   ```bash
   docker pull qdrant/qdrant
   ```

2. **Run the Qdrant service:**

   ```bash
   docker run -p 6333:6333 --name qdrant -p 6334:6334 \
       -v /opt/qdrant_storage:/qdrant/storage:z \
       qdrant/qdrant
   ```

   Under the default configuration, all data will be stored in the `./qdrant_storage` directory. This will be the only directory that both the Container and the host machine can access.

3. **Access Qdrant:**

   - REST API: [http://localhost:6333](http://localhost:6333)
   - Web UI: [http://localhost:6333/dashboard](http://localhost:6333/dashboard)
   - GRPC API: [localhost:6334](http://localhost:6334)

## Upload Snapshots

- Go to the `scripts` the folder  
- Run the script with the folder path and base URL of Qdrant Vector DB as arguments:

   ```./upload_snapshots.sh /path/to/your/folder http://localhost:6333```
