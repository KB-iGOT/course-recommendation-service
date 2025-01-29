import random
from typing import Any, Dict, List
import requests
from vertexai.generative_models import ( FunctionDeclaration,Tool, GenerationResponse, Part)
from src.core.constants import DEFAULT_COURSES, TOTAL_SIMILAR_COURSE, MASTER_CONTENT_LIST, TOTAL_DOMAIN_COUURSE
from src.services.neural_searcher import NeuralSearcher
from src.core import config
from qdrant_client.http.models.models import Filter, FieldCondition, MatchText, MatchValue


retriever  = NeuralSearcher()

get_course_func = FunctionDeclaration(
    name="get_course_list",
    description="Determine the designated role for a user's training calendar for a specific course. Use this tool whenever you need to provide a recommended training schedule, such as when a customer requests, 'Suggest a training calendar for me. Or Suggest some course for me' Ensure to ask focused questions to gather necessary details.",
    parameters={
        "type": "object",
        "properties": {
            "designation": {
                "type": "string",
                "description": "The user's job designation or role within the organization.",
            },
            "department": {
                "type": "string",
                "description": "Name of Ministry, Department, or Organization withing goverment",
            }
        },
        "required": ["designation", "department"]
    }
)

get_designation_func = FunctionDeclaration(
    name="get_designation_list",
    description="Use this function to fetch list of designation to suggest the user based responsibilty or role. Use this function when the user is unsure about their specific designation.",
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query to retrieve designations related to the user's responsibilities from the vector database.",
            },
            "department": {
                "type": "string",
                "description": "Name of Ministry, Department, or Organization withing goverment",
            }
        },
        "required": ["query", "department"]   
    }
)

get_department_func = FunctionDeclaration(
    name="get_department_list",
    description="Use this function to fetch list of department to suggest the user based some informatiion. Use this function when the user is unsure about their specific name of Ministry, Department, or Organization withing goverment.",
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query to retrieve departments related to the user's information from the vector database.",
            }
        },
        "required": ["query"]   
    },
)

get_acronym_func = FunctionDeclaration(
    name="get_acronym_list",
    description="Fetch a list of designations based on the provided acronym. This function is useful for users who may be uncertain about the specific name of designation or role within the government.",
    parameters={
        "type": "object",
        "properties": {
            "acronym": {
                "type": "string",
                "description": "The acronym to search for",
            },
            "department": {
                "type": "string",
                "description": "Name of Ministry, Department, or Organization withing goverment",
            }
        },
        "required": ["acronym", "department"]   
    }
)

bot_insights_tool = Tool(
    function_declarations=[
        get_course_func, 
        get_designation_func, 
        get_department_func,
        get_acronym_func
    ]
)

def fetch_course(filter, query= None, limit = 15):
    url = f"{config.KB_BASE_URL}/apis/proxies/v8/sunbirdigot/search"
    headers = {
        "Content-Type": "application/json",
        "Cookie": config.KB_COOKIES,  # Replace with your actual cookie value
    }
    data = {
        "request": {
            "filters": filter,
            "query": query if query else "",
            # "sort_by": {
            #     "totalNoOfRating": "desc"
            # },
            "fields": [
                "name",
                "description",
                "competencies_v5",
                "contentType",
                "channel",
                "organisation",
                "duration",
                "objectType"
            ],
            "limit": limit
        }
    }
    response = requests.post(url, headers=headers, json=data)
    # Check for successful response
    if response.status_code == 200:
        # print("response ===>", response.text)
        # Process the JSON response
        data = response.json()
        return data
    else:
        print(f"Error: {response.text}")
        print(f"Error: {response.status_code}")

def extract_competency_theme_above_threshold(scored_points: List, threshold: float = 0.70) -> List[str]:
    competency_themes = []
    for scored_point in scored_points:
        if scored_point["score"] > threshold:
            competency_theme: str = scored_point['metadata']['competency_theme']
            competency_themes.extend(competency_theme.split(",") if competency_theme else [])
    return competency_themes

def extract_competency_theme_and_course_above_threshold(scored_points: List, threshold: float = 0.70) -> List[str]:
    competency_themes = []
    course_ids = []
    for scored_point in scored_points:
        if scored_point["score"] >= threshold:
            if 'competency_theme' in scored_point['metadata']:  
                competency_theme: str = scored_point['metadata']['competency_theme']
                competency_themes.extend(competency_theme.split(",") if competency_theme else [])
            
            if 'course_ids' in scored_point['metadata']:
                ids: str = scored_point['metadata']['course_ids']
                course_ids.extend(ids.split(",") if ids else [])
    return competency_themes, course_ids

def extract_course(scored_points: List) -> List[str]:
    course_ids = []
    for scored_point in scored_points:
        ids: str = scored_point['metadata']['course_ids']
        course_ids.extend(ids.split(",") if ids else [])
    return course_ids

def extract_course_above_threshold(scored_points: List, threshold: float = 0.70) -> List[str]:
    course_ids = []
    for scored_point in scored_points:
        if scored_point["score"] >= threshold:
            ids: str = scored_point['metadata']['course_ids']
            course_ids.extend(ids.split(",") if ids else [])
    return course_ids

def extract_sector_above_threshold(scored_points: List, threshold: float = 0.70) -> List[str]:
    sector_names = []
    for scored_point in scored_points:
        if scored_point["score"] >= threshold:
            sectors: str = scored_point['metadata']['sector_name']
            sector_names.extend(sectors.split(",") if sectors else [])
    return sector_names

def trim_data(data):
    return [item.strip() for item in data]

def get_unique_courses(courses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extracts unique courses from a list of course dictionaries, preserving order.

    Args:
        courses: A list of dictionaries, where each dictionary represents a course.

    Returns:
        A new list containing only the unique courses, preserving the original order.
        Returns an empty list if input is None or not a list.
    """

    if courses is None or not isinstance(courses, list):
        return []

    seen_identifiers = set()
    unique_courses = []

    for course in courses:
        if not isinstance(course, dict) or "identifier" not in course:
            continue  # Skip invalid course entries

        identifier = course["identifier"]
        if identifier not in seen_identifiers:
            seen_identifiers.add(identifier)
            unique_courses.append(course)

    return unique_courses

def prepare_markdown(data):
  """
  Prepares markdown format for a list of content dictionaries.

  Args:
      data: A list of dictionaries containing information about content.

  Returns:
      A string containing the markdown formatted data.
  """

  markdown_text = ""
  for index, item in enumerate(data):
    # Extract relevant information
    name = item["name"]
    identifier = item["identifier"]
    competencies = item["competencies_v5"]

    # Build the competency list
    competency_list =  set()
    for competency in competencies:
      competency_list.add(competency["competencyArea"])

    # Combine competencies with a comma separator
    competencies_string = ", ".join(list(competency_list))

    # Build the markdown link
    link = f"{KB_BASE_URL}/public/toc/{identifier}/overview"

    # Add the formatted line to markdown text
    markdown_text += f"{index + 1}. [{name}]({link}) - {competencies_string}\n"

  return markdown_text

def get_competenncies(data):
    competencies = []
    course_ids = []
    remaining_course = TOTAL_SIMILAR_COURSE
    department_filter = Filter(
                must=[FieldCondition(
                        key="metadata.department",
                        match=MatchText(text=data["department"])
                    )
                ])
    print("_______Relevant Course______")
    relevant_results = retriever.search(collection_name=config.QDRANT_RELEVANT_COLLECTION_NAME,text=data["designation"], filter_=department_filter)
    relevant_course_ids = extract_course_above_threshold(relevant_results, threshold=0.90)
    relevant_course_ids = trim_data(relevant_course_ids)
    print("Course IDs --->", relevant_course_ids)
    if relevant_course_ids and len(relevant_course_ids) >= TOTAL_SIMILAR_COURSE:
        return competencies, relevant_course_ids
    else:
        course_ids.extend(relevant_course_ids)
        
    print("______Exact search______")
    base_filter = Filter(
                must=[
                    FieldCondition(
                        key="metadata.department", # TO_DO: Key value need to be changed for hybrid search
                        match=MatchText(text=data["department"])
                    ),
                    FieldCondition(
                        key="page_content",
                        match=MatchValue(value=data["designation"]),
                    )
                ])
    results = retriever.search(collection_name=config.QDRANT_DESIGNATION_COLLECTION_NAME, filter_= base_filter, limit=1)
    if results:
        exact_course_ids = extract_course(results)
        exact_course_ids = trim_data(course_ids)
        print("Course IDs --->", exact_course_ids)
        course_ids.extend(exact_course_ids)
        remaining_course = 0 if len(course_ids) >= TOTAL_SIMILAR_COURSE else remaining_course - len(course_ids)

    if remaining_course:
        print("______Similar search within department______")
        results = retriever.search(collection_name=config.QDRANT_COMPETENCY_COLLECTION_NAME,text=data["designation"], filter_ = department_filter)
        competencies = extract_competency_theme_above_threshold(results)
        competencies = trim_data(competencies)
        print("competencies ---->", competencies)
        if competencies:
            return competencies, course_ids
        
        print("______Designation group search______")
        results = retriever.search(collection_name=config.QDRANT_GROUP_COLLECTION_NAME,text=data["designation"])
        competencies, group_course_ids = extract_competency_theme_and_course_above_threshold(results, threshold=0.65)
        competencies = trim_data(competencies)
        group_course_ids = trim_data(group_course_ids)
        course_ids.extend(group_course_ids)
        print("competencies ---->", competencies)
        print("Group Course IDs --->", group_course_ids)
        if competencies or group_course_ids:
            return competencies, course_ids

        print("______Cross search______")
        results = retriever.search(collection_name=config.QDRANT_COMPETENCY_COLLECTION_NAME,text=data["designation"])
        competencies = extract_competency_theme_above_threshold(results)
        competencies = trim_data(competencies)
        print("competencies ---->", competencies)
        if competencies:
            return competencies, course_ids
        
        # print("______Sector wises search______")
        # results = retriever.search(collection_name="designation_sector",text=data["designation"])
        # sector_course_ids = extract_course_above_threshold(results)
        # sector_course_ids = trim_data(sector_course_ids)
        # if sector_course_ids:
        #     course_ids.extend(sector_course_ids)
        #     return competencies, course_ids
        
        return competencies, course_ids
    else:
        return competencies, course_ids

def filter_courses_by_master_list(courses, master_content = MASTER_CONTENT_LIST):
    """
    Filters a list of courses, returning only those that exist in the master content list.

    Args:
        courses: A list of course identifiers (e.g., course IDs, course names).
        master_content: A list or set of master content identifiers.

    Returns:
        A list containing only the courses that are present in the master content.
        Returns an empty list if no courses are found in the master content.
    """

    # Use a set for faster lookups if master_content is a list
    if isinstance(master_content, list):
        master_content_set = set(master_content)
    else:
        master_content_set = master_content #Assume it's already a set or other efficient collection

    filtered_courses = [course for course in courses if course in master_content_set]
    return filtered_courses

def get_similar_courses(data: any):
    competencies, course_ids = get_competenncies(data)
    exact_courses = []
    courses = []
    if course_ids:
        # filter course by master list
        # filtered_courses = [course_id for course_id in course_ids if course_id in MASTER_CONTENT_LIST]
        filtered_courses = course_ids
        exact_courses = fetch_course(filter={"contentType": "Course","identifier": filtered_courses})
        exact_courses  = exact_courses['result']['content'] if exact_courses['result']['count'] > 0 else []
    
    print("Total exact course ===>", len(exact_courses))
    limit = TOTAL_SIMILAR_COURSE - len(exact_courses)
    
    print("Remaining limit ==>", limit)
    if competencies and limit > 0:
        print("Total Other course ==", limit)
        com_courses = fetch_course(filter={"contentType": "Course","competencies_v5.competencyTheme": competencies}, limit=limit)
        if "result" in com_courses and com_courses['result']['count'] > 0:
            random.shuffle(com_courses['result']['content'])
            # filter course by master list
            # courses = [course for course in com_courses['result']['content'] if course["identifier"] in MASTER_CONTENT_LIST]
            courses = com_courses['result']['content']
    return exact_courses + courses

def get_domain_specific_courses(data):
    print("______Domain wises search______")
    results = retriever.search(collection_name=config.QDRANT_DOMAIN_COLLECTION_NAME,text=data["department"], limit=2)
    course_ids = extract_course_above_threshold(results,  threshold=0.65)
    course_ids = trim_data(course_ids)
    print("=== Domain Courses ===>", course_ids)
    if course_ids:
       random.shuffle(course_ids)
       domain_course = fetch_course(filter={"contentType": "Course","identifier": course_ids[:TOTAL_DOMAIN_COUURSE]})
       domain_course  = domain_course['result']['content'] if domain_course['result']['count'] > 0 else []
    else:
        domain_course = []
    return domain_course

def get_sector_course(data):
    print("______Sector wises search______")
    department_filter = Filter(
                must=[FieldCondition(
                        key="metadata.department",
                        match=MatchText(text=data["department"])
                    )
                ])
    results = retriever.search(collection_name=config.QDRANT_SECTOR_COLLECTION_NAME, filter_=department_filter)
    sector_names = extract_sector_above_threshold(results,  threshold=0.0)
    sector_names = trim_data(sector_names)
    print("=== Sector Names ===>", sector_names)
    courses = []
    if sector_names:
        courses = fetch_course(filter={"contentType": "Course","sectorName": sector_names})
        courses = courses['result']['content'][:TOTAL_SIMILAR_COURSE] if courses['result']['count'] > 0 else []
    return courses


def fetch_course_list(data: any):
    domain_courses = get_domain_specific_courses(data)
    similar_courses = get_similar_courses(data)
    sector_courses = []
    if not similar_courses:
        sector_courses = get_sector_course(data)
    unique_contents = get_unique_courses(domain_courses + similar_courses + sector_courses + DEFAULT_COURSES)
    print(prepare_markdown(unique_contents))
    return prepare_markdown(unique_contents)
  
def fetch_desgination_list(data):
    filter = Filter(
                must=[
                    FieldCondition(
                        key="metadata.department",
                        match=MatchText(text=data["department"]),
                    )
                ])
    results: List = retriever.search(collection_name=config.QDRANT_ROLE_COLLECTION_NAME, text=data["query"], filter_=filter)
    designations = []
    for scored_point in results:
        if scored_point["score"] > 0.60:
            role: str = scored_point['metadata']['designation']
            designations.append(role)
    items = [item.strip() for item in designations]

    if len(designations) > 0:
        return items
    else:
        results: List = retriever.search(collection_name=config.QDRANT_ROLE_COLLECTION_NAME, text=data["query"])
        for scored_point in results:
            if scored_point["score"] > 0.60:
                role: str = scored_point['metadata']['designation']
                designations.append(role)
        items = [item.strip() for item in designations]
        return items

def fetch_acronnym_list(data):
    filter = Filter(
                must=[
                    FieldCondition(
                        key="metadata.department",
                        match=MatchText(text=data["department"]),
                    )
                ])
    results: List = retriever.search(collection_name=config.QDRANT_ACRONYM_COLLECTION_NAME, text=data["acronym"], filter_=filter)
    designations = []
    for scored_point in results:
        if scored_point["score"] > 0.60:
            role: str = scored_point['metadata']['designation']
            designations.append(role)
    items = [item.strip() for item in designations]
    if len(designations) > 0:
        return items
    else:
        results: List = retriever.search(collection_name=config.QDRANT_ACRONYM_COLLECTION_NAME, text=data["acronym"])
        for scored_point in results:
            if scored_point["score"] > 0.60:
                role: str = scored_point['metadata']['designation']
                designations.append(role)
        items = [item.strip() for item in designations]
        return items

def fetch_department_list(data):
    results: List = retriever.search(collection_name=config.QDRANT_DEPARTMENT_COLLECTION_NAME, text=data["query"])
    departments = []
    for scored_point in results:
        if scored_point["score"] > 0.60:
            department: str = scored_point['metadata']['name']
            departments.append(department)
    items = [item.strip() for item in departments]
    return items

function_handler = {            
    "get_course_list": fetch_course_list,
    "get_designation_list": fetch_desgination_list,
    "get_department_list": fetch_department_list,
    "get_acronym_list": fetch_acronnym_list
}


def extract_function_calls(response: GenerationResponse) -> list[dict]:
    function_calls: list[dict] = []
    if response.candidates[0].function_calls:
        for function_call in response.candidates[0].function_calls:
            function_call_dict: dict[str, dict[str, Any]] = {function_call.name: {}}
            for key, value in function_call.args.items():
                function_call_dict[function_call.name][key] = value
            function_calls.append(function_call_dict)
    return function_calls

def call_function(functions):      
    function_response: list[ "Part"] = []  # type: ignore
    # Loop over multiple function calls
    for function_call in functions:
        #  params = {key: value for key, value in function_call.args.items()}
        for function_name, function_args in function_call.items():
            print(function_args)
            function_response.append(Part.from_function_response(
                name=function_name,
                response={"content": function_handler[function_name](function_args)  },
            ))
    return function_response
    