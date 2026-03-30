"""
    - Include all dependencies such as Python Standard Modules and open source libraries
"""
from __future__ import absolute_import

import json
import time
import traceback
import concurrent.futures
from datetime import datetime
from datetime import timezone
from urllib.parse import urlencode
import requests
import furl
from jsonpath_ng import parse

CTA_LABEL = 'View in Degreed'


def error_response(error_str):
    """Error Response message"""
    error = {"error": error_str}
    print(json.dumps(error))
    
    # Extract status code from error string if present
    status_code = 500  # Default status code
    if "Status code: 401" in error_str:
        status_code = 401
    elif "Status code: 403" in error_str:
        status_code = 403
    
    return {
        "statusCode": status_code,
        "body": json.dumps(error)
    }


def str2bool(val):
    """Boolean string formatter"""
    return str(val).lower() in ("yes", "true", "t", "1")


def get_access_token(app_settings, token_baseurl):
    """Get Access token from Degreed with Client id & Client Secret"""
    client_id = app_settings.get("degreed_client_id")
    client_secret = app_settings.get("degreed_client_secret")

    payload = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "users:read,content:read",
    }
    login_headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": app_settings.get("user_agent", "Mozilla/5.0")
    }

    # getting token
    response = requests.post(
        token_baseurl + "/oauth/token", headers=login_headers, data=payload
    )

    if response.status_code != 200:
        return error_response(f'Request failed. Status code: {response.status_code}. Reason: {response.reason}.')

    token = response.json()["access_token"]
    return token


def check_with_term(skills, term):
    """Comparing recommended course skills with term"""
    skill_matched = False
    for skill in skills:
        if skill["id"] == term:
            skill_matched = True
            break
    return skill_matched


def check_with_fq_skills(skills, fq_skills):
    """Comparing recommended course skills with filtered candidate skills"""
    skill_matched = False
    for skill in skills:
        for pskill in fq_skills:
            if pskill.get("name") in skill.get("id").split(";"):
                skill_matched = True
                break
        if skill_matched:
            break
    return skill_matched


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


def concate_skills(str, skills):
    """Comparing content course skills with candidate skills"""
    for skill in skills:
        if str != "":
            str = str + "," + skill.get("name")
        else:
            str = skill.get("name")
    return str


def get_search_string(request_data, skill_function_name, str):
    """Get Filter query/Search Term skills query to fetch or match recommended & content course"""
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
    f.remove(["filter[term]"])
    print(f.url)
    return f.url


def get_recommend_skills(baseurl, headers, course):
    """Fetching Skills of recommended course with API call"""
    course_id = course["included"][0]["id"]
    ans = requests.get(
        baseurl + "/api/v2/content/" + course_id + "/skills", headers=headers
    )
    course["skills_status_code"] = ans.status_code
    if ans.status_code != 200:
        print(f'Could not find skills for id {course_id}. Status code: {ans.status_code}. Reason: {ans.reason}.')
    else:
        skills_json = ans.json()
        course["skills"] = skills_json["data"]
    return course


# There was previously course filtering based on matching skill on homepage but not marketplace page,
# removed the logic so the results are consistent, this means the fetched course skills are not being used now.
def recommend_concurrent_loop(baseurl, headers, recommended_num, recommended_courses):
    """Optimization: Using ThreadPool method to fetch skills using API call for recommended course loop"""
    matching_start_time = time.perf_counter()
    modified_course = []
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=int(recommended_num)
    ) as executor:
        futures = [
            executor.submit(get_recommend_skills, baseurl, headers, course)
            for course in recommended_courses
        ]
    for future in concurrent.futures.as_completed(futures):
        course = future.result()
        modified_course.append(course)
    matching_end_time = time.perf_counter()
    print(
        f"Time taken for fetching course skills concurrent: {matching_end_time - matching_start_time:0.4f} seconds"
    )
    return modified_course

def course_language_matches_setting(course_language, settings_language):
    # Check if the course_language prefix matches the settings_language
    # For example, if settings_language is 'en', then course_language 'en' and 'en-US' will match
    course_language = course_language or ''
    return course_language.startswith(settings_language)

def matching_schema(baseurl, headers, course, language):
    """API call for getting detailed content schema"""
    recomm_course_list = ""
    recommended_course_id = course["included"][0]["id"]
    recommended_course_details_response = requests.get(
        baseurl + "/api/v2/content/" + str(recommended_course_id), headers=headers
    )

    if recommended_course_details_response.status_code != 200:
        print(f'Could not get recommended required learning details for course {recommended_course_id}. \
                Status code: {recommended_course_details_response.status_code}. \
                Reason: {recommended_course_details_response.reason}.')
    else:
        recomm_course_details_response_json = recommended_course_details_response.json()
        recomm_course_details_item = recomm_course_details_response_json["data"]
        if course_language_matches_setting(recomm_course_details_item.get("attributes")["language"], language):
            recomm_course_list = recomm_course_details_item
    return recomm_course_list


def matching_schema_concurrent_loop(
    baseurl, headers, language, filtered_matched_course_list, recommended_num
):
    """Optimization: Using ThreadPool method for getting detailed schema"""
    matching_schema_start_time = time.perf_counter()
    matched_course_list = []
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=int(recommended_num)
    ) as executor:
        futures = [
            executor.submit(matching_schema, baseurl, headers, course, language)
            for course in filtered_matched_course_list
        ]
    for future in concurrent.futures.as_completed(futures):
        course = future.result()
        if course and course not in matched_course_list:
            matched_course_list.append(course)
    matching_schema_end_time = time.perf_counter()
    print(
        f"Time taken for fetching course details schema concurrent: {matching_schema_end_time - matching_schema_start_time:0.4f} seconds"
    )
    return matched_course_list

def filter_recommended_courses(courses, recommended_num):
    """
    Filter out courses with status: "Complete" from required learning api
    to address customer issue.

    Args:
        courses: array of objects under data key of /api/v2/required-learning api
            For an example value, see tests/fake_data/recommended_course.py
        recommended_num (int): Max number of courses to return
    """
    filtered_courses = []
    for course in courses:
        if len(filtered_courses) == recommended_num:
            break
        if course.get('attributes', {}).get('status') != 'Complete':
            filtered_courses.append(course)
    return filtered_courses

def recommended_course_list(
    baseurl, candidate_id, headers, language, request_data, app_settings
):
    """Get Recommended course list"""
    # recommended courses
    start_time = time.perf_counter()
    trigger_source = request_data.get("trigger_source", "")
    recommended_num = int(app_settings.get("recommended_course_limit", 5))
    recommended_endpoint = "/recommended-learning" if app_settings.get("use_recommended_learning_endpoint", False) else "/required-learning"
    recommended_response = requests.get(
        baseurl + "/api/v2/users/" + candidate_id + recommended_endpoint,
        headers=headers,
    )
    # print("Required Learning: ", recommended_response.json())
    if recommended_response.status_code != 200:
        return error_response('Could not get recommended courses. Status code: ' +
                              f'{recommended_response.status_code}. Reason: ' +
                              f'{recommended_response.reason}.')
    recommended_response_json = recommended_response.json()
    recommended_courses = filter_recommended_courses(recommended_response_json["data"], recommended_num)

    filtered_matched_course_list = []
    matched_course_list = []
    # print(recommended_courses)
    if recommended_courses:
        # Removed logic to filter only courses that match EF skills to make homepage and marketplace consistent
        filtered_matched_course_list = recommended_courses

        matched_course_list = matching_schema_concurrent_loop(
            baseurl, headers, language, filtered_matched_course_list, recommended_num
        )

    # print(len(matched_course_list), 'matched_course_list: ', matched_course_list)
    result = {
        "course_list": matched_course_list,
        "course_len": len(matched_course_list),
        "function_name": "recommended_course_list",
    }
    end_time = time.perf_counter()
    print(
        f"Time taken for fetching recommended list: {end_time - start_time:0.4f} seconds"
    )
    return result


def get_search_course_list(baseurl, headers, language, request_data, candidate_id, app_settings):
    """Get Content course list with filter query parameter"""
    # getting search courses
    start_time = time.perf_counter()
    course_list = []
    course_len = 0
    captured_value = ""

    # if course_count < 10:
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

    # remove character from search term
    if len(filter_search_term) > 255:
        filter_search_term = filter_search_term[:255]

    print("Search Term:", filter_search_term)

    # get course api call with filter query
    params = {}
    # Check for filter query blank
    if filter_search_term:
        params["filter[term]"] = filter_search_term
    # filter[internal_only] defaults to True in Degreed API, set to false for override
    if app_settings.get("not_internal_only", False):
        params["filter[internal_only]"] = "false"
    # filter[include_restricted] defaults to False in Degreed API, set to true for override
    if app_settings.get("include_restricted", False):
        params["filter[include_restricted]"] = "true"

    url_without_nextBatch = f'{baseurl}api/v2/content'

    course_with_filter_response = requests.get(url_without_nextBatch, params=params, headers=headers)
    course_list_response = course_with_filter_response

    if course_list_response.status_code != 200:
        print(f'Could not get courses. Status code: \
                {course_list_response.status_code}. Reason: \
                {course_list_response.reason}.')
        course_len = 0
    else:
        course_list_response_json = course_list_response.json()

        # Course List
        # If this search is for recommended skill courses (search term is empty and we're using fq skill term),
        # filter out completed courses
        should_filter_completed_courses = not bool(request_data.get("term"))
        completed_course_ids = []
        if should_filter_completed_courses:
            request_url = f"/api/v2/users/{candidate_id}/completions?limit=1000"
            print(f"Fetching completed courses for filtering using url {request_url}")
            course_attendance_response = requests.get(
                baseurl + request_url,
                headers=headers,
            )
            if course_attendance_response.status_code != 200:
                print(f"Failed fetching completed courses for filtering. Status code: " +
                    f"{course_attendance_response.status_code}. Reason: " +
                    f"{course_attendance_response.reason}."
                )
            else:
                course_attendance_response_json = course_attendance_response.json()
                course_attendance_list = course_attendance_response_json["data"]
                for course_attendance in course_attendance_list:
                    course_id = course_attendance["included"][0]["id"]
                    completed_course_ids.append(course_id)
            print(f"Fetched completed course ids (first 100): {', '.join(completed_course_ids[:100])}")
        filter_course_list = course_list_response_json["data"]
        for course in filter_course_list:
            include_course = True
            if not course_language_matches_setting(course["attributes"]["language"], language):
                include_course = False
            if course["id"] in completed_course_ids:
                include_course = False
            if include_course:
                course_list.append(course)
        course_len = len(course_list)

        print("Content searched course count:", course_len)

    result = {
        "course_list": course_list,
        "course_len": course_len,
        "function_name": "get_search_course_list",
        "cursor": captured_value,
    }
    # print(json.dumps(course_list, indent=4))
    end_time = time.perf_counter()
    print(
        f"Time taken for fetching content filter list: {end_time - start_time:0.4f} seconds"
    )
    return result


def get_user_id(email, baseurl, request_headers):
    """Get Degreed candidate id using email as a identifier"""
    user_id = ""
    if email != "" and email is not None:
        candidate_response = requests.get(
            baseurl + "api/v2/users/" + email + "?identifier=email",
            headers=request_headers,
        )
        if candidate_response.status_code != 200:
            print(f'Could not find the user. Status code: {candidate_response.status_code}. \
                    Reason: {candidate_response.reason}.')
        else:
            candidate_response_json = candidate_response.json()
            # print(candidate_response_json)
            user_id = candidate_response_json["data"]["id"]

    return user_id


def time_epoch(epoch):
    """Convert datetime format to time epoch"""
    if not epoch:
        return None
    date_formats = ['%Y-%m-%dT%H:%M:%S.%f', '%Y-%m-%dT%H:%M:%S']
    for date_format in date_formats:
        try:
            report_completion_date_time = datetime.strptime(
                epoch.split(".")[0], "%Y-%m-%dT%H:%M:%S"
            )
            epoch = int(report_completion_date_time.replace(tzinfo=timezone.utc).timestamp())
            break
        except ValueError as e:
            print(e)
            pass
    return epoch


def get_date(date):
    """Get date from datetime format"""
    date_formats = ['%Y-%m-%dT%H:%M:%S.%f', '%Y-%m-%dT%H:%M:%S']
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


def get_duration(duration_type, duration):
    """Convert duration of the course in hours - duration types available seconds, minutes, words"""
    if duration_type is None or duration_type == "":
        course_duration = "NA"
    elif duration_type.lower() == "seconds":
        course_duration = round(((duration / 60) / 60), 2)
    elif duration_type.lower() == "minutes":
        course_duration = round(duration / 60, 2)
    elif duration_type.lower() == "words":
        course_duration = round((duration / 250) / 60, 2)
    else:
        course_duration = duration
    return course_duration


def get_image_url(url, app_settings):
    """Assign degreed logo if image url is empty or unavailable"""
    image_url = url

    if app_settings.get("skip_all_images", False):
        return app_settings.get("default_image_url") or ""

    default_image = app_settings.get("default_image_url") or \
        "https://blog.degreed.com/wp-content/themes/degreed-blog/assets/img/new-logo.svg"
    if url is None or url == "":
        image_url = default_image
    elif url.startswith("~"):
        image_url = "https://prod.degreedcdn.com" + url[1:]
    return image_url


def get_email(request_data, app_settings):
    """Get candidate/user email - employee_email, email, current_user_email"""
    use_test_email = str2bool(app_settings.get("use_test_email", False))
    degreed_test_email = app_settings.get("degreed_test_email", "")
    email = ""

    employee_email = request_data.get("employee_email", "")
    candidate_email = request_data.get("email", "")
    current_user_email = request_data.get("current_user_email", "")
    if (
        "employee_email" in request_data
        and employee_email != ""
        and employee_email is not None
    ):
        email = degreed_test_email if use_test_email else employee_email
    elif (
        "email" in request_data
        and candidate_email != ""
        and candidate_email is not None
    ):
        email = degreed_test_email if use_test_email else candidate_email
    elif (
        "current_user_email" in request_data
        and current_user_email != ""
        and current_user_email is not None
    ):
        email = degreed_test_email if use_test_email else current_user_email
    elif use_test_email:
        email = degreed_test_email
    print("email:", email)
    return email


def recommendation_trigger_limitations(request_data):
    """Recommendation function calling conditions - Function for adding limitations to recommended course"""
    term = request_data.get("term", "")
    next_batch = request_data.get("cursor")
    trigger_source = request_data.get("trigger_source", "")

    if (
        (term is not None and term != "")
        or trigger_source == "ch_jobs"
        or trigger_source == "ch_projects"
        or (next_batch is not None and next_batch != "")
    ):
        return False
    else:
        return True


def get_combined_concurrent(
    request_data, app_settings, baseurl, candidate_id, request_headers, language
):
    """Optimization: Using ThreadPool method for getting combined courses - Recommendation & content course lists"""
    recomm_list = []
    con_list = []
    recomm_course_len = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        print("Parallel ThreadPool start")
        futures = []
        if recommendation_trigger_limitations(request_data):
            futures.append(
                executor.submit(
                    recommended_course_list,
                    baseurl,
                    candidate_id,
                    request_headers,
                    language,
                    request_data,
                    app_settings,
                )
            )
        futures.append(
            executor.submit(
                get_search_course_list, baseurl, request_headers, language, request_data, candidate_id, app_settings
            )
        )
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            function_name = result.get("function_name")

            if recommendation_trigger_limitations(request_data):
                if function_name == "recommended_course_list":
                    index = 0
                    for item in result.get("course_list"):
                        recomm_list.insert(index, item)
                        index = index + 1
                        recomm_course_len = result.get("course_len")

            if function_name == "get_search_course_list":
                course_con_len = result.get("course_len")
                # cursor = result.get('cursor', '')
                for item in result.get("course_list"):
                    con_list.append(item)

        print("Parallel ThreadPool end")

    result = {
        "recomm_list": recomm_list,
        "con_list": con_list,
        "recomm_course_len": recomm_course_len,
        "course_con_len": course_con_len,
    }

    return result


def recommended_course_cursor_list(
    recomm_course_len, endlimit, course_limit, offset, next_batch, recomm_list, con_list
):
    """Course list start & end limit in array function"""
    if recomm_course_len >= endlimit:
        recommended_course = recomm_list[offset:endlimit]
    else:
        con_limit = endlimit - recomm_course_len
        if recomm_course_len >= offset:
            recomm_limit = recomm_course_len - offset
            if recomm_limit == 0 or recomm_course_len == 0:
                con_list_num = offset - int(0 if next_batch is None else next_batch)
                recommended_course = con_list[
                    con_list_num: (con_list_num + course_limit)
                ]
            else:
                recommended_course = recomm_list[-recomm_limit:] + con_list[:con_limit]
            next_batch = recomm_course_len
        else:
            con_list_num = offset - int(0 if next_batch is None else next_batch)
            recommended_course = con_list[con_list_num: (con_list_num + course_limit)]

    result = {"recommended_course": recommended_course, "next_batch": next_batch}
    return result


def get_combined_courses(request_data, app_settings):
    """Get combined course lists"""
    email = get_email(request_data, app_settings)

    degreed_base_url = app_settings.get("degreed_base_url")
    baseurl = "https://api." + degreed_base_url + "/"
    language = app_settings.get("language", "en")
    # get token
    token_url = "https://" + degreed_base_url
    token = get_access_token(app_settings, token_url)
    request_headers = {"Authorization": "Bearer " + str(token)}

    # candidate id
    candidate_id = ""
    start_time = time.perf_counter()
    if email != "":
        candidate_id = get_user_id(email, baseurl, request_headers)
    print("Candidate Id:", candidate_id)
    end_time = time.perf_counter()
    print(f"Time taken for fetching Candidate id: {end_time - start_time:0.4f} seconds")

    next_batch = request_data.get("cursor")

    course_limit = request_data.get("limit", 0)
    if course_limit is None or course_limit == "None":
        course_limit = 0

    offset = request_data.get("start", 0)
    if offset is None or offset == "None":
        offset = 0

    endlimit = offset + course_limit

    if candidate_id == "" or candidate_id is None:
        return error_response("Could not get the courses")
    else:
        recommended_course = []
        get_combined_list = get_combined_concurrent(
            request_data, app_settings, baseurl, candidate_id, request_headers, language
        )
        recomm_course_len = get_combined_list.get("recomm_course_len")
        course_con_len = get_combined_list.get("course_con_len")
        recomm_list = get_combined_list.get("recomm_list")
        con_list = get_combined_list.get("con_list")

        print("Recommended course count:", recomm_course_len)
        
        if app_settings.get('course_filter',False):
            hris_employee_api_field = app_settings.get('additional_filter').get('hris_employee_api_field')
            hris_employee_api_field_value = app_settings.get('additional_filter').get('hris_employee_api_field_value')
            degreed_api_field = app_settings.get('additional_filter').get('degreed_api_field')
            degreed_api_field_value = app_settings.get('additional_filter').get('degreed_api_field_value')
            action = app_settings.get('additional_filter').get('action') # include_only, exclude

            current_email = request_data.get("current_user_email", "")

            filter_identifier = get_hris_employee_by_email(app_settings,hris_employee_api_field,current_email)
            
            if filter_identifier and filter_identifier in hris_employee_api_field_value:

                if action == "exclude":

                    if recomm_course_len > 0:
                        json_data = recomm_list
                        filtered_recomm_list = list(filter(lambda item: item["attributes"][degreed_api_field] not in degreed_api_field_value, json_data))
                        get_combined_list["recomm_list"] = filtered_recomm_list
                        get_combined_list["recomm_course_len"] = len(filtered_recomm_list)
                        recomm_course_len = get_combined_list.get("recomm_course_len")
                        recomm_list = get_combined_list.get("recomm_list")
                        print("Filtered Recommended course count:", recomm_course_len)

                    if course_con_len > 0:
                        json_data = con_list
                        filtered_con_list = list(filter(lambda item: item["attributes"][degreed_api_field] not in degreed_api_field_value, json_data))
                        get_combined_list["con_list"] = filtered_con_list
                        get_combined_list["course_con_len"] = len(filtered_con_list)
                        course_con_len = get_combined_list.get("course_con_len")
                        con_list = get_combined_list.get("con_list")
                        print("Filtered Content searched course count:", course_con_len)

                if action == "include_only":

                    if recomm_course_len > 0:
                        json_data = recomm_list
                        filtered_recomm_list = list(filter(lambda item: item["attributes"][degreed_api_field] in degreed_api_field_value, json_data))
                        get_combined_list["recomm_list"] = filtered_recomm_list
                        get_combined_list["recomm_course_len"] = len(filtered_recomm_list)
                        recomm_course_len = get_combined_list.get("recomm_course_len")
                        recomm_list = get_combined_list.get("recomm_list")
                        print("Filtered Recommended course count:", recomm_course_len)

                    if course_con_len > 0:
                        json_data = con_list
                        filtered_con_list = list(filter(lambda item: item["attributes"][degreed_api_field] in degreed_api_field_value, json_data))
                        get_combined_list["con_list"] = filtered_con_list
                        get_combined_list["course_con_len"] = len(filtered_con_list)
                        course_con_len = get_combined_list.get("course_con_len")
                        con_list = get_combined_list.get("con_list")
                        print("Filtered Content searched course count:", course_con_len)

        recommended_list_cursor = recommended_course_cursor_list(
            recomm_course_len,
            endlimit,
            course_limit,
            offset,
            next_batch,
            recomm_list,
            con_list,
        )

        recommended_course = recommended_list_cursor.get("recommended_course")
        next_batch = recommended_list_cursor.get("next_batch")

        # print('recommended_course', recommended_course)
        result = {
            "offset": offset,
            "endlimit": endlimit,
            "course_limit": course_limit,
            "recommended_course_list": recommended_course,
            "recomm_len": recomm_course_len,
            "content_len": course_con_len,
            "next_batch": next_batch,
        }

        return result


def careerhub_entity_search_results_handler(event, context):
    """Careerhub Entity Search Results handler"""
    start_handler_time = time.perf_counter()
    request_data = event.get("request_data", {})
    app_settings = event.get("app_settings", {})

    course_list_start_time = time.perf_counter()
    course_list_data = []
    get_combined_course = get_combined_courses(request_data, app_settings)
    # if get_combined_course.get('statusCode') == 500:
    #     return get_combined_course
    # else:
    recommended_course = get_combined_course.get("recommended_course_list")
    if recommended_course is not None:
        for course in recommended_course:
            if course != "":
                course_attr = course.get("attributes", "")
                course_id = course.get("id", "")
                course_title = course_attr.get("title", "")
                course_desc = course_attr.get("summary", "")
                degreed_url = course_attr.get("degreed-url", "")
                card_label = course_attr.get("content-type", "Course")
                cta_label = CTA_LABEL
                image_url = get_image_url(course_attr.get("image-url", ""), app_settings)
                course_modified_at = time_epoch(course_attr.get("modified-at", ""))
                course_created_at = get_date(course_attr.get("created-at", ""))
                provider = course_attr.get("provider", "")
                if provider is None and course_attr.get("is-internal") is True:
                    provider = "Internal"
                course_duration = get_duration(
                    course_attr.get("duration-type"), course_attr.get("duration")
                )

                item = {
                    "entity_id": course_id,
                    "title": course_title,
                    "subtitle": "",
                    "description": course_desc,
                    "custom_fields": "",
                    "last_modified_ts": course_modified_at,
                    "image_url": image_url,
                    "cta_url": degreed_url,
                    "source_name": provider,
                    "fields": [
                        {
                            "name": "Provider",
                            "value": provider,
                        },
                        {
                            "name": "Durations Hours",
                            "value": course_duration,
                        },
                        {
                            "name": "Content Type",
                            "value": course_attr.get("content-type", "Course"),
                        },
                        {"name": "Language", "value": course_attr.get("language", "")},
                        {"name": "Owner", "value": course_attr.get("owner", "")},
                        {"name": "Published Date", "value": course_created_at},
                    ],
                    "card_label": card_label,
                    "cta_label": cta_label,
                    "tags": [],
                    "metadata": [],
                }

                course_list_data.append(item)

    content_len = get_combined_course.get("content_len", 0)
    recomm_len = get_combined_course.get("recomm_len", 0)
    course_list_len = int(content_len) + int(recomm_len)

    print("Cursor:", get_combined_course.get("next_batch"))

    data = {
        "entities": course_list_data,
        "num_results": course_list_len,
        "limit": get_combined_course.get("course_limit"),
        "offset": get_combined_course.get("offset"),
        "cursor": get_combined_course.get("next_batch"),
    }

    course_list_end_time = time.perf_counter()
    print(
        f"Time taken for fetching Courses: {course_list_end_time - course_list_start_time:0.4f} seconds"
    )

    # print(data)

    end_handler_time = time.perf_counter()
    print(
        f"Time taken for fetching Handler: {end_handler_time - start_handler_time:0.4f} seconds"
    )

    return {"statusCode": 200, "body": json.dumps({"data": data})}


def careerhub_homepage_recommended_courses_handler(event, context):
    """Careerhub Homepage Recommended Courses handler used in career planner tab"""
    start_handler_time = time.perf_counter()
    request_data = event.get("request_data", {})
    app_settings = event.get("app_settings", {})
    course_list_start_time = time.perf_counter()
    data = []
    get_combined_course = get_combined_courses(request_data, app_settings)
    recommended_course = get_combined_course.get("recommended_course_list")

    # print(recommended_course)
    if recommended_course is not None:
        for course in recommended_course:
            if course != "":
                course_attr = course.get("attributes")
                course_id = course.get("id", "")
                course_title = course_attr.get("title", "")
                course_desc = course_attr.get("summary", "")
                degreed_url = course_attr.get("degreed-url", "")
                card_label = course_attr.get("content-type")
                image_url = get_image_url(course_attr.get("image-url", ""), app_settings)
                # course_modified_at = time_epoch(course_attr.get('modified-at', ''))
                course_created_at = get_date(course_attr.get("created-at", ""))
                provider = course_attr.get("provider", "")
                if provider is None and course_attr.get("is-internal") is True:
                    provider = "Internal"
                course_duration = get_duration(
                    course_attr.get("duration-type", ""),
                    course_attr.get("duration", ""),
                )
                language = course_attr.get("language", "")

                item = {
                    "status": "",
                    "category": "",
                    "group_id": "",
                    "description": course_desc,
                    "language": language,
                    "title": course_title,
                    "skills": "",
                    "published_date": course_created_at,
                    "lms_course_id": course_id,
                    "lms_data": "",
                    "course_type": card_label,
                    "image_url": image_url,
                    "provider": provider,
                    "difficulty": "",
                    "course_url": degreed_url,
                    "duration_hours": course_duration,
                }

                data.append(item)

    course_list_end_time = time.perf_counter()
    print(
        f"Time taken for fetching Combined courses: {course_list_end_time - course_list_start_time:0.4f} seconds"
    )

    # print(data)

    end_handler_time = time.perf_counter()
    print(
        f"Time taken for fetching Handler: {end_handler_time - start_handler_time:0.4f} seconds"
    )

    return {"statusCode": 200, "body": json.dumps({"data": data})}


def careerhub_get_entity_details_handler(event, context):
    """Careerhub get Entity Course details"""
    request_data = event.get("request_data", {})
    app_settings = event.get("app_settings", {})

    degreed_base_url = app_settings.get("degreed_base_url")
    baseurl = "https://api." + degreed_base_url + "/"
    # get token
    token_url = "https://" + degreed_base_url
    token = get_access_token(app_settings, token_url)
    request_headers = {"Authorization": "Bearer " + str(token)}

    entity_id = request_data.get("entity_id", 0)
    print(entity_id)

    if entity_id is None or entity_id == "None":
        return error_response("Entity id cannot be blank")

    # getting course details
    course_details_response = requests.get(
        baseurl + "/api/v2/content/" + str(entity_id), headers=request_headers
    )

    if course_details_response.status_code != 200:
        return error_response('Could not get course detail. Status code: ' +
                              f'{course_details_response.status_code}. Reason: ' +
                              f'{course_details_response.reason}.')

    course_details_response_json = course_details_response.json()
    # print(json.dumps(course_details_response_json, indent=4))

    course_json = course_details_response_json["data"]

    course_attr = course_json.get("attributes", "")

    # Course duration
    course_duration = get_duration(
        course_attr.get("duration-type", ""), course_attr.get("duration", "")
    )

    # Course URL
    degreedUrl = course_attr.get("degreed-url", "")

    provider = course_attr.get("provider", "")
    if provider is None and course_attr.get("is-internal") is True:
        provider = "Internal"

    course_modified_at = time_epoch(course_attr.get("modified-at", ""))
    course_created_at = get_date(course_attr.get("created-at", ""))
    last_modified_date = get_date(course_attr.get("modified-at", ""))
    image_url = get_image_url(course_attr.get("image-url", ""), app_settings)
    owner = course_attr.get("owner") or "NA"

    entity_detail = {
        "entity_id": course_json.get("id"),
        "card_label": course_attr.get("content-type", "Course"),
        "cta_label": CTA_LABEL,
        "cta_url": degreedUrl,
        "custom_sections": [],
        "description": course_attr.get("summary", ""),
        "fields": [
            {"name": "Provider", "value": provider},
            {"name": "Duration Hours", "value": course_duration},
            {
                "name": "Content Type",
                "value": course_attr.get("content-type", "Course"),
            },
            {"name": "Language", "value": course_attr.get("language", "")},
            {"name": "Owner", "value": owner},
            {"name": "Published Date", "value": course_created_at},
            {"name": "Last Modified Date", "value": last_modified_date},
        ],
        "image_url": image_url,
        "last_modified_ts": course_modified_at,
        "metadata": [],
        "source_name": provider,
        "subtitle": "",
        "tags": [],
        "title": course_attr.get("title", ""),
    }

    data = entity_detail

    print(data)

    return {"statusCode": 200, "body": json.dumps({"data": data})}

def _get_sorted_attendance(data):
    """Sort course attendance data by completion date desc"""
    return sorted(
        data,
        key=lambda course: course.get('completion_date') or 0,
        reverse=True
    )

def careerhub_profile_course_attendance_handler(event, context):
    """Careerhub Profile Course Attendance Handler"""
    request_data = event.get("request_data", {})
    app_settings = event.get("app_settings", {})

    email = get_email(request_data, app_settings)

    degreed_base_url = app_settings.get("degreed_base_url")
    baseurl = "https://api." + degreed_base_url + "/"
    # get token
    token_url = "https://" + degreed_base_url
    token = get_access_token(app_settings, token_url)
    request_headers = {"Authorization": "Bearer " + str(token)}

    # candidate id
    candidate_id = ""
    start_time = time.perf_counter()
    if email != "":
        candidate_id = get_user_id(email, baseurl, request_headers)
    print("Candidate Id:", candidate_id)
    end_time = time.perf_counter()
    print(f"Time taken for fetching Candidate id: {end_time - start_time:0.4f} seconds")

    data = []

    if candidate_id == "" or candidate_id is None:
        # Return empty data without throwing error if candidate not found
        print(f'Warning: could not find user {candidate_id} in Degreed')
    else:
        course_att_start_time = time.perf_counter()
        course_attendance_response = requests.get(
            baseurl + "/api/v2/users/" + candidate_id + "/completions?limit=1000",
            headers=request_headers,
        )

        if course_attendance_response.status_code != 200:
            return error_response('Could not find course attendance list. Status code: ' +
                                    f'{course_attendance_response.status_code}. Reason: ' +
                                    f'{course_attendance_response.reason}.')

        course_attendance_response_json = course_attendance_response.json()
        course_list = course_attendance_response_json["data"]
        for course in course_list:
            com_details = course["included"][0]

            course_com_at = time_epoch(course["attributes"]["completed-at"])
            course_added_at = time_epoch(course["attributes"]["added-at"])

            item = {
                "status": "",
                "medium": "",
                "verified": course["attributes"]["is-verified"],
                "description": "",
                "language": "",
                "title": com_details["attributes"]["title"],
                "lms_course_id": com_details["id"],
                "is_internal": com_details["attributes"]["is-internal"],
                "points_earned": course["attributes"]["points-earned"],
                "course_url": com_details["attributes"]["url"],
                "course_type": com_details["attributes"]["content-type"],
                "completion_date": course_com_at or course_added_at, # Fallback to added-at if no completed-at
                "provider": com_details["attributes"]["provider"],
                "data_json": {},
                "difficulty": "",
                "start_date": course_added_at,
            }

            data.append(item)

        course_att_end_time = time.perf_counter()
        print(
            f"Time taken for fetching course attendance list: {course_att_end_time - course_att_start_time:0.4f} seconds"
        )
    data = _get_sorted_attendance(data)
    # print(data)

    return {"statusCode": 200, "body": json.dumps({"data": data})}

def get_hris_employee_by_email(app_settings,
                               api_field,
                               current_email):
    
    ef_api_url = app_settings.get('ef_api_url')

    ef_api_key = app_settings.get('ef_api_key')

    ef_system_id = app_settings.get('ats_system_id','default')

    hris_url = ef_api_url + '/core/hris-systems/'+ef_system_id+'/hris-employees/'+current_email
    
    headers = { "Authorization": "Basic "+ str(ef_api_key)}
    
    response = requests.get( hris_url, headers=headers, data={})
    if response.status_code == 200:
        hris_resp_json = response.text
        identifier_value = extract_json_value(hris_resp_json,api_field)
        return identifier_value
    return None

def extract_json_value(json_data, json_path):
    try:
        parsed_json = json.loads(json_data)
        jsonpath_expr = parse(json_path)
        matches = jsonpath_expr.find(parsed_json)
        if matches:
            return [match.value for match in matches][0]
        else:
            return None
    except Exception as e:
        print("Error in extracting json value:", e)
        return None

def app_handler(event, context):
    request_data = event.get("request_data", {})
    trigger_name = request_data.get("trigger_name")
    print("Trigger Name: ", trigger_name)
    print("Event: ", event)
    print("Context: ", context)

    app_settings = event.get('app_settings')

    multi_tenant = app_settings.get('multi_tenant',False) # to integrate with multiple degreed tenants

    language_setting = app_settings.get('language_setting','Application Language')

    ef_api_key = event.get('context').get('api_key')

    ef_api_url = event.get('context').get('api_url')

    app_settings['ef_api_key'] = ef_api_key

    app_settings['ef_api_url'] = ef_api_url

    event['app_settings'] = app_settings

    if language_setting == 'Employee Preferred Language':
        #Design Decision: Setting the language to the main key to support regression   
        language_value = request_data.get("locale","en")

        app_settings['language'] = language_value

        event['app_settings'] = app_settings

    if multi_tenant:
        
        api_field = app_settings.get('hris_emp_by_email_api_field',None) # API field from HRIS employee API - Only works if we have HRIS integration enabled

        current_email = request_data.get("current_user_email", "")

        if api_field:
            
            tenant_identifier = get_hris_employee_by_email(app_settings,api_field,current_email)
            
            if tenant_identifier:
                
                tenant_value = app_settings.get('tenant_to_field_mapping').get(tenant_identifier)
                
                tenant_api = app_settings.get('tenant_details').get(tenant_value)

                if tenant_api:
                # Design Decision: Setting the tenant level degreed credentials to the main key to support regression                                
                    app_settings['degreed_client_id'] = tenant_api.get('degreed_client_id')
                    app_settings['degreed_client_secret'] = tenant_api.get('degreed_client_secret')
                    app_settings['degreed_test_email'] = tenant_api.get('tenant_test_email')
                    if language_setting== 'Tenant Language':
                        app_settings['language'] = tenant_api.get("tenant_language","en")

                    event['app_settings'] = app_settings
                else:
                    print("Coundn't find the tenant for the provided identifier for this employee")

    print(f'Updated Event: {event}')
    
    try:
        if trigger_name == "careerhub_entity_search_results":
            return careerhub_entity_search_results_handler(event, context)
        elif trigger_name == "careerhub_get_entity_details":
            return careerhub_get_entity_details_handler(event, context)
        elif trigger_name == "career_planner_recommended_courses":
            return careerhub_homepage_recommended_courses_handler(event, context)
        elif trigger_name == "careerhub_profile_course_attendance":
            return careerhub_profile_course_attendance_handler(event, context)
        else:
            return error_response("Unknown trigger.")

    except Exception as ex:
        print("Something went wrong, traceback: {}".format(traceback.format_exc()))
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': repr(ex),
                'stacktrace': traceback.format_exc(),
            }),
        }
