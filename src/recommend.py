from typing import Any, Dict
from fastapi import HTTPException,status
from sqlalchemy.orm import Session
from src.core.constants import TOTAL_SIMILAR_COURSE
from src.tools import fetch_course, get_domain_specific_courses, get_sector_course, get_similar_courses, DEFAULT_COURSES, get_unique_courses
from src.crud import (create_feedback, create_recommendation, get_recommended_course_by_id
                     , get_recommendation_with_feedback, get_recommendation_with_courses)


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

    # Priority 4: Department alone (with sector mapping)
    # if not recommended_courses:
    #     recommended_courses = get_courses_by_department(data)

    sector_courses = []
    # if not recommended_courses:
    #     sector_courses = get_sector_course(data)
    
    unique_contents = get_unique_courses(recommended_courses + sector_courses + DEFAULT_COURSES)
    recommendation = create_recommendation(db=db, recommended_courses=unique_contents, **data)
    recommendation_data = get_recommendation_with_courses(db,recommendation.id)
    return recommendation_data

def submit_feedback(db: Session, request):
    recommended_course = get_recommended_course_by_id(db, request.recommendation_id, request.course_id)
    if not recommended_course:
        return None
    
    return create_feedback(db, request)


def get_recommendation_with_feedbacks(db: Session, recommendation_id: str):
    return get_recommendation_with_feedback(db, recommendation_id=recommendation_id)

