import sys
import pytest
from unittest.mock import MagicMock, Mock, patch
from sqlalchemy.orm import Session

# Patch problematic modules *only in this file*
@pytest.fixture(autouse=True, scope='module')
def patch_problematic_modules():
    original_tools = sys.modules.get('src.tools')
    original_searcher = sys.modules.get('src.services.neural_searcher')

    sys.modules['src.tools'] = MagicMock()
    sys.modules['src.services.neural_searcher'] = MagicMock()

    yield

    # Restore originals after tests
    if original_tools is not None:
        sys.modules['src.tools'] = original_tools
    else:
        del sys.modules['src.tools']
    
    if original_searcher is not None:
        sys.modules['src.services.neural_searcher'] = original_searcher
    else:
        del sys.modules['src.services.neural_searcher']

# import after patching to avoid type errors in Python <3.9
from src.recommend import (
    remove_whitespace, get_courses_by_designation, get_courses_by_competency,
    get_courses_by_role, get_courses_by_department, generate_recommendations,
    remove_non_relevant_courses, getEnrolledCoursesForUser, get_non_relevant_courses,
    update_non_relevant_courses, submit_feedback, get_recommendation_with_feedbacks
)

class TestRemoveWhitespace:
    
    def test_string_whitespace_removal(self):
        assert remove_whitespace("  test  ") == "test"
        assert remove_whitespace("") == ""
    
    def test_dict_whitespace_removal(self):
        data = {"key": "  value  ", "nested": {"inner": "  test  "}}
        expected = {"key": "value", "nested": {"inner": "test"}}
        assert remove_whitespace(data) == expected
    
    def test_list_whitespace_removal(self):
        data = ["  item1  ", "  item2  "]
        expected = ["item1", "item2"]
        assert remove_whitespace(data) == expected
    
    def test_other_types_unchanged(self):
        assert remove_whitespace(123) == 123
        assert remove_whitespace(None) is None


class TestGetCoursesByDesignation:
    
    @patch('src.recommend.get_similar_courses')
    @patch('src.recommend.get_domain_specific_courses')
    def test_get_courses_by_designation(self, mock_domain, mock_similar):
        data = {"department": "IT"}
        non_relevant = ["course1"]
        mock_domain.return_value = [{"id": "domain1"}]
        mock_similar.return_value = [{"id": "similar1"}]
        
        result = get_courses_by_designation(data, non_relevant)
        
        assert result == [{"id": "domain1"}, {"id": "similar1"}]
        mock_domain.assert_called_once_with(data, non_relevant)
        mock_similar.assert_called_once_with(data, non_relevant)


class TestGetCoursesByCompetency:
    
    @patch('src.recommend.fetch_course')
    def test_get_courses_by_competency_with_results(self, mock_fetch):
        data = {"competency": "skill1,skill2"}
        mock_fetch.return_value = {
            'result': {'count': 2, 'content': [{"id": "course1"}, {"id": "course2"}]}
        }
        
        result = get_courses_by_competency(data)
        
        assert len(result) <= 10  # TOTAL_SIMILAR_COURSE limit
        mock_fetch.assert_called_once()
    
    @patch('src.recommend.fetch_course')
    def test_get_courses_by_competency_no_results(self, mock_fetch):
        data = {"competency": "skill1"}
        mock_fetch.return_value = {'result': {'count': 0, 'content': []}}
        
        result = get_courses_by_competency(data)
        
        assert result == []


class TestGetCoursesByRole:
    
    @patch('src.recommend.fetch_course')
    def test_get_courses_by_role_with_results(self, mock_fetch):
        data = {"role_responsibility": "manager"}
        mock_fetch.return_value = {
            'result': {'count': 1, 'content': [{"id": "course1"}]}
        }
        
        result = get_courses_by_role(data)
        
        assert len(result) <= 10
        mock_fetch.assert_called_once()
    
    @patch('src.recommend.fetch_course')
    def test_get_courses_by_role_no_results(self, mock_fetch):
        data = {"role_responsibility": "test"}
        mock_fetch.return_value = {'result': {'count': 0, 'content': []}}
        
        result = get_courses_by_role(data)
        
        assert result == []


class TestGetCoursesByDepartment:
    
    def test_get_courses_by_department(self):
        data = {"department": "IT"}
        result = get_courses_by_department(data)
        assert result == []


class TestGenerateRecommendations:
    
    @patch('src.recommend.get_recommendation_with_courses_and_feedback')
    @patch('src.recommend.create_recommendation')
    @patch('src.recommend.remove_non_relevant_courses')
    @patch('src.recommend.get_unique_courses')
    @patch('src.recommend.get_courses_by_designation')
    @patch('src.recommend.getEnrolledCoursesForUser')
    @patch('src.recommend.get_non_relevant_courses')
    @patch('src.recommend.remove_whitespace')
    def test_generate_recommendations_with_designation(self, mock_remove_ws, mock_non_relevant, 
                                                     mock_enrolled, mock_designation, mock_unique,
                                                     mock_remove_non_relevant, mock_create, mock_get_rec):
        db = Mock(spec=Session)
        request = Mock()
        request.model_dump.return_value = {"user_id": "user1", "designation": "engineer"}
        request.user_id = "user1"
        request.designation = "engineer"
        request.competency = None
        request.role_responsibility = None
        
        mock_remove_ws.return_value = {"user_id": "user1", "designation": "engineer"}
        mock_non_relevant.return_value = ["course1"]
        mock_enrolled.return_value = ["course2"]
        mock_designation.return_value = [{"identifier": "course3"}]
        mock_unique.return_value = [{"identifier": "course3"}]
        mock_remove_non_relevant.return_value = [{"identifier": "course3"}]
        mock_rec = Mock()
        mock_rec.id = "rec1"
        mock_create.return_value = mock_rec
        mock_get_rec.return_value = {"id": "rec1"}
        
        result = generate_recommendations(db, request)
        
        assert result == {"id": "rec1"}
        mock_designation.assert_called_once()

    @patch('src.recommend.get_recommendation_with_courses_and_feedback')
    @patch('src.recommend.create_recommendation')
    @patch('src.recommend.remove_non_relevant_courses')
    @patch('src.recommend.get_unique_courses')
    @patch('src.recommend.get_courses_by_competency')
    @patch('src.recommend.get_courses_by_designation')
    @patch('src.recommend.getEnrolledCoursesForUser')
    @patch('src.recommend.get_non_relevant_courses')
    @patch('src.recommend.remove_whitespace')
    def test_generate_recommendations_with_competency(self, mock_remove_ws, mock_non_relevant,
                                                    mock_enrolled, mock_designation, mock_competency,
                                                    mock_unique, mock_remove_non_relevant, mock_create, mock_get_rec):
        db = Mock(spec=Session)
        request = Mock()
        request.model_dump.return_value = {"user_id": "user1", "competency": "skill1"}
        request.user_id = "user1"
        request.designation = None
        request.competency = "skill1"
        request.role_responsibility = None
        
        mock_remove_ws.return_value = {"user_id": "user1", "competency": "skill1"}
        mock_non_relevant.return_value = []
        mock_enrolled.return_value = []
        mock_designation.return_value = []
        mock_competency.return_value = [{"identifier": "course4"}]
        mock_unique.return_value = [{"identifier": "course4"}]
        mock_remove_non_relevant.return_value = [{"identifier": "course4"}]
        mock_rec = Mock()
        mock_rec.id = "rec2"
        mock_create.return_value = mock_rec
        mock_get_rec.return_value = {"id": "rec2"}
        
        result = generate_recommendations(db, request)
        
        assert result == {"id": "rec2"}
        mock_competency.assert_called_once()


class TestRemoveNonRelevantCourses:
    
    def test_remove_non_relevant_courses_success(self):
        courses = [{"identifier": "1"}, {"identifier": "2"}, {"identifier": "3"}]
        non_relevant = ["2"]
        
        result = remove_non_relevant_courses(courses, non_relevant)
        
        assert len(result) == 2
        assert result == [{"identifier": "1"}, {"identifier": "3"}]
    
    def test_remove_non_relevant_courses_error(self):
        courses = [{"bad_key": "1"}]  # Missing 'identifier' key
        non_relevant = ["1"]

        with pytest.raises(KeyError):
            remove_non_relevant_courses(courses, non_relevant)


class TestGetEnrolledCoursesForUser:
    
    @patch('src.recommend.requests.request')
    def test_get_enrolled_courses_success(self, mock_request):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": {"courses": [{"courseId": "course1"}, {"courseId": "course2"}]}
        }
        mock_request.return_value = mock_response
        
        result = getEnrolledCoursesForUser("user1")
        
        assert result == ["course1", "course2"]
    
    @patch('src.recommend.requests.request')
    def test_get_enrolled_courses_no_courses(self, mock_request):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": {"courses": None}}
        mock_request.return_value = mock_response
        
        result = getEnrolledCoursesForUser("user1")
        
        assert result == []
    
    @patch('src.recommend.requests.request')
    def test_get_enrolled_courses_error(self, mock_request):
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Server error"
        mock_request.return_value = mock_response
        
        result = getEnrolledCoursesForUser("user1")
        
        assert result == []


class TestGetNonRelevantCourses:
    
    @patch('src.recommend.requests.request')
    def test_get_non_relevant_courses_success(self, mock_request):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": {"courserecommendations": ["course1", "course2"]}
        }
        mock_request.return_value = mock_response
        
        result = get_non_relevant_courses("user1")
        
        assert result == ["course1", "course2"]
    
    @patch('src.recommend.requests.request')
    def test_get_non_relevant_courses_no_recommendations(self, mock_request):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": {}}
        mock_request.return_value = mock_response
        
        result = get_non_relevant_courses("user1")
        
        assert result == []
    
    @patch('src.recommend.requests.request')
    def test_get_non_relevant_courses_error(self, mock_request):
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not found"
        mock_request.return_value = mock_response
        
        result = get_non_relevant_courses("user1")
        
        assert result == []


class TestUpdateNonRelevantCourses:
    
    @patch('src.recommend.requests.post')
    def test_update_non_relevant_courses_success(self, mock_post):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_post.return_value = mock_response
        
        result = update_non_relevant_courses("user1", ["course1"])
        
        assert result == {"success": True}
    
    @patch('src.recommend.requests.post')
    def test_update_non_relevant_courses_error(self, mock_post):
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Server error"
        mock_post.return_value = mock_response
        
        result = update_non_relevant_courses("user1", ["course1"])
        
        assert result is None


class TestSubmitFeedback:
    
    @patch('src.recommend.update_non_relevant_courses')
    @patch('src.recommend.create_feedback')
    @patch('src.recommend.get_recommended_course_by_id')
    def test_submit_feedback_with_rating(self, mock_get_course, mock_create_feedback, mock_update):
        db = Mock(spec=Session)
        request = Mock()
        request.recommendation_id = "rec1"
        request.course_id = "course1"
        request.rating = 5
        request.user_id = "user1"
        
        mock_get_course.return_value = Mock()
        mock_feedback = Mock()
        mock_create_feedback.return_value = mock_feedback
        
        result = submit_feedback(db, request)
        
        assert result == mock_feedback
        mock_update.assert_not_called()
    
    @patch('src.recommend.update_non_relevant_courses')
    @patch('src.recommend.create_feedback')
    @patch('src.recommend.get_recommended_course_by_id')
    def test_submit_feedback_without_rating(self, mock_get_course, mock_create_feedback, mock_update):
        db = Mock(spec=Session)
        request = Mock()
        request.recommendation_id = "rec1"
        request.course_id = "course1"
        request.rating = None
        request.user_id = "user1"
        
        mock_get_course.return_value = Mock()
        mock_feedback = Mock()
        mock_create_feedback.return_value = mock_feedback
        
        result = submit_feedback(db, request)
        
        assert result == mock_feedback
        mock_update.assert_called_once_with("user1", ["course1"])
    
    @patch('src.recommend.get_recommended_course_by_id')
    def test_submit_feedback_no_course(self, mock_get_course):
        db = Mock(spec=Session)
        request = Mock()
        request.recommendation_id = "rec1"
        request.course_id = "course1"
        
        mock_get_course.return_value = None
        
        result = submit_feedback(db, request)
        
        assert result is None


class TestGetRecommendationWithFeedbacks:
    
    @patch('src.recommend.get_recommendation_with_courses_and_feedback')
    def test_get_recommendation_with_feedbacks(self, mock_get_rec):
        db = Mock(spec=Session)
        recommendation_id = "rec1"
        expected_result = {"id": "rec1", "feedbacks": []}
        mock_get_rec.return_value = expected_result
        
        result = get_recommendation_with_feedbacks(db, recommendation_id)
        
        assert result == expected_result
        mock_get_rec.assert_called_once_with(db, recommendation_id=recommendation_id)