import os
from dotenv import load_dotenv

load_dotenv()

# Qdrant 
QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
QDRANT_DEPARTMENT_COLLECTION_NAME= os.environ.get("QDRANT_DEPARTMENT_COLLECTION_NAME", "departments")
QDRANT_COMPETENCY_COLLECTION_NAME= os.environ.get("QDRANT_COMPETENCY_COLLECTION_NAME", "competencies")
QDRANT_ACRONYM_COLLECTION_NAME= os.environ.get("QDRANT_ACRONYM_COLLECTION_NAME", "abbreviations")
QDRANT_ROLE_COLLECTION_NAME= os.environ.get("QDRANT_ROLE_COLLECTION_NAME", "role_designation")
QDRANT_RELEVANT_COLLECTION_NAME=os.environ.get("QDRANT_RELEVANT_COLLECTION_NAME", "relevant_course")
QDRANT_DESIGNATION_COLLECTION_NAME=os.environ.get("QDRANT_DESIGNATION_COLLECTION_NAME", "designation_course")
QDRANT_GROUP_COLLECTION_NAME=os.environ.get("QDRANT_GROUP_COLLECTION_NAME", "designation_group")
QDRANT_DOMAIN_SECTOR_COLLECTION_NAME=os.environ.get("QDRANT_DOMAIN_SECTOR_COLLECTION_NAME", "domain_courses")
QDRANT_SECTOR_COLLECTION_NAME=os.environ.get("QDRANT_SECTOR_COLLECTION_NAME", "sector_course")

# KB COMPOSITE SEARCH API
KB_BASE_URL = os.environ.get("KB_BASE_URL", "https://portal.igotkarmayogi.gov.in")
KB_AUTHORIZATION_TOKEN = os.environ.get("KB_AUTHORIZATION_TOKEN")

# KB Course non-relevant APIs
KB_CR_BASE_URL = os.environ.get("KB_CR_BASE_URL", "https://portal.igotkarmayogi.gov.in")
KB_CR_AUTHORIZATION_TOKEN = os.environ.get("KB_CR_AUTHORIZATION_TOKEN")


#Gemini confiuration
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-1.5-pro-001")
MODEL_TEMPERATURE = int(os.environ.get("MODEL_TEMPERATURE", 0))
GOOGLE_PROJECT_ID = os.environ.get("GOOGLE_PROJECT_ID")
GOOGLE_LOCATION = os.environ.get("LOCATION", "us-central1")
GOOGLE_APPLICATION_CREDENTIALS= os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")

# OpenAI
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_EMBEDDING_MODEL = os.environ.get("OPENAI_EMBEDDING_MODEL")

# Redis
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
REDIS_DB = int(os.environ.get('REDIS_DB', 0))
REDIS_TTL = int(os.environ.get('REDIS_TTL', '43200')) # 12 hours (TTL in seconds)

# Postgres

POSTGRES_DATABASE_USERNAME= os.environ.get('POSTGRES_DATABASE_USERNAME', 'postgres')
POSTGRES_DATABASE_PASSWORD = os.environ.get('POSTGRES_DATABASE_PASSWORD', 'postgres')
POSTGRES_DATABASE_HOST = os.environ.get('POSTGRES_DATABASE_HOST', 'localhost')
POSTGRES_DATABASE_NAME = os.environ.get('POSTGRES_DATABASE_NAME', 'postgres')
POSTGRES_DATABASE_PORT = int(os.environ.get('POSTGRES_DATABASE_PORT', '5432'))