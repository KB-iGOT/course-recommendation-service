import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session
from src.crud import (
    create_user, get_user_by_id, create_session, get_session_by_id,
    get_session_by_turn_id, update_session, create_turn, update_turn,
    get_turn_by_id, create_message, get_message_by_id, create_message_feedback,
    create_content_feedback, create_recommendation, get_recommendation_with_courses_and_feedback,
    convert_results_to_recommendation_response, get_recommendation_by_id,
    get_recommendations_for_user, get_recommended_course_by_id, create_feedback
)


class TestUserOperations:
    
    def test_create_user(self):
        db = Mock(spec=Session)
        db.add.return_value = None
        db.commit.return_value = None
        db.refresh.return_value = None
        
        result = create_user(db, "user123", "en")
        
        db.add.assert_called_once()
        db.commit.assert_called_once()
        db.refresh.assert_called_once()
        assert result.id == "user123"
        assert result.language_preference == "en"
    
    def test_create_user_default_language(self):
        db = Mock(spec=Session)
        
        result = create_user(db, "user123")
        
        assert result.language_preference == "en"
    
    def test_get_user_by_id(self):
        db = Mock(spec=Session)
        mock_user = Mock()
        db.query.return_value.filter.return_value.first.return_value = mock_user
        
        result = get_user_by_id(db, "user123")
        
        assert result == mock_user
        db.query.assert_called_once()


class TestSessionOperations:
    
    @patch('src.crud.uuid.uuid4')
    def test_create_session_with_session_id(self, mock_uuid):
        db = Mock(spec=Session)
        db.add.return_value = None
        db.commit.return_value = None
        db.refresh.return_value = None
        
        result = create_session(db, "user123", "session456", {"key": "value"})
        
        db.add.assert_called_once()
        db.commit.assert_called_once()
        db.refresh.assert_called_once()
        assert result.id == "session456"
        assert result.user_id == "user123"
    
    @patch('src.crud.uuid.uuid4')
    def test_create_session_without_session_id(self, mock_uuid):
        db = Mock(spec=Session)
        mock_uuid.return_value = "generated-uuid"
        
        result = create_session(db, "user123")
        
        assert result.id == "generated-uuid"
    
    def test_get_session_by_id(self):
        db = Mock(spec=Session)
        mock_session = Mock()
        db.query.return_value.filter.return_value.first.return_value = mock_session
        
        result = get_session_by_id(db, "session123")
        
        assert result == mock_session
    
    def test_get_session_by_turn_id(self):
        db = Mock(spec=Session)
        mock_session = Mock()
        db.query.return_value.join.return_value.filter.return_value.first.return_value = mock_session
        
        result = get_session_by_turn_id(db, "turn123")
        
        assert result == mock_session
    
    @patch('src.crud.datetime')
    def test_update_session_exists(self, mock_datetime):
        db = Mock(spec=Session)
        mock_session = Mock()
        mock_now = datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = mock_now
        db.query.return_value.filter.return_value.first.return_value = mock_session
        
        result = update_session(db, "session123")
        
        assert result == mock_session
        assert mock_session.updated_at == mock_now
        db.commit.assert_called_once()
    
    def test_update_session_not_exists(self):
        db = Mock(spec=Session)
        db.query.return_value.filter.return_value.first.return_value = None
        
        result = update_session(db, "nonexistent")
        
        assert result is None


class TestTurnOperations:
    
    @patch('src.crud.uuid.uuid4')
    def test_create_turn(self, mock_uuid):
        db = Mock(spec=Session)
        mock_uuid.return_value = "turn-uuid"
        
        result = create_turn(db, "session123", "user123")
        
        assert result.id == "turn-uuid"
        assert result.session_id == "session123"
        assert result.user_id == "user123"
        db.add.assert_called_once()
        db.commit.assert_called_once()
        db.refresh.assert_called_once()
    
    def test_update_turn_exists(self):
        db = Mock(spec=Session)
        mock_turn = Mock()
        db.query.return_value.filter.return_value.first.return_value = mock_turn
        
        result = update_turn(db, "session123", "turn123")
        
        assert result == mock_turn
        assert mock_turn.session_id == "session123"
        db.commit.assert_called_once()
    
    def test_update_turn_not_exists(self):
        db = Mock(spec=Session)
        db.query.return_value.filter.return_value.first.return_value = None
        
        result = update_turn(db, "session123", "nonexistent")
        
        assert result is None
    
    def test_get_turn_by_id(self):
        db = Mock(spec=Session)
        mock_turn = Mock()
        db.query.return_value.filter.return_value.first.return_value = mock_turn
        
        result = get_turn_by_id(db, "turn123")
        
        assert result == mock_turn


class TestMessageOperations:
    
    @patch('src.crud.uuid.uuid4')
    def test_create_message(self, mock_uuid):
        db = Mock(spec=Session)
        mock_uuid.return_value = "msg-uuid"
        
        result = create_message(db, 123, "user", "Hello", "text", {"meta": "data"})
        
        assert result.id == "msg-uuid"
        assert result.turn_id == 123
        assert result.sender == "user"
        assert result.content == "Hello"
        assert result.message_type == "text"
        db.add.assert_called_once()
        db.commit.assert_called_once()
        db.refresh.assert_called_once()
    
    def test_get_message_by_id(self):
        db = Mock(spec=Session)
        mock_message = Mock()
        db.query.return_value.filter.return_value.first.return_value = mock_message
        
        result = get_message_by_id(db, "msg123")
        
        assert result == mock_message


class TestFeedbackOperations:
    
    def test_create_message_feedback(self):
        db = Mock(spec=Session)
        feedback = Mock()
        feedback.turn_id = "turn123"
        feedback.msg_id = "msg123"
        feedback.rating = 5
        feedback.comments = "Great"
        
        result = create_message_feedback(db, feedback)
        
        assert result.turn_id == "turn123"
        assert result.msg_id == "msg123"
        assert result.rating == 5
        assert result.comment == "Great"
        db.add.assert_called_once()
        db.commit.assert_called_once()
        db.refresh.assert_called_once()
    
    def test_create_content_feedback(self):
        db = Mock(spec=Session)
        feedback = Mock()
        feedback.msg_id = "msg123"
        feedback.content_id = "content123"
        feedback.rating = 4
        feedback.comments = "Good"
        
        result = create_content_feedback(db, feedback)
        
        assert result.msg_id == "msg123"
        assert result.content_id == "content123"
        assert result.rating == 4
        assert result.comment == "Good"
        db.add.assert_called_once()
        db.commit.assert_called_once()
        db.refresh.assert_called_once()


class TestRecommendationOperations:
    
    @patch('src.crud.uuid.uuid4')
    def test_create_recommendation_success(self, mock_uuid):
        db = Mock(spec=Session)
        mock_uuid.return_value = "rec-uuid"
        recommended_courses = [
            {"identifier": "course1"},
            {"identifier": "course2"}
        ]
        
        result = create_recommendation(db, recommended_courses, user_id="user123", department="IT")
        
        assert result.id == "rec-uuid"
        db.add.assert_called_once()
        db.commit.assert_called()
        db.bulk_save_objects.assert_called_once()
        db.refresh.assert_called_once()
    
    @patch('src.crud.uuid.uuid4')
    def test_create_recommendation_exception(self, mock_uuid):
        db = Mock(spec=Session)
        mock_uuid.return_value = "rec-uuid"
        db.commit.side_effect = Exception("Database error")
        
        with pytest.raises(HTTPException) as exc_info:
            create_recommendation(db, [], user_id="user123")
        
        assert exc_info.value.status_code == 500
        db.rollback.assert_called_once()
    
    @patch('src.crud.convert_results_to_recommendation_response')
    def test_get_recommendation_with_courses_and_feedback(self, mock_convert):
        db = Mock(spec=Session)
        mock_results = [("rec1", "user1", "course1", 1, "fb1", 5, "Great")]
        db.execute.return_value.fetchall.return_value = mock_results
        mock_convert.return_value = {"id": "rec1"}
        
        result = get_recommendation_with_courses_and_feedback(db, "rec123")
        
        assert result == {"id": "rec1"}
        mock_convert.assert_called_once_with(mock_results)

    def test_convert_results_to_recommendation_response_empty(self):
        result = convert_results_to_recommendation_response([])
        assert result is None
    
    def test_get_recommendation_by_id(self):
        db = Mock(spec=Session)
        mock_rec = Mock()
        db.query.return_value.filter.return_value.first.return_value = mock_rec
        
        result = get_recommendation_by_id(db, "rec123")
        
        assert result == mock_rec
    
    def test_get_recommendations_for_user(self):
        db = Mock(spec=Session)
        mock_recs = [Mock(), Mock()]
        db.query.return_value.filter.return_value.all.return_value = mock_recs
        
        result = get_recommendations_for_user(db, "user123")
        
        assert result == mock_recs
    
    def test_get_recommended_course_by_id(self):
        db = Mock(spec=Session)
        mock_course = Mock()
        db.query.return_value.filter.return_value.first.return_value = mock_course
        
        result = get_recommended_course_by_id(db, "rec123", "course123")
        
        assert result == mock_course
    
    def test_create_feedback(self):
        db = Mock(spec=Session)
        feedback_req = Mock()
        feedback_req.user_id = "user123"
        feedback_req.recommendation_id = "rec123"
        feedback_req.course_id = "course123"
        feedback_req.rating = 5
        feedback_req.comments = "Excellent"
        
        result = create_feedback(db, feedback_req)
        
        assert result.user_id == "user123"
        assert result.recommendation_id == "rec123"
        assert result.course_id == "course123"
        assert result.rating == 5
        assert result.comments == "Excellent"
        db.add.assert_called_once()
        db.commit.assert_called_once()
        db.refresh.assert_called_once()