from sqlalchemy import JSON, Column, Integer, String, Text, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.database import Base
import enum

class SenderEnum(enum.Enum):
    user = 'user'
    bot = 'bot'

class KBUser(Base):
    __tablename__ = "kb_users"

    id = Column(String, primary_key=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    language_preference = Column(String, default="en", nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

class KBSession(Base):
    __tablename__ = "kb_sessions"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("kb_users.id"), index=True, nullable=False)
    additional_metadata = Column(JSON, nullable=True, default={})
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        onupdate=func.now(),
    )

    turns = relationship("KBTurn", back_populates="session", cascade="all, delete-orphan")

class KBTurn(Base):
    __tablename__ = "kb_turns"

    id = Column(String, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("kb_sessions.id"), index=True, nullable=False)
    user_id = Column(String, ForeignKey("kb_users.id"), index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    session = relationship("KBSession", back_populates="turns")
    messages = relationship("KBMessage", back_populates="turn", cascade="all, delete-orphan")

class KBMessage(Base):
    __tablename__ = "kb_messages"

    id = Column(String, primary_key=True, index=True)
    turn_id = Column(String, ForeignKey('kb_turns.id', ondelete="CASCADE"), index=True, nullable=False)
    sender = Column(Enum(SenderEnum), nullable=False)
    content = Column(Text, nullable=False)
    message_type = Column(String, nullable=True, default="text")
    additional_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    turn = relationship("KBTurn", back_populates="messages")
    contents = relationship("KBMessageContent", back_populates="message", cascade="all, delete-orphan")
    feedback = relationship("KBFeedback", back_populates="message", uselist=False, cascade="all, delete-orphan")
    content_feedbacks = relationship("KBContentFeedback", back_populates="message", cascade="all, delete-orphan")

class KBMessageContent(Base):
    __tablename__ = "kb_message_contents"

    id = Column(Integer, primary_key=True, index=True)
    msg_id = Column(String, ForeignKey('kb_messages.id', ondelete="CASCADE"), index=True, nullable=False)
    content_id = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    message = relationship("KBMessage", back_populates="contents")

class KBContentFeedback(Base):
    __tablename__ = "kb_content_feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    msg_id = Column(String, ForeignKey('kb_messages.id', ondelete="CASCADE"), index=True, nullable=False)
    content_id = Column(String, nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    message = relationship("KBMessage", back_populates="content_feedbacks")

class KBFeedback(Base):
    __tablename__ = "kb_feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    turn_id = Column(String, ForeignKey('kb_turns.id', ondelete="CASCADE"), index=True, nullable=False)
    msg_id = Column(String, ForeignKey('kb_messages.id', ondelete="CASCADE"), index=True, nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    turn = relationship("KBTurn")
    message = relationship("KBMessage", back_populates="feedback")


class KBRecommendations(Base):
    __tablename__ = "kb_recommendations"

    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=True, index=True)
    department = Column(String, index=True, nullable=False)
    designation = Column(String, nullable=True)
    competency = Column(String, nullable=True)
    role_responsibility = Column(String, nullable=True)
    device_type = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    recommended_courses = relationship("KBRecommendedCourses", back_populates="recommendation")
    feedbacks = relationship("KBRecommendedCoursesFeedback", back_populates="recommendation")

class KBRecommendedCourses(Base):
    __tablename__ = "kb_recommended_courses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    recommendation_id = Column(String, ForeignKey("kb_recommendations.id"), nullable=False, index=True)
    course_id = Column(String, nullable=False, index=True)
    position = Column(Integer, nullable=False)

    # Relationships
    recommendation = relationship("KBRecommendations", back_populates="recommended_courses")
    

class KBRecommendedCoursesFeedback(Base):
    __tablename__ = "kb_recommended_courses_feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    recommendation_id = Column(String, ForeignKey("kb_recommendations.id"), nullable=False, index=True)
    user_id = Column(String, nullable=False, index=True)
    course_id = Column(String, nullable=False, index=True)
    rating = Column(Integer)  # Use Boolean for 0/1 (False/True)
    comments = Column(String, nullable=True)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())

    recommendation = relationship("KBRecommendations", back_populates="feedbacks")