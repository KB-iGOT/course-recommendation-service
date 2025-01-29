from fastapi import HTTPException
from sqlalchemy.orm import Session
from src.agent import send_chat_message
from src.crud import (create_content_feedback, create_message, create_message_feedback, create_session, create_turn, create_user, get_message_by_id,
                      get_session_by_id, get_turn_by_id, get_user_by_id, update_session)
from src.core.logger import logger

def get_or_create_user(db: Session, user_id: str):
    try:
        user = get_user_by_id(db, user_id)
        if not user:
            user = create_user(db, user_id)
        return user
    except Exception as e:
        logger.error(f"Error in get_or_create_user: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve or create user")

def create_chat_session(db: Session, request):
    user = get_or_create_user(db, request.user_id)
    session = create_session(db, user.id, request.session_id, request.additional_metadata)
    return session

def handle_chat(db: Session, session_id: str, request):
    # Get or create user
    session = get_session_by_id(db, session_id)

    # Manage session
    # session = manage_session(user.id, session_id, db)

    # Create turn
    turn = create_turn(db, session.id, session.user_id)

    # Create input message
    input_message = create_message(db, turn.id, "user", request.query, "text", request.additional_metadata)

    # start chat
    output_content = send_chat_message(request.query, session.id)

    # Create output message
    output_message = create_message(db, turn.id, "bot", output_content["content"], "text", output_content["response_metadata"])
    session = update_session(db, session.id)

    return {
        "turn_id": turn.id,
        "msg_id": output_message.id,
        "contents": [],
        "message": output_content
    }

def save_message_feedback(db: Session, request):
    # Validate if turn and message exist
    turn = get_turn_by_id(db, request.turn_id)
    message = get_message_by_id(db, request.msg_id)
    if not turn:
        raise HTTPException(status_code=400, detail="Invalid turn_id")
    if not message:
        raise HTTPException(status_code=400, detail="Invalid msg_id")
    
    feedback = create_message_feedback(db, request)
    return feedback

def save_content_feedback(db: Session, request):
    # Validate if message exist
    message = get_message_by_id(db, request.msg_id)
    if not message:
        raise HTTPException(status_code=400, detail="Invalid msg_id")
    
    feedback = create_content_feedback(db, request)
    return feedback