import pytest
from unittest.mock import Mock, patch, MagicMock
from src.tools import (
    fetch_course, extract_competency_theme_above_threshold, 
    extract_competency_theme_and_course_above_threshold, extract_course,
    extract_course_above_threshold, extract_sector_above_threshold, trim_data,
    get_unique_courses, prepare_markdown, get_competenncies, filter_courses_by_master_list,
    get_similar_courses, get_domain_specific_courses, get_sector_course,
    fetch_course_list, fetch_desgination_list, fetch_acronnym_list,
    fetch_department_list, extract_function_calls, call_function
)


class TestFetchCourse:
    
    @patch('src.tools.requests.post')
    def test_fetch_course_success(self, mock_post):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": {"content": [{"id": "course1"}]}}
        mock_post.return_value = mock_response
        
        result = fetch_course({"contentType": "Course"}, "test query")
        
        assert result == {"result": {"content": [{"id": "course1"}]}}
        mock_post.assert_called_once()
    
    @patch('src.tools.requests.post')
    def test_fetch_course_error(self, mock_post):
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Server error"
        mock_post.return_value = mock_response
        
        result = fetch_course({"contentType": "Course"})
        
        assert result is None


class TestExtractFunctions:
    
    def test_extract_competency_theme_above_threshold(self):
        scored_points = [
            {"score": 0.8, "metadata": {"competency_theme": "skill1,skill2"}},
            {"score": 0.6, "metadata": {"competency_theme": "skill3"}}
        ]
        
        result = extract_competency_theme_above_threshold(scored_points)
        
        assert result == ["skill1", "skill2"]
    
    def test_extract_competency_theme_and_course_above_threshold(self):
        scored_points = [
            {"score": 0.8, "metadata": {"competency_theme": "skill1", "course_ids": "course1,course2"}},
            {"score": 0.6, "metadata": {"competency_theme": "skill2"}}
        ]
        
        themes, courses = extract_competency_theme_and_course_above_threshold(scored_points)
        
        assert themes == ["skill1"]
        assert courses == ["course1", "course2"]
    
    def test_extract_course(self):
        scored_points = [
            {"metadata": {"course_ids": "course1,course2"}},
            {"metadata": {"course_ids": "course3"}}
        ]
        
        result = extract_course(scored_points)
        
        assert result == ["course1", "course2", "course3"]
    
    def test_extract_course_above_threshold(self):
        scored_points = [
            {"score": 0.8, "metadata": {"course_ids": "course1"}},
            {"score": 0.6, "metadata": {"course_ids": "course2"}}
        ]
        
        result = extract_course_above_threshold(scored_points)
        
        assert result == ["course1"]
    
    def test_extract_sector_above_threshold(self):
        scored_points = [
            {"score": 0.8, "metadata": {"sector_name": "sector1,sector2"}},
            {"score": 0.6, "metadata": {"sector_name": "sector3"}}
        ]
        
        result = extract_sector_above_threshold(scored_points)
        
        assert result == ["sector1", "sector2"]


class TestTrimData:
    
    def test_trim_data(self):
        data = ["  item1  ", "  item2  ", "item3"]
        result = trim_data(data)
        assert result == ["item1", "item2", "item3"]


class TestGetUniqueCourses:
    
    def test_get_unique_courses_valid_list(self):
        courses = [
            {"identifier": "1", "name": "Course1"},
            {"identifier": "2", "name": "Course2"},
            {"identifier": "1", "name": "Course1 Duplicate"}
        ]
        
        result = get_unique_courses(courses)
        
        assert len(result) == 2
        assert result[0]["identifier"] == "1"
        assert result[1]["identifier"] == "2"
    
    def test_get_unique_courses_none_input(self):
        result = get_unique_courses(None)
        assert result == []
    
    def test_get_unique_courses_invalid_entries(self):
        courses = [
            {"identifier": "1", "name": "Course1"},
            {"name": "Course2"},  # Missing identifier
            "invalid_entry"  # Not a dict
        ]
        
        result = get_unique_courses(courses)
        
        assert len(result) == 1
        assert result[0]["identifier"] == "1"


class TestPrepareMarkdown:
    
    def test_prepare_markdown(self):
        data = [
            {
                "name": "Course1",
                "identifier": "course1",
                "competencies_v5": [{"competencyArea": "Skill1"}, {"competencyArea": "Skill2"}]
            }
        ]
        
        result = prepare_markdown(data)
        
        assert "Course1" in result
        assert "course1" in result
        assert "Skill1, Skill2" in result or "Skill2, Skill1" in result


class TestGetCompetencies:
    
    @patch('src.tools.retriever.search')
    @patch('src.tools.extract_course_above_threshold')
    @patch('src.tools.extract_course')
    @patch('src.tools.extract_competency_theme_above_threshold')
    @patch('src.tools.extract_competency_theme_and_course_above_threshold')
    def test_get_competencies_relevant_courses(self, mock_extract_comp_course, mock_extract_comp, 
                                             mock_extract_course, mock_extract_course_threshold, mock_search):
        data = {"department": "IT", "designation": "Engineer"}
        non_relevant_courses = []
        
        mock_extract_course_threshold.return_value = ["course1", "course2", "course3", "course4", "course5", 
                                                    "course6", "course7", "course8", "course9", "course10"]
        
        competencies, course_ids = get_competenncies(data, non_relevant_courses)
        
        assert len(course_ids) == 10
        assert competencies == []
    
    @patch('src.tools.retriever.search')
    @patch('src.tools.extract_course_above_threshold')
    @patch('src.tools.extract_course')
    @patch('src.tools.extract_competency_theme_above_threshold')
    def test_get_competencies_exact_search(self, mock_extract_comp, mock_extract_course, 
                                         mock_extract_course_threshold, mock_search):
        data = {"department": "IT", "designation": "Engineer"}
        non_relevant_courses = []
        
        mock_extract_course_threshold.return_value = []
        mock_search.side_effect = [[], [{"metadata": {"course_ids": "course1"}}], []]
        mock_extract_course.return_value = ["course1"]
        mock_extract_comp.return_value = ["skill1"]
        
        competencies, course_ids = get_competenncies(data, non_relevant_courses)
        
        assert course_ids == ["course1"]
        assert competencies == ["skill1"]


class TestFilterCoursesByMasterList:
    
    def test_filter_courses_by_master_list(self):
        courses = ["course1", "course2", "course3"]
        master_content = ["course1", "course3", "course4"]
        
        result = filter_courses_by_master_list(courses, master_content)
        
        assert result == ["course1", "course3"]


class TestGetSimilarCourses:
    
    @patch('src.tools.fetch_course')
    @patch('src.tools.get_competenncies')
    def test_get_similar_courses_with_course_ids(self, mock_get_comp, mock_fetch):
        data = {"department": "IT"}
        mock_get_comp.return_value = ([], ["course1", "course2"])
        mock_fetch.side_effect = [
            {"result": {"count": 2, "content": [{"id": "course1"}, {"id": "course2"}]}},
            {"result": {"count": 0, "content": []}}
        ]
        
        result = get_similar_courses(data)
        
        assert len(result) == 2
    
    @patch('src.tools.fetch_course')
    @patch('src.tools.get_competenncies')
    def test_get_similar_courses_with_competencies(self, mock_get_comp, mock_fetch):
        data = {"department": "IT"}
        mock_get_comp.return_value = (["skill1"], [])
        mock_fetch.return_value = {"result": {"count": 1, "content": [{"id": "course1"}]}}
        
        result = get_similar_courses(data)
        
        assert len(result) == 1


class TestGetDomainSpecificCourses:
    
    @patch('src.tools.fetch_course')
    @patch('src.tools.retriever.search')
    @patch('src.tools.extract_course_above_threshold')
    def test_get_domain_specific_courses(self, mock_extract, mock_search, mock_fetch):
        data = {"department": "IT"}
        mock_extract.return_value = ["course1", "course2"]
        mock_fetch.return_value = {"result": {"count": 2, "content": [{"id": "course1"}]}}
        
        result = get_domain_specific_courses(data)
        
        assert len(result) == 1


class TestGetSectorCourse:
    
    @patch('src.tools.fetch_course')
    @patch('src.tools.retriever.search')
    @patch('src.tools.extract_sector_above_threshold')
    def test_get_sector_course(self, mock_extract, mock_search, mock_fetch):
        data = {"department": "IT"}
        mock_extract.return_value = ["sector1"]
        mock_fetch.return_value = {"result": {"count": 1, "content": [{"id": "course1"}]}}
        
        result = get_sector_course(data)
        
        assert len(result) == 1


class TestFetchFunctions:
    
    @patch('src.tools.get_domain_specific_courses')
    @patch('src.tools.get_similar_courses')
    @patch('src.tools.get_unique_courses')
    @patch('src.tools.prepare_markdown')
    def test_fetch_course_list(self, mock_markdown, mock_unique, mock_similar, mock_domain):
        data = {"department": "IT"}
        mock_domain.return_value = [{"identifier": "1"}]
        mock_similar.return_value = [{"identifier": "2"}]
        mock_unique.return_value = [{"identifier": "1"}, {"identifier": "2"}]
        mock_markdown.return_value = "markdown text"
        
        result = fetch_course_list(data)
        
        assert result == "markdown text"
    
    @patch('src.tools.retriever.search')
    def test_fetch_designation_list_with_department_filter(self, mock_search):
        data = {"department": "IT", "query": "engineer"}
        mock_search.return_value = [
            {"score": 0.8, "metadata": {"designation": "Software Engineer"}},
            {"score": 0.5, "metadata": {"designation": "Junior Engineer"}}
        ]
        
        result = fetch_desgination_list(data)
        
        assert result == ["Software Engineer"]
    
    @patch('src.tools.retriever.search')
    def test_fetch_designation_list_fallback(self, mock_search):
        data = {"department": "IT", "query": "engineer"}
        mock_search.side_effect = [
            [],  # First search returns empty
            [{"score": 0.8, "metadata": {"designation": "Engineer"}}]  # Second search
        ]
        
        result = fetch_desgination_list(data)
        
        assert result == ["Engineer"]
    
    @patch('src.tools.retriever.search')
    def test_fetch_acronym_list(self, mock_search):
        data = {"department": "IT", "acronym": "SE"}
        mock_search.return_value = [
            {"score": 0.8, "metadata": {"designation": "Software Engineer"}}
        ]
        
        result = fetch_acronnym_list(data)
        
        assert result == ["Software Engineer"]
    
    @patch('src.tools.retriever.search')
    def test_fetch_department_list(self, mock_search):
        data = {"query": "technology"}
        mock_search.return_value = [
            {"score": 0.8, "metadata": {"name": "Information Technology"}}
        ]
        
        result = fetch_department_list(data)
        
        assert result == ["Information Technology"]


class TestExtractFunctionCalls:
    
    def test_extract_function_calls(self):
        mock_response = Mock()
        mock_function_call = Mock()
        mock_function_call.name = "get_course_list"
        mock_function_call.args = {"department": "IT", "designation": "Engineer"}
        mock_response.candidates = [Mock()]
        mock_response.candidates[0].function_calls = [mock_function_call]
        
        result = extract_function_calls(mock_response)
        
        assert len(result) == 1
        assert "get_course_list" in result[0]
        assert result[0]["get_course_list"]["department"] == "IT"
    
    def test_extract_function_calls_no_calls(self):
        mock_response = Mock()
        mock_response.candidates = [Mock()]
        mock_response.candidates[0].function_calls = None
        
        result = extract_function_calls(mock_response)
        
        assert result == []


class TestCallFunction:
    
    @patch('src.tools.function_handler')
    @patch('src.tools.Part.from_function_response')
    def test_call_function(self, mock_part, mock_handler):
        functions = [{"get_course_list": {"department": "IT", "designation": "Engineer"}}]
        mock_handler.__getitem__.return_value = Mock(return_value="test response")
        mock_part.return_value = Mock()
        
        result = call_function(functions)
        
        assert len(result) == 1
        mock_part.assert_called_once()