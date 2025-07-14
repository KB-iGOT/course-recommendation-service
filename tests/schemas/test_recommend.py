import pytest
from pydantic import ValidationError
from src.schemas.recommend import RecommendationCreateRequest


class TestRecommend:

    @pytest.mark.parametrize("designation_input", ["", "   "])
    def test_empty_string_designation_becomes_none(self, designation_input):
        """
        Empty or whitespace-only designation should be converted to None.
        """
        request = RecommendationCreateRequest(
            user_id="test_user",
            department="test_department",
            designation=designation_input
        )
        assert request.designation is None

    def test_non_empty_designation_remains(self):
        """
        Non-empty designation remains unchanged.
        """
        designation_input = "Software Engineer"
        request = RecommendationCreateRequest(
            user_id="test_user",
            department="test_department",
            designation=designation_input
        )
        assert request.designation == designation_input

    @pytest.mark.parametrize("device_type_input, expected", [
        ("web", "web"),
        ("WEB", "web"),
        ("Web", "web"),
        ("mobile", "mobile"),
        ("MOBILE", "mobile"),
        ("Mobile", "mobile"),
    ])
    def test_valid_device_type(self, device_type_input, expected):
        """
        Valid device types (in any case) should return lowercased version.
        """
        request = RecommendationCreateRequest(
            user_id="user1",
            department="IT",
            device_type=device_type_input
        )
        assert request.device_type == expected

    def test_none_device_type(self):
        """
        If device_type is None, it should stay None.
        """
        request = RecommendationCreateRequest(
            user_id="test_user",
            department="IT",
            device_type=None
        )
        assert request.device_type is None

    def test_invalid_device_type_raises(self):
        """
        Invalid device type should raise ValidationError.
        """
        with pytest.raises(ValidationError) as exc_info:
            RecommendationCreateRequest(
                user_id="test_user",
                department="test_department",
                device_type="invalid_type"
            )
        error_msg = str(exc_info.value)
        assert "device_type must be one of" in error_msg
