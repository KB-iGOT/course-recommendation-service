import os
os.environ.setdefault("LOG_LEVEL", "INFO")
import sys
import types
from unittest.mock import MagicMock, AsyncMock, Mock, patch
import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException
import atexit

mock_session = MagicMock()

patcher1 = patch("src.database.SessionLocal", return_value=mock_session)
patcher1.start()
atexit.register(patcher1.stop)

patcher2 = patch("src.database.engine", MagicMock())
patcher2.start()
atexit.register(patcher2.stop)

mock_agent = types.ModuleType("src.agent")

# mock GenerativeModel
mock_GenerativeModel = MagicMock()
mock_instance = MagicMock()
mock_instance.generate_content.return_value = "mock response"
mock_GenerativeModel.return_value = mock_instance
mock_agent.GenerativeModel = mock_GenerativeModel

# mock send_chat_message
mock_agent.send_chat_message = AsyncMock(return_value={"message": "mocked response"})

# inject into sys.modules
sys.modules["src.agent"] = mock_agent

from src.main import app

client = TestClient(app)


class TestRootEndpoint:
    def test_read_root(self):
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"This is": "iGOT AI APIs"}


class TestHealthCheck:
    def test_get_health(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "OK"}


class TestChatSessionStart:
    @patch('src.main.create_chat_session')
    @patch('src.main.get_db')
    def test_chat_session_start_success(self, mock_get_db, mock_create_session):
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_session = Mock()
        mock_session.id = "session_123"
        mock_create_session.return_value = mock_session

        response = client.post("/api/chat/session/start", json={
            "user_id": "user123",
            "session_id": "session_123"
        })

        assert response.status_code == 200
        assert response.json() == {"session_id": "session_123"}

    @patch('src.main.create_chat_session')
    @patch('src.main.get_db')
    def test_chat_session_start_http_exception(self, mock_get_db, mock_create_session):
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_create_session.side_effect = HTTPException(status_code=400, detail="Bad request")

        response = client.post("/api/chat/session/start", json={"user_id": "user123"})

        assert response.status_code == 400

    @patch('src.main.create_chat_session')
    @patch('src.main.get_db')
    def test_chat_session_start_generic_exception(self, mock_get_db, mock_create_session):
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_create_session.side_effect = Exception("Database error")

        response = client.post("/api/chat/session/start", json={"user_id": "user123"})

        assert response.status_code == 500
        assert "something went wrong" in response.json()["detail"]


class TestChat:
    @patch('src.main.handle_chat')
    @patch('src.main.get_db')
    def test_chat_success(self, mock_get_db, mock_handle_chat):
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_response = {
            "turn_id": "turn_123",
            "msg_id": "msg_123",
            "contents": [],
            "message": {"content": "Hello"}
        }
        mock_handle_chat.return_value = mock_response

        response = client.post("/api/chat/session/session_123", json={"query": "Hello"})

        assert response.status_code == 200
        assert response.json() == mock_response

    @patch('src.main.handle_chat')
    @patch('src.main.get_db')
    def test_chat_http_exception(self, mock_get_db, mock_handle_chat):
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_handle_chat.side_effect = HTTPException(status_code=404, detail="Session not found")

        response = client.post("/api/chat/session/session_123", json={"query": "Hello"})

        assert response.status_code == 404

    @patch('src.main.handle_chat')
    @patch('src.main.get_db')
    def test_chat_generic_exception(self, mock_get_db, mock_handle_chat):
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_handle_chat.side_effect = Exception("Chat error")

        response = client.post("/api/chat/session/session_123", json={"query": "Hello"})

        assert response.status_code == 500
        assert "something went wrong" in response.json()["detail"]


class TestSubmitMessageFeedback:
    @patch('src.main.save_message_feedback')
    @patch('src.main.get_db')
    def test_submit_message_feedback_success(self, mock_get_db, mock_save_feedback):
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_feedback = Mock()
        mock_save_feedback.return_value = mock_feedback

        response = client.post("/api/chat/message/feedback", json={
            "turn_id": "turn_123", "msg_id": "msg_123", "rating": 5
        })

        assert response.status_code == 200

    @patch('src.main.save_message_feedback')
    @patch('src.main.get_db')
    def test_submit_message_feedback_http_exception(self, mock_get_db, mock_save_feedback):
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_save_feedback.side_effect = HTTPException(status_code=400, detail="Invalid turn_id")

        response = client.post("/api/chat/message/feedback", json={
            "turn_id": "invalid", "msg_id": "msg_123", "rating": 5
        })

        assert response.status_code == 400

    @patch('src.main.save_message_feedback')
    @patch('src.main.get_db')
    def test_submit_message_feedback_generic_exception(self, mock_get_db, mock_save_feedback):
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_save_feedback.side_effect = Exception("Database error")

        response = client.post("/api/chat/message/feedback", json={
            "turn_id": "turn_123", "msg_id": "msg_123", "rating": 5
        })

        assert response.status_code == 500
        assert "Failed to submit message feedback" in response.json()["detail"]


class TestChatMessageContentFeedback:
    @patch('src.main.save_content_feedback')
    @patch('src.main.get_db')
    def test_chat_message_content_feedback_success(self, mock_get_db, mock_save_feedback):
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_feedback = Mock()
        mock_save_feedback.return_value = mock_feedback

        response = client.post("/api/chat/message/content/feedback", json={
            "msg_id": "msg_123", "content_id": "content_123", "rating": 4
        })

        assert response.status_code == 200
        assert "Content feedback submitted successfully" in response.json()["message"]

    @patch('src.main.save_content_feedback')
    @patch('src.main.get_db')
    def test_chat_message_content_feedback_http_exception(self, mock_get_db, mock_save_feedback):
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_save_feedback.side_effect = HTTPException(status_code=400, detail="Invalid msg_id")

        response = client.post("/api/chat/message/content/feedback", json={
            "msg_id": "invalid", "content_id": "content_123", "rating": 4
        })

        assert response.status_code == 400

    @patch('src.main.save_content_feedback')
    @patch('src.main.get_db')
    def test_chat_message_content_feedback_generic_exception(self, mock_get_db, mock_save_feedback):
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_save_feedback.side_effect = Exception("Database error")

        response = client.post("/api/chat/message/content/feedback", json={
            "msg_id": "msg_123", "content_id": "content_123", "rating": 4
        })

        assert response.status_code == 500
        assert "Failed to submit content feedback" in response.json()["detail"]


class TestGenerateRecommendation:
    @patch('src.main.generate_recommendations')
    @patch('src.main.get_db')
    def test_generate_recommendation_exception(self, mock_get_db, mock_generate):
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_generate.side_effect = Exception("Generation error")

        response = client.post("/api/recommendation/create", json={
            "user_id": "user123", "department": "IT"
        })

        assert response.status_code == 500
        assert "something went wrong" in response.json()["detail"]


class TestGetRecommendationWithFeedback:
    @patch('src.main.get_recommendation_with_feedbacks')
    @patch('src.main.get_db')
    def test_get_recommendation_not_found(self, mock_get_db, mock_get_rec):
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_get_rec.return_value = None

        response = client.get("/api/recommendation/read/invalid_rec")

        assert response.status_code == 404
        assert "does not exist" in response.json()["detail"]

    @patch('src.main.get_recommendation_with_feedbacks')
    @patch('src.main.get_db')
    def test_get_recommendation_http_exception(self, mock_get_db, mock_get_rec):
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_get_rec.side_effect = HTTPException(status_code=400, detail="Bad request")

        response = client.get("/api/recommendation/read/rec_123")

        assert response.status_code == 400

    @patch('src.main.get_recommendation_with_feedbacks')
    @patch('src.main.get_db')
    def test_get_recommendation_generic_exception(self, mock_get_db, mock_get_rec):
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_get_rec.side_effect = Exception("Database error")

        response = client.get("/api/recommendation/read/rec_123")

        assert response.status_code == 500
        assert "Internal Server Error" in response.json()["detail"]
