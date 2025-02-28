from datetime import datetime
from typing import Dict, List
import uuid
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, join, select
from src.models import (KBContentFeedback, KBFeedback, KBMessage, KBRecommendations,KBRecommendedCourses, KBRecommendedCoursesFeedback, 
                        KBSession, KBTurn, KBUser)
from src.schemas.recommend import RecommendationResponse

def create_user(db: Session, user_id: str, language_preference: str = "en"):
    # user_id = str(uuid.uuid4())
    db_user = KBUser(id=user_id, language_preference=language_preference)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_id(db: Session, user_id: str):
    return db.query(KBUser).filter(KBUser.id == user_id).first()

def create_session(db: Session, user_id: str, session_id: str = None, metadata: Dict = {}):
    session_id = session_id if session_id else str(uuid.uuid4()) 
    db_session = KBSession(id=session_id, user_id=user_id, additional_metadata=metadata)
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

def get_session_by_id(db: Session, session_id: str):
    return db.query(KBSession).filter(KBSession.id == session_id).first()

def get_session_by_turn_id(db: Session, turn_id: str):
    return db.query(KBSession).join(KBTurn).filter(KBTurn.id == turn_id).first()

def update_session(db: Session, session_id: str):
    session = db.query(KBSession).filter(KBSession.id == session_id).first()
    if session:
        session.updated_at = datetime.now()
        db.commit()
    return session

def create_turn(db: Session, session_id: str, user_id: str):
    turn_id = str(uuid.uuid4())
    db_turn = KBTurn(id=turn_id, session_id=session_id, user_id=user_id)
    db.add(db_turn)
    db.commit()
    db.refresh(db_turn)
    return db_turn

def update_turn(db: Session, session_id: str, turn_id: str):
    turn = db.query(KBTurn).filter(KBTurn.id == turn_id).first()
    if turn:
        turn.session_id = session_id
        db.commit()
    return turn

def get_turn_by_id(db: Session, turn_id: str):
    return db.query(KBTurn).filter(KBTurn.id == turn_id).first()

def create_message(db: Session, turn_id: int, sender: str, content: str, message_type: str, metadata: dict = {}):
    msg_id = str(uuid.uuid4())
    db_message = KBMessage(id=msg_id, turn_id=turn_id, sender=sender, content=content, message_type=message_type, additional_metadata=metadata)
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

def get_message_by_id(db: Session, msg_id: str):
    return db.query(KBMessage).filter(KBMessage.id == msg_id).first()


def create_message_feedback(db: Session, feedback):
    feedback_entry = KBFeedback(
        turn_id=feedback.turn_id,
        msg_id=feedback.msg_id,
        rating=feedback.rating,
        comment=feedback.comments
    )
    db.add(feedback_entry)
    db.commit()
    db.refresh(feedback_entry)
    return feedback_entry

def create_content_feedback(db: Session, feedback):
    content_feedback_entry = KBContentFeedback(
        msg_id=feedback.msg_id,
        content_id=feedback.content_id,
        rating=feedback.rating,
        comment=feedback.comments
    )
    db.add(content_feedback_entry)
    db.commit()
    db.refresh(content_feedback_entry)
    return content_feedback_entry

# Create Recommendation
def create_recommendation(db: Session, recommended_courses: list, **kwargs):
    try:
        recommendation_id = str(uuid.uuid4())
        recommendation = KBRecommendations(id=recommendation_id,**kwargs)
        db.add(recommendation)
        db.commit()

        # Add recommended courses
        courses = [
            KBRecommendedCourses(
                recommendation_id=recommendation_id,
                course_id=course["identifier"],
                position=index + 1,  # Position starts from 1
            )
            for index, course in enumerate(recommended_courses)
        ]
        db.bulk_save_objects(courses)
        
        db.commit()
        db.refresh(recommendation)
        return recommendation
    except Exception as e:
        db.rollback()
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

def get_recommendation_with_courses_and_feedback(db: Session, recommendation_id: str):
    """
    Retrieves all columns from KBRecommendations and KBRecommendedCoursesFeedback, along with related course data.
    """
    query = (
        select(
            KBRecommendations.id,
            KBRecommendations.user_id,
            KBRecommendedCourses.course_id,
            KBRecommendedCourses.position,
            KBRecommendedCoursesFeedback.id,
            KBRecommendedCoursesFeedback.rating,
            KBRecommendedCoursesFeedback.comments,
        )
        .select_from(
            join(
                KBRecommendations,
                KBRecommendedCourses,
                KBRecommendations.id == KBRecommendedCourses.recommendation_id,
            )
        )
        .outerjoin(
            KBRecommendedCoursesFeedback,
            and_(
                KBRecommendedCourses.course_id == KBRecommendedCoursesFeedback.course_id,
                KBRecommendations.user_id == KBRecommendedCoursesFeedback.user_id,
            ),
        )
        .where(
            and_(
                KBRecommendations.id == recommendation_id
            )
        )
    )
    results = db.execute(query).fetchall()
    results = convert_results_to_recommendation_response(results)
    return results


def convert_results_to_recommendation_response(results):
    """
    Converts database query results to a RecommendationResponse object.
    """
    if not results:
        return None

    recommendation_id = results[0][0]
    user_id = results[0][1]

    recommended_courses: List = []
    feedbacks: List = []

    for row in results:
        recommended_courses.append({
            "course_id":row[2],
            "position":row[3],
        })
        if row[4] is not None: #check if feedback id exist
            feedbacks.append({
                "id":row[4],
                "course_id":row[2],
                "rating":row[5],
                "comments":row[6],
            })

    response = RecommendationResponse(
        id=recommendation_id,
        user_id=user_id,
        recommended_courses=recommended_courses,
        feedbacks=feedbacks,
    )

    return response

# Get Recommendation by ID
def get_recommendation_by_id(db: Session, recommendation_id: str):      
    return db.query(KBRecommendations).filter(KBRecommendations.id == recommendation_id).first()

# Get Recommendations for User
def get_recommendations_for_user(db: Session, user_id: str):
    return db.query(KBRecommendations).filter(KBRecommendations.user_id == user_id).all()

# Get Recommended courses by ID
def get_recommended_course_by_id(db: Session, recommendation_id: str, course_id: str):
    return db.query(KBRecommendedCourses).filter(
        KBRecommendedCourses.course_id == course_id, 
        KBRecommendedCourses.recommendation_id == recommendation_id 
    ).first()

# Create Feedback
def create_feedback(db: Session, feedback_req):
    feedback = KBRecommendedCoursesFeedback(
        user_id = feedback_req.user_id,
        recommendation_id= feedback_req.recommendation_id,
        course_id=feedback_req.course_id,
        rating=feedback_req.rating,
        comments=feedback_req.comments
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback