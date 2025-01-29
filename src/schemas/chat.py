from pydantic import BaseModel
from typing import Any, Dict, List, Optional

# Input data model
class ChatInputModel(BaseModel):
    query: str
    additional_metadata: Optional[Dict[str, Any]] = {}

# Output data model
class ChatOutputModel(BaseModel):
    turn_id: str
    msg_id: str
    contents: List[str]
    message: Dict[str, Any]

class ChatSessionCreateModel(BaseModel):
    user_id: str
    session_id: Optional[str | None] = None
    additional_metadata: Optional[Dict[str, Any]] = {}

class ChatSessionResponseModel(BaseModel):
    session_id: str

class MessageFeedbackCreateModel(BaseModel):
    turn_id: str
    msg_id: str
    rating: int
    comments: Optional[str] = None

class ContentFeedbackCreateModel(BaseModel):
    msg_id: str
    content_id: str
    rating: int
    comments: Optional[str] = None

