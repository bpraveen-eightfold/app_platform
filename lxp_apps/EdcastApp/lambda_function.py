"""
    - Include all dependencies such as Python Standard Modules and open source libraries
"""
from __future__ import absolute_import

import json
import time
import traceback
from datetime import datetime
import requests
import jwt
import furl

CTA_LABEL = 'View in EdCast'


def error_response(error_str):
    """Error Response message"""
    data = {"error": error_str}
    print(json.dumps(data))
    return {"statusCode": 500, "body": json.dumps({"data": data})}


def str2bool(val):
    """Boolean string formatter"""
    return str(val).lower() in ("yes", "true", "t", "1")


def get_email(request_data, app_settings):
    """Get candidate/user email - employee_email, email, current_user_email"""
    use_test_email = str2bool(app_settings.get("use_test_email", False))
    edcast_test_email = app_settings.get("edcast_test_email", "")
    email = ""

    employee_email = request_data.get("employee_email", "")
    candidate_email = request_data.get("email", "")
    current_user_email = request_data.get("current_user_email", "")
    if (
        "employee_email" in request_data
        and employee_email != ""
        and employee_email is not None
    ):
        email = edcast_test_email if use_test_email else employee_email
    elif (
        "email" in request_data
        and candidate_email != ""
        and candidate_email is not None
    ):
        email = edcast_test_email if use_test_email else candidate_email
    elif (
        "current_user_email" in request_data
        and current_user_email != ""
        and current_user_email is not None
    ):
        email = edcast_test_email if use_test_email else current_user_email
    elif use_test_email:
        email = edcast_test_email
    print("email:", email)
    return email


def get_access_token(app_settings, token_baseurl, email):
    """Get Access token from Edcast with Client id & Client Secret using JWT encode"""
    start_time = time.perf_counter()
    client_api_key = app_settings.get("edcast_api_key")
    client_secret = app_settings.get("edcast_client_secret")

    payload = {"email": email}
    encoded = jwt.encode(payload, client_secret, algorithm="HS256")
    login_headers = {
        "X-API-KEY": client_api_key,
        "X-AUTH-TOKEN": encoded,
    }

    # getting token
    response = requests.get(token_baseurl + "/auth", headers=login_headers, data={})
    print(response, response.text)

    if response.status_code != 200:
        return error_response("Could not get the token.")

    token = response.json()["jwt_token"]

    end_time = time.perf_counter()
    print(f"Time taken for Access token: {end_time - start_time:0.4f} seconds")

    return token


def check_with_term(skills, term):
    """Comparing recommended course skills with term"""
    skill_matched = False
    for skill in skills:
        if skill["id"] == term:
            skill_matched = True
            break
    return skill_matched


def concate_skills(str, skills):
    """Comparing content course skills with candidate skills"""
    for skill in skills:
        if str != "":
            str = str + "," + skill.get("name")
        else:
            str = skill.get("name")
    return str


def subtract_common_skills(skills_set1, skills_set2):
    """Subtract common skills from required, skill_goals, position or project"""
    uncommon_skills = []
    final_list = list(
        set([s.get("name") for s in skills_set2])
        - set([s.get("name") for s in skills_set1])
    )
    for skill in final_list:
        uncommon_skills.append({"name": skill})

    if not uncommon_skills:
        uncommon_skills = skills_set2
    return uncommon_skills


def get_search_string(request_data, skill_function_name, str):
    """Get Filter query/Search Term skills query to fetch or match content course"""
    term = request_data.get("term")
    if term is not None and term != "":
        if skill_function_name.__name__ == "check_with_fq_skills":
            str = check_with_term(str, term)
        else:
            str = term
    elif "fq" in request_data:
        candidate_skills = request_data.get("fq")
        if candidate_skills is not None and candidate_skills != "":
            profile_skills = candidate_skills.get("profile_skills", [])
            if "position_skills" in candidate_skills:
                position_skills = candidate_skills.get("position_skills", [])
                uncommon_skills = subtract_common_skills(
                    profile_skills, position_skills
                )
                str = skill_function_name(str, uncommon_skills)
            elif "project_skills" in candidate_skills:
                project_skills = candidate_skills.get("project_skills", [])
                uncommon_skills = subtract_common_skills(profile_skills, project_skills)
                str = skill_function_name(str, uncommon_skills)
            elif "skill_goals" in candidate_skills:
                skill_goals = candidate_skills.get("skill_goals", [])
                uncommon_skills = subtract_common_skills(profile_skills, skill_goals)
                str = skill_function_name(str, uncommon_skills)
            elif "required_skills" in candidate_skills:
                required_skills = candidate_skills.get("required_skills", [])
                uncommon_skills = subtract_common_skills(
                    profile_skills, required_skills
                )
                str = skill_function_name(str, uncommon_skills)
            else:
                str = skill_function_name(str, profile_skills)
    elif "skills" in request_data:
        skills = request_data.get("skills")
        str = ",".join(skills)

    return str


def course_url_format(url):
    """Method to remove filter query param if empty"""
    f = furl.furl(url)
    f.remove(["q"])
    print(f.url)
    return f.url


def get_image_url(url):
    """Assign edcast logo if image url is empty or unavailable"""
    image_url = url
    if url is None or url == "":
        image_url = "https://integrations.edcast.com/assets/images/logo-icon.png"

    return image_url


def get_date(date):
    """Get date from datetime format"""
    date_formats = ["%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"]
    for date_format in date_formats:
        try:
            course_created_date_time = datetime.strptime(
                date.split(".")[0], "%Y-%m-%dT%H:%M:%S"
            )
            date = course_created_date_time.date().strftime("%d/%m/%Y")
            break
        except ValueError as e:
            print(e)
            pass
    return date


def get_course_list(baseurl, headers, email, language, request_data, offset, limit):
    """Get Content course list with filter query parameter"""
    start_time = time.perf_counter()
    course_list = []
    course_len = 0

    fetch_skill_start_time = time.perf_counter()
    filter_search_term = ""
    search_term = get_search_string(request_data, concate_skills, filter_search_term)
    fetch_skill_end_time = time.perf_counter()
    print(
        f"Time taken for fetching Search query skills: {fetch_skill_end_time - fetch_skill_start_time:0.4f} seconds"
    )

    # Check for Duplicates
    if search_term != "":
        search_words = search_term.split(",")
        filter_search_term = ",".join(sorted(set(search_words), key=search_words.index))

    print("Filter Search term:", filter_search_term)

    # get course api call with query
    url_params = (
        baseurl
        + "/cards/search?email="
        + email
        + "&q="
        + filter_search_term
        + "&offset="
        + str(offset)
        + "&limit="
        + str(limit)
    )

    # Check for filter query blank
    if filter_search_term == "":
        url_params = course_url_format(url_params)

    course_with_filter_response = requests.get(url_params, headers=headers, data={})
    course_list_response = course_with_filter_response

    if course_list_response.status_code != 200:
        print("Could not get courses")
    else:
        course_list_response_json = course_list_response.json()

        # Course List
        filter_course_list = course_list_response_json["cards"]
        for course in filter_course_list:
            if course["language"] == language:
                course_list.append(course)
        course_len = len(course_list)

        print("Content searched course count:", course_len)

    result = {"course_list": course_list, "course_len": course_len}
    end_time = time.perf_counter()
    print(
        f"Time taken for fetching content filter list: {end_time - start_time:0.4f} seconds"
    )
    return result


def get_course_list_inputs(request_data, app_settings, email):
    baseurl = app_settings.get("edcast_base_url")
    api_key = app_settings.get("edcast_api_key")
    token = get_access_token(app_settings, baseurl, email)

    headers = {
        "X-API-KEY": api_key,
        "X-ACCESS-TOKEN": token,
        "Content-Type": "application/json",
    }
    language = app_settings.get("language", "en")

    limit = request_data.get("limit", 0)
    if limit is None or limit == "None":
        limit = 0

    offset = request_data.get("start", 0)
    if offset is None or offset == "None":
        offset = 0

    get_cards_listings = get_course_list(
        baseurl, headers, email, language, request_data, offset, limit
    )
    result = {
        "course_list": get_cards_listings.get("course_list"),
        "course_len": get_cards_listings.get("course_len"),
        "limit": limit,
        "offset": offset,
    }

    return result


def careerhub_entity_search_results_handler(event, context):
    trigger_start_time = time.perf_counter()
    request_data = event.get("request_data", {})
    app_settings = event.get("app_settings", {})
    email = get_email(request_data, app_settings)

    course_list_data = []
    get_card_list = get_course_list_inputs(request_data, app_settings, email)

    if get_card_list is not None:
        for course in get_card_list["course_list"]:
            if course != "":
                course_id = course.get("id", "")
                course_attr = course.get("resource")
                course_title = course_attr.get("title", "")
                course_desc = course_attr.get("description", "")
                image_url = get_image_url(course_attr.get("imageUrl", ""))
                card_label = course_attr.get("type", "")
                cta_label = CTA_LABEL
                course_url = course.get("shareUrl", "")
                provider = course.get("provider", "")
                course_duration = course.get("duration", "")
                course_published_at = get_date(course.get("publishedAt", ""))
                item = {
                    "entity_id": course_id,
                    "title": course_title,
                    "subtitle": "",
                    "description": course_desc,
                    "custom_fields": "",
                    "last_modified_ts": "",
                    "image_url": image_url,
                    "cta_url": course_url,
                    "source_name": provider,
                    "fields": [
                        {
                            "name": "Provider",
                            "value": provider,
                        },
                        {
                            "Name": "Durations Hours",
                            "Value": course_duration,
                        },
                        {
                            "name": "Content Type",
                            "value": course_attr.get("content-type", "Course"),
                        },
                        {"name": "Language", "value": course_attr.get("language", "")},
                        {"name": "Published Date", "value": course_published_at},
                    ],
                    "cta_label": cta_label,
                    "card_label": card_label,
                    "tags": "",
                    "metadata": "",
                }

                course_list_data.append(item)

    data = {
        "entities": course_list_data,
        "num_results": get_card_list.get("course_len"),
        "limit": get_card_list.get("limit"),
        "offset": get_card_list.get("offset"),
        "cursor": "",
    }

    print(data)

    trigger_end_time = time.perf_counter()
    print(
        f"Time taken for search entity results trigger: {trigger_end_time - trigger_start_time:0.4f} seconds"
    )

    return {"statusCode": 200, "body": json.dumps({"data": data})}


def career_planner_recommended_courses_handler(event, context):
    trigger_start_time = time.perf_counter()
    request_data = event.get("request_data", {})
    app_settings = event.get("app_settings", {})
    email = get_email(request_data, app_settings)

    data = []
    get_card_list = get_course_list_inputs(request_data, app_settings, email)

    if get_card_list is not None:
        for course in get_card_list["course_list"]:
            if course != "":
                course_id = course.get("id", "")
                course_attr = course.get("resource")
                course_title = course_attr.get("title", "")
                course_desc = course_attr.get("description", "")
                image_url = get_image_url(course_attr.get("imageUrl", ""))
                card_label = course_attr.get("type", "")
                course_url = course.get("shareUrl", "")
                provider = course.get("provider", "")
                course_duration = course.get("duration", "")
                course_published_at = get_date(course.get("publishedAt", ""))
                language = course.get("language", "")
                item = {
                    "status": "",
                    "category": "",
                    "group_id": "",
                    "description": course_desc,
                    "language": language,
                    "title": course_title,
                    "skills": "",
                    "published_date": course_published_at,
                    "lms_course_id": course_id,
                    "lms_data": "",
                    "course_type": card_label,
                    "image_url": image_url,
                    "provider": provider,
                    "difficulty": "",
                    "course_url": course_url,
                    "duration_hours": course_duration,
                }

                data.append(item)

    # print(data)

    trigger_end_time = time.perf_counter()
    print(
        f"Time taken for search entity results trigger: {trigger_end_time - trigger_start_time:0.4f} seconds"
    )
    return {"statusCode": 200, "body": json.dumps({"data": data})}


def careerhub_get_entity_details_handler(event, context):
    """Careerhub get Entity Course details"""
    trigger_start_time = time.perf_counter()
    request_data = event.get("request_data", {})
    app_settings = event.get("app_settings", {})

    baseurl = app_settings.get("edcast_base_url")
    api_key = app_settings.get("edcast_api_key")
    email = get_email(request_data, app_settings)
    token = get_access_token(app_settings, baseurl, email)

    headers = {
        "X-API-KEY": api_key,
        "X-ACCESS-TOKEN": token,
        "Content-Type": "application/json",
    }

    entity_id = request_data.get("entity_id", 0)
    if entity_id is None or entity_id == "None":
        return error_response("Entity id cannot be blank")

    # getting course details
    course_details_response = requests.get(
        baseurl + "/cards/" + str(entity_id), headers=headers, data={}
    )

    if course_details_response.status_code != 200:
        return error_response("Could not get course detail.")

    course_details_response_json = course_details_response.json()

    course_json = course_details_response_json.get("card")
    edcastUrl = course_json.get("shareUrl", "")
    provider = course_json.get("provider", "")
    author_details = course_json.get("author", "")
    author = (
        author_details.get("fullName", "")
        if author_details and author_details is not None
        else ""
    )
    course_created_at = get_date(course_json.get("createdAt", ""))
    course_published_at = get_date(course_json.get("publishedAt", ""))
    course_attr = course_json.get("resource", [])
    course_attr_status = course_attr != [] and course_attr is not None
    image_url = (
        get_image_url(course_attr.get("imageUrl", ""))
        if course_attr_status
        else get_image_url("")
    )
    card_label = course_attr.get("type", "Course") if course_attr_status else "Course"
    description = course_attr.get("description", "") if course_attr_status else ""
    title = course_attr.get("title", "") if course_attr_status else ""
    content_type = course_attr.get("type", "Course") if course_attr_status else "Course"
    entity_detail = {
        "entity_id": course_json.get("id"),
        "cta_label": CTA_LABEL,
        "card_label": card_label,
        "cta_url": edcastUrl,
        "custom_sections": [],
        "description": description,
        "fields": [
            {"name": "Provider", "value": provider},
            {"name": "Duration Hours", "value": course_json.get("duration", "")},
            {
                "name": "Content Type",
                "value": content_type,
            },
            {"name": "Language", "value": course_json.get("language", "")},
            {"name": "Author", "value": author},
            {"name": "Created Date", "value": course_created_at},
            {"name": "Published Date", "value": course_published_at},
        ],
        "image_url": image_url,
        "last_modified_ts": "",
        "metadata": [],
        "source_name": provider,
        "subtitle": "",
        "tags": "",
        "title": title,
    }

    data = entity_detail

    trigger_end_time = time.perf_counter()
    print(
        f"Time taken for search entity results trigger: {trigger_end_time - trigger_start_time:0.4f} seconds"
    )

    print(data)

    return {"statusCode": 200, "body": json.dumps({"data": data})}


def app_handler(event, context):
    request_data = event.get("request_data", {})
    trigger_name = request_data.get("trigger_name")
    print("Trigger Name: ", trigger_name)
    print("event: ", event)

    try:
        if trigger_name == "careerhub_entity_search_results":
            return careerhub_entity_search_results_handler(event, context)
        elif trigger_name == "careerhub_get_entity_details":
            return careerhub_get_entity_details_handler(event, context)
        elif trigger_name == "career_planner_recommended_courses":
            return career_planner_recommended_courses_handler(event, context)
        else:
            return error_response("Unknown trigger.")

    except Exception as e:
        data = {}
        error_str = "Something went wrong, traceback: {}".format(traceback.format_exc())
        print(error_str)
        data = {"error": repr(e), "stacktrace": traceback.format_exc()}
        return {"statusCode": 500, "body": json.dumps({"data": data})}
