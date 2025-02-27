from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, validator
from datetime import datetime


class DeviceType(Enum):
    MOBILE = "mobile"
    WEB = "web"

# Pydantic Models for Request Body
class RecommendationCreateRequest(BaseModel):
    user_id: str
    department: str
    designation: Optional[str] = None
    competency: Optional[str] = None
    role_responsibility: Optional[str] = None
    device_type: Optional[str] = None

    @validator("device_type")
    def validate_device_type(cls, value):
        if value is not None:  # Allow None values
            value = value.lower() #handle cases like "Web", "WEB", "web"
            allowed_types = {"web", "mobile"}
            if value not in allowed_types:
                raise ValueError(f"device_type must be one of: {allowed_types}")
        return value
    
    @validator("designation")
    def empty_string_to_none(cls, value: str):
        if not value or len(value.strip()) == 0:
            return None
        return value

class FeedbackCreateRequest(BaseModel):
    user_id: str
    recommendation_id: str
    course_id: str
    rating: int
    comments: Optional[str] = None

class RecommendedCourseFeedback(BaseModel):
    id: int 
    course_id: str
    rating: int
    comments: Optional[str]
    submitted_at: datetime

class RecommendedCourse(BaseModel):
    course_id: str
    position: int

class RecommendationResponse(BaseModel):
    id: str
    user_id: str
    department: str
    designation: Optional[str]
    competency: Optional[str]
    role_responsibility: Optional[str]
    device_type: Optional[str]
    created_at: datetime
    recommended_courses: List[RecommendedCourse]
    feedbacks: List[RecommendedCourseFeedback]

    # @field_serializer("created_at")
    # def serialize_created_at(self, created_at: datetime) -> str:
    #     return created_at.isoformat()  # Convert datetime to ISO 8601 string
    
    class Config:
        from_attributes = True

class FeedbackResponse(BaseModel):
    # feedback_id: int
    message: str = "Feedback submitted successfully"