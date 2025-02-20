from typing import Any, Dict, List
from fastapi import HTTPException,status
import requests
from sqlalchemy.orm import Session
from src.core.constants import TOTAL_SIMILAR_COURSE
from src.tools import fetch_course, get_domain_specific_courses, get_sector_course, get_similar_courses, DEFAULT_COURSES, get_unique_courses
from src.crud import (create_feedback, create_recommendation, get_recommended_course_by_id
                     , get_recommendation_with_feedback, get_recommendation_with_courses)
from src.core import config


def remove_whitespace(data):
    """Recursively removes whitespace from strings within a dictionary or list."""
    if isinstance(data, str):
        return data.strip()
    elif isinstance(data, dict):
        return {k: remove_whitespace(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [remove_whitespace(item) for item in data]
    else:
        return data  # Keep other data types as they are


def get_courses_by_designation(data):
  """
  Retrieves courses based on department and designation.
  """
  print("Retrieves courses based on department and designation.")
  domain_courses = get_domain_specific_courses(data)
  similar_courses = get_similar_courses(data)
  return domain_courses + similar_courses

def get_courses_by_competency(data: Dict[str, str]):
  """
  Retrieves courses based on competencies.
  """
  print("Retrieves courses based on competencies.")
  competencies = data["competency"].split(",")
  courses = fetch_course(filter={"contentType": "Course","competencies_v5.competencyTheme": competencies})
  courses = courses['result']['content'] if courses['result']['count'] > 0 else []
  return courses[:TOTAL_SIMILAR_COURSE]

def get_courses_by_role(data):
  """
  Retrieves courses based on role responsibilities.
  """
  print("Retrieves courses based on role responsibilities.")
  query = data["role_responsibility"]
  courses = fetch_course(filter={"contentType": "Course"}, query=query)
  courses = courses['result']['content'] if courses['result']['count'] > 0 else []
  return courses[:TOTAL_SIMILAR_COURSE]

def get_courses_by_department(data):
  """
  Retrieves courses based on department and sector mapping.
  """
  # Implement your logic to fetch courses from your data source
  print("Retrieves courses based on department and sector mapping.")
  return []

def generate_recommendations(db: Session, request):
    data = remove_whitespace(request.model_dump())
    recommended_courses = []
    # Priority 1: Department + Designation
    if request.designation:
        recommended_courses = get_courses_by_designation(data)

    # Priority 2: Department + Competency
    if not recommended_courses and request.competency:
        recommended_courses = get_courses_by_competency(data)

    # Priority 3: Department + Role Responsibility
    if not recommended_courses and request.role_responsibility:
        recommended_courses = get_courses_by_role(data)

    # Priority 4: Department alone
    if not recommended_courses:
        recommended_courses = get_courses_by_designation(data)

    sector_courses = []
    # if not recommended_courses:
    #     sector_courses = get_sector_course(data)
    
    unique_contents = get_unique_courses(recommended_courses + sector_courses + DEFAULT_COURSES)
    non_relevant_courses = get_non_relevant_courses(request.user_id)
    unique_contents = remove_courses(unique_contents, non_relevant_courses)
    recommendation = create_recommendation(db=db, recommended_courses=unique_contents, **data)
    recommendation_data = get_recommendation_with_courses(db,recommendation.id)
    return recommendation_data

def remove_courses(unique_contents, non_relevant_courses: Dict[str, any]):
    try:
        result = non_relevant_courses.get("result")

        if result and "courserecommendations" in result:
            courses_to_remove = result["courserecommendations"]
            courses_to_remove_set = set(courses_to_remove)  # For efficient lookup
            updated_unique_contents = [
                item for item in unique_contents if str(item["identifier"]) not in courses_to_remove_set
            ]
            return updated_unique_contents
        else:
            print("No 'courserecommendations' found. Returning original list.")
            return unique_contents  # Return original list if data is missing

    except (TypeError, AttributeError) as e:  # Handle type errors and other potential issues
        print(f"An error occurred: {e}. Returning original list.")
        return unique_contents  # Return original list in case of errors

def get_non_relevant_courses(user_id:str):
    url = f"{config.KB_CR_BASE_URL}/api/courseRecommendation/v1/read/{user_id}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"{config.KB_CR_AUTHORIZATION_TOKEN}"
    }
    payload = {}
    response = requests.request("GET", url, headers=headers, data=payload)
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print(f"Error while fethching non relevant course: {response.text}")
        print(f"Error: {response.status_code}")
        return None
    
def update_non_relevant_courses(user_id:str, courseIds: List[str]):
    url = f"{config.KB_CR_BASE_URL}/api/courseRecommendation/v1/update"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"{config.KB_CR_AUTHORIZATION_TOKEN}"
    }
    data = { "userId": user_id, "courseIds": courseIds }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print(f"Error while updating non relevant course: {response.text}")
        print(f"Error: {response.status_code}")
        return None

def submit_feedback(db: Session, request):
    recommended_course = get_recommended_course_by_id(db, request.recommendation_id, request.course_id)
    if not recommended_course:
        return None
    
    feedback = create_feedback(db, request)
    if not request.rating:
        update_non_relevant_courses(request.user_id, [request.course_id])
    return feedback


def get_recommendation_with_feedbacks(db: Session, recommendation_id: str):
    return get_recommendation_with_feedback(db, recommendation_id=recommendation_id)

