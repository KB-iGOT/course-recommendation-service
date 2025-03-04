from typing import List
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from src.chat import create_chat_session, handle_chat, save_content_feedback, save_message_feedback
from src.core.logger import logger
from src.database import engine, get_db
from src.models import Base
from src.schemas.recommend import RecommendationCreateRequest, RecommendationResponse, FeedbackCreateRequest, FeedbackResponse
from src.schemas.chat import (ChatInputModel, ChatOutputModel, ChatSessionCreateModel, 
                              ChatSessionResponseModel, ContentFeedbackCreateModel, MessageFeedbackCreateModel)
from sqlalchemy.orm import Session
from src.recommend import generate_recommendations, submit_feedback, get_recommendation_with_feedbacks

# Create the tables in the database
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class HealthCheck(BaseModel):
    """Response model to validate and return when performing a health check."""
    status: str = "OK"


@app.get("/")
def read_root():
    return {"This is": "iGOT AI APIs"}

@app.post(
    "/api/chat/session/start",
    tags=["Chat APIs"],
    status_code=status.HTTP_200_OK,
    response_model=ChatSessionResponseModel
)
def chat_session_start(request: ChatSessionCreateModel, db: Session = Depends(get_db)):
    try:
        session = create_chat_session(db, request)
        return ChatSessionResponseModel(session_id=session.id)
    except HTTPException as e:
        raise e    
    except Exception as e:
        logger.exception("Error while creating chat session")
        raise HTTPException(status_code=500, detail=str("Oops, something went wrong! We couldn't process your request. Please try again later."))

@app.post(
    "/api/chat/session/{session_id}",
    tags=["Chat APIs"],
    status_code=status.HTTP_200_OK,
    response_model=ChatOutputModel
)
def chat(session_id: str, request: ChatInputModel, db: Session = Depends(get_db)):
    try:
        chat_response = handle_chat(db, session_id, request)
        return chat_response
    except HTTPException as e:
        raise e    
    except Exception as e:
        logger.exception("Error while generatig chat response")
        raise HTTPException(status_code=500, detail=str("Oops, something went wrong! We couldn't process your request. Please try again later or rephrase your query."))

@app.post(
    "/api/chat/message/feedback",
    tags=["Chat APIs"],
    status_code=status.HTTP_200_OK,
    response_model=FeedbackResponse
)
def submit_message_feedback(request: MessageFeedbackCreateModel, db: Session = Depends(get_db)):
    """
    Submit feedback for a message at the turn level.
    """
    try:
        message_feedback = save_message_feedback(db, request)
        return FeedbackResponse()
    except HTTPException as e:
        raise e    
    except Exception as e:
        logger.exception("Error while saving message feedback")
        raise HTTPException(status_code=500, detail=str("Failed to submit message feedback"))

@app.post(
    "/api/chat/message/content/feedback",
    tags=["Chat APIs"],
    status_code=status.HTTP_200_OK,
    response_model=FeedbackResponse
)
def chat_message_content_feedback(request: ContentFeedbackCreateModel, db: Session = Depends(get_db)):
    """
    Submit feedback for a specific content within a message.
    """
    try:
        content_feedback = save_content_feedback(db, request)
        return FeedbackResponse(message="Content feedback submitted successfully.")
    except HTTPException as e:
        raise e    
    except Exception as e:
        logger.exception("Error while saving content feedback")
        raise HTTPException(status_code=500, detail=str("Failed to submit content feedback"))


# Endpoint to create a recommendation
@app.post(
    "/api/recommendation/create", 
    tags=["Recommendation APIs"],
    status_code=status.HTTP_200_OK,
    response_model=RecommendationResponse
)
def generate_recommendation(request: RecommendationCreateRequest, db: Session = Depends(get_db)):
    """
    Generate a new recommendation for a user by providing details and a list of course IDs.
    """
    try:
        logger.info(f"Received recommendation request: {request.model_dump()}")
        recommendation = generate_recommendations(db, request)

        logger.info(f"Recommendation created successfully")
        return recommendation
    except Exception as e:
        logger.exception("Unexpected error occurred while generating recommendations")
        raise HTTPException(status_code=500, detail=str("Oops, something went wrong! We couldn't process your request. Please try again later!"))

# Endpoint to get recommendation with feedback
@app.get(
    "/api/recommendation/read/{recommendation_id}", 
    tags=["Recommendation APIs"],
    response_model=RecommendationResponse
)
def get_recommendation_with_feedback_endpoint(recommendation_id: str, db: Session = Depends(get_db)):
    """
    Retrieve a recommendation along with all associated feedback.
    """
    try:
        logger.debug(f"Attempting to fetch recommendation for ID: {recommendation_id}")
        recommendation = get_recommendation_with_feedbacks(db, recommendation_id=recommendation_id)
        
        if not recommendation:
            logger.warning(f"Recommendation not found for ID: {recommendation_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation ID does not exist")
        
        logger.info(f"Recommendation retrieved successfully: {recommendation_id}")
        return recommendation
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.exception("Unexpected error occurred while fetching recommendations")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

# Endpoint to save feedback
@app.post(
    "/api/recommendation/feedback", 
    tags=["Recommendation APIs"],
    status_code=status.HTTP_201_CREATED, 
    response_model=FeedbackResponse,
)
async def save_feedback(request: FeedbackCreateRequest, db: Session = Depends(get_db)):
    """
    Save feedback for a course based on the provided recommendation ID and course ID.
    """
    try:
        logger.debug(f"Received feedback request: {request.model_dump()}")

        feedback = submit_feedback(db, request) 
        if not feedback:
            logger.warning(f"Invalid recommendation or course ID: {request.recommendation_id}, {request.course_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation or Course ID does not exist")
        
        logger.info(f"Feedback saved successfully: {feedback.id}")
        return FeedbackResponse(feedback_id=feedback.id)
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.exception("Unexpected error occurred while saving feedback")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

@app.get(
    "/health",
    tags=["Health Check APIs"],
    summary="Perform a Health Check",
    response_description="Return HTTP Status Code 200 (OK)",
    status_code=status.HTTP_200_OK,
    response_model=HealthCheck,
    include_in_schema=True,
)
def get_health() -> HealthCheck:
    """
    ## Perform a Health Check
    Endpoint to perform a healthcheck on. This endpoint can primarily be used Docker
    to ensure a robust container orchestration and management is in place. Other
    services which rely on proper functioning of the API service will not deploy if this
    endpoint returns any other HTTP status code except 200 (OK).
    Returns:
        HealthCheck: Returns a JSON response with the health status
    """
    return HealthCheck(status="OK")