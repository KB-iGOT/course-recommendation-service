from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from src.core.config import (POSTGRES_DATABASE_HOST, POSTGRES_DATABASE_NAME, POSTGRES_DATABASE_PASSWORD
                        , POSTGRES_DATABASE_PORT, POSTGRES_DATABASE_USERNAME)

SQLALCHEMY_DATABASE_URL = f"postgresql://{POSTGRES_DATABASE_USERNAME}:{POSTGRES_DATABASE_PASSWORD}@{POSTGRES_DATABASE_HOST}:{POSTGRES_DATABASE_PORT}/{POSTGRES_DATABASE_NAME}"

# Create SQLAlchemy engine and session maker
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()