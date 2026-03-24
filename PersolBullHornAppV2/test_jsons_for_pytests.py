# Contains all test jsons used for pytests in test_lambda_function.py

def get_update_candidate_event_context():
    event_context = {
        "operation": "update_candidate",
        "group_id": "persolkelly-sandbox.com",
        "system_id": "BullHorn-App-Adapter",
        "candidate_id": 756,
        "ats_sync_activity_id": 447151023165,
        "profile_id": 446843188648,
        "update_spec": [
            {
                "section_name": "title",
                "section_item": "test_title"
            },
            {
                "section_name": "experience",
                "all_section_items": [
                    {
                        "external_key": None,
                        "source": None,
                        "time": [
                            "2020-08-01",
                            "current"
                        ],
                        "event_type": "experience",
                        "title": "Regional Manager 2",
                        "work": "Segaing & Mandalay 2",
                        "duration": 903,
                        "description": "<div>Standardize Microfinance ------- Manage performance of branches from respective regions by leading them to set, monitor and evaluate their key performance indicators on regular basic for achieving both operational and financial objectives. Take part in assessing human resource needs, staff recruitment, capacity development, performance appraisal of all branch staff from respective regions to ensure that resource is exploited and balanced with the case load, right people are selected, staff are trained and equipped with right knowledge and skills for their career advancement and succession plan development of the MFI, performance evaluation are conducted effectively, and reward and punishment are granted in proper manner.</div>",
                        "location": "",
                        "addl_json": {
                            "src": "ats",
                            "edited_by": [
                                {
                                    "email": "kkumar@eightfold.ai",
                                    "edited_at": 1674301723
                                }
                            ]
                        },
                        "skills": [
                            "Branch"
                        ],
                        "edited": True,
                        "user_verified_skills": True,
                        "is_internal": None,
                        "department": None,
                        "industry": None,
                        "experience_key": None,
                        "start_date": "2020-08-01",
                        "end_date": "current"
                    },
                    {
                        "external_key": None,
                        "source": None,
                        "time": [
                            "2015-01-01",
                            "2018-01-01"
                        ],
                        "event_type": "experience",
                        "title": "Customer Service Officer",
                        "work": "FMI AIR Company Limited",
                        "duration": 1096,
                        "description": "Naypyidaw Airport ------- Assisting passengers by answering questions, providing directions, or attending to their other needs.     Involves checking-in, greeting passengers upon their arrival and ensuring a smooth departure process.      Taking reservations from passengers who call in. Assisting passengers with luggage check-ins at the ticket counter.      Provided baggage wrapping services.      Develop good customer relationships.",
                        "location": "",
                        "addl_json": {
                            "src": "ats"
                        },
                        "skills": [],
                        "edited": None,
                        "user_verified_skills": False,
                        "is_internal": None,
                        "department": None,
                        "industry": None,
                        "experience_key": None,
                        "growth_percentile": None,
                        "start_date": "2015-01-01",
                        "end_date": "2018-01-01"
                    }
                ]
            }
        ]
    }
    return event_context

def get_change_app_stage_event_context():
    event_context = {
        "operation": "change_appl_stage",
        "group_id": "eightfolddemo-kkumar.com",
        "system_id": "volkscience",
        "candidate_id": 961529,
        "application_id": "vs-961529-12443499-1674993612",
        "job_id": 12443499,
        "new_ats_stage": {
            "wf_stage": "Onsite Interview",
            "wf_sub_stage": None,
            "stage_ts": 1234567890,
            "reason": None,
            "stage": "Onsite Interview",
            "user": {
                "name": "Eightfold.Ai User",
                "first_name": None,
                "last_name": None,
                "email": "demo@eightfolddemo-kkumar.com",
                "workflow_recipe_id": None,
                "ats_roles": [],
                "userid": None,
                "emp_id": None
            }
        },
        "new_stage": "Onsite Interview",
        "new_sub_stage": None,
        "application": {
            "application_id": "1674993612"
        },
        "ats_sync_activity_id": 478451282,
        "profile_id": 961529,
        "pid": "12443499",
        "comment": "test_comment"
    }
    return event_context
        
def get_add_candidate_note_event_context():
    event_context = {
        "candidate_id": 446842466743,
        "note": {
            "creator": "demo@persolkelly-sandbox.com",
            "creation_ts": 1674817800.0471673,
            "note_type": "note",
            "subject": None,
            "body": "Test Note",
            "to": None,
            "sender": 'abd@def.com',
            "cc": None,
            "visibility": None,
            "job_id": "565409",
            "__initialized": True,
            "_modified_fields": [
                "creator",
                "creation_ts",
                "note_type",
                "job_id",
                "body",
                "visibility"
            ]
        }
    }
    return event_context

def get_application_for_handle_add_application():
    application = {
        "application_id": 456,
        "candidate_id": None,
        "jobs": [
            [
                "554248",
                "[Test 5 Jan] EF Senior Devops Developer - 554248"
            ]
        ],
        "application_ts": 1675056231,
        "last_modified_ts": 1675056231,
        "past_stages": [],
        "current_stage": {
            "wf_stage": "Under Consideration",
            "wf_sub_stage": None,
            "stage_ts": 1675056231,
            "reason": None,
            "stage": "Under Consideration",
            "user": {
                "name": "Persol User",
                "first_name": None,
                "last_name": None,
                "email": "demo@persolkelly-sandbox.com",
                "workflow_recipe_id": None,
                "ats_roles": [],
                "userid": None,
                "emp_id": None
            }
        },
    }
    return application

def get_create_candidate_req_data():
    req_data = {
        "additionalSections": None,
        "awards": [],
        "certificates": [],
        "customFields": None,
        "customInfo": {},
        "education": [
            {
                "awards": [],
                "degree": "Bachelor's Degree, Linguistics, 3.58",
                "description": "* Major: Linguistics \n* Minors: Japanese, Music, and Art History",
                "endTime": "1104537600.0",
                "location": "",
                "major": "",
                "school": "University of Washington",
                "startTime": "1009843200.0"
            },
            {
                "awards": [],
                "degree": "Master's Degree, Teaching English to Speakers of Other Languages, 3.9",
                "description": "",
                "endTime": "1199145600.0",
                "location": "",
                "major": "",
                "school": "University of Washington",
                "startTime": "1136073600.0"
            }
        ],
        "educationLevel": "Masters",
        "efGender": "f",
        "efRace": "asian",
        "email": "alina.to@gmail.com",
        "employeeInfo": {
            "employeeId": None,
            "performanceManagement": {
                "performanceRatings": [],
                "promotionReadiness": None
            },
            "relocationPreferences": None,
            "successionPlan": {
                "leaderWithoutPathForward": "True",
                "successionPlanId": None,
                "successionPlanMetrics": {
                    "readiness": {
                        "ready_later": 0,
                        "ready_now": 0,
                        "ready_soon": 0
                    }
                },
                "successionPlanNotes": [],
                "successionPlanRole": None,
                "successors": []
            }
        },
        "endorsements": [],
        "experiences": [
            {
                "addlJson": {
                    "src": "ats"
                },
                "department": None,
                "description": "",
                "durationMonths": 0,
                "edited": None,
                "endTime": 0,
                "experienceKey": None,
                "industry": None,
                "isCurrent": False,
                "isInternal": False,
                "location": "",
                "skills": [],
                "startTime": 0,
                "title": "Independent Consultant",
                "userVerifiedSkills": False,
                "work": "Self"
            },
            {
                "addlJson": {
                    "src": "ats"
                },
                "department": None,
                "description": "",
                "durationMonths": 44,
                "edited": None,
                "endTime": 1677801600,
                "experienceKey": None,
                "industry": None,
                "isCurrent": False,
                "isInternal": False,
                "location": "",
                "skills": [],
                "startTime": 1564617600,
                "title": "Software Engineer",
                "userVerifiedSkills": False,
                "work": "North Highland"
            }
        ],
        "firstName": "Alina",
        "fullName": "Alina To",
        "gender": "F",
        "highlights": [
            "Went to 1 top school: University of Washington"
        ],
        "id": "1ljdn6jPq",
        "imageUrl": "",
        "industries": [],
        "internalGroupAffiliation": [],
        "language": "en",
        "lastName": "To",
        "lastUpdated": 1677848008,
        "location": None,
        "patents": [],
        "phone": "",
        "preferences": {
            "contactConsent": None
        },
        "profileId": 446849572009,
        "projects": [],
        "publications": [],
        "race": None,
        "resumeFileName": None,
        "roleId": None,
        "seniorityLevel": "Mid-Level",
        "skillGoals": [],
        "skills": [
            {
                "displayName": "jQuery",
                "evaluations": [],
                "name": "jquery",
                "source": None
            },
            {
                "displayName": "JavaScript",
                "evaluations": [],
                "name": "javascript",
                "source": None
            }
        ],
        "sources": [
            {
                "datetime": "2023-03-03T12:03:21+00:00",
                "sourceName": "persolkelly-sandbox.com",
                "sourceType": "ats"
            }
        ],
        "summary": "",
        "title": "Web Developer",
        "urls": [],
        "workExperienceYears": 16.583333333333332
    }
    return req_data

def get_add_candidate_event_context():
    event_context = {
        "operation": "add_candidate",
        "group_id": "persolkelly-sandbox.com",
        "profile_id": 12345,
        "system_id": "PK-BullHorn-EntitySync",
        "candidate_id": 123,
        "application": {
            "application_id": 456,
            "candidate_id": 123,
            "jobs": [
                [
                    "554248",
                    "[Test 5 Jan] EF Senior Devops Developer - 554248"
                ]
            ],
            "application_ts": 1675056231,
            "last_modified_ts": 1675056231,
            "past_stages": [],
            "current_stage": {
                "wf_stage": "Under Consideration",
                "wf_sub_stage": None,
                "stage_ts": 1675056231,
                "reason": None,
                "stage": "Under Consideration",
                "user": {
                    "name": "Persol User",
                    "first_name": None,
                    "last_name": None,
                    "email": "demo@persolkelly-sandbox.com",
                    "workflow_recipe_id": None,
                    "ats_roles": [],
                    "userid": None,
                    "emp_id": None
                }
            },
        },
        "ats_action_user": {
            "name": "Persol User",
            "first_name": "Persol",
            "last_name": "User",
            "email": "demo@persolkelly-sandbox.com",
            "workflow_recipe_id": None,
            "ats_roles": [],
            "userid": None,
            "emp_id": None
        }
    }
    return event_context
        
def get_candidate_entity_from_bh():
    bh_candidate = {'data': {'id': 1234, 'occupation': 'Web Developer', 'dateOfBirth': None, 'customText3': None, 'address': {'address1': None, 'address2': None, 'city': None, 'countryCode': 'SG', 'countryID': 2333, 'countryName': 'Singapore', 'state': None, 'timezone': None, 'zip': None}, 'email': 'alina.to@gmail.com', 'email2': None, 'mobile': '', 'gender': 'F', 'ethnicity': None, 'firstName': 'Alina', 'customText1': '3YvQneqX', 'lastName': 'To', 'dateLastModified': 1677844603287, 'primarySkills': {'total': 10, 'data': [{'id': 1002183, 'name': 'jQuery'}, {'id': 1002180, 'name': 'JavaScript'}, {'id': 1002003, 'name': 'Proofreading'}, {'id': 1001960, 'name': 'Leadership'}, {'id': 1001674, 'name': 'Research'}, {'id': 1000710, 'name': 'NodeJS'}, {'id': 1000704, 'name': 'JSON'}, {'id': 1000697, 'name': 'HTML5'}, {'id': 1000681, 'name': 'CSS'}, {'id': 1000674, 'name': 'AngularJS'}]}, 'educations': {'total': 3, 'data': [{'id': 2827481}, {'id': 2827480}, {'id': 2827479}]}, 'workHistories': {'total': 8, 'data': [{'id': 8598390}, {'id': 8598389}, {'id': 8598388}, {'id': 8598387}, {'id': 8598386}, {'id': 8598385}, {'id': 8598384}, {'id': 8598383}]}, 'notes': {'total': 0, 'data': []}, 'submissions': {'total': 0, 'data': []}, 'fileAttachments': {'total': 0, 'data': []}, 'customTextBlock1': None}}
    return bh_candidate

def get_joborder_entity_from_bh():
    job_order = {'data': {'id': 1234, 'title': 'Arjuna 23-SEP Test Position', 'description': 'test', 'clientCorporation': {'id': 121652, 'name': 'Bullhorn Test'}, 'status': 'Actively Recruiting', 'isOpen': True, 'correlatedCustomText10': 'SG - PERM - BNF - BNF1', 'dateLastModified': 1663940146673, 'dateAdded': 1663940146673, 'publishedCategory': None, 'customText13': None, 'owner': {'id': 2884809, 'firstName': 'Eightfold', 'lastName': 'API User'}, 'address': {'address1': '123 Address Rd', 'address2': None, 'city': 'St. Louis', 'countryCode': 'US', 'countryID': 1, 'countryName': 'United States', 'state': 'Missouri', 'timezone': 'America/Chicago', 'zip': '63033'}, 'clientContact': {'id': 1696488, 'firstName': 'test', 'lastName': 'test'}}}
    return job_order

def get_candidate_mapped_data():
    candidate_mapped_data = {'candidateId': '1234', 'title': 'Web Developer', 'address': None, 'emails': 'alina.to@gmail.com', 'gender': 'F', 'firstName': 'Alina', 'lastName': 'To', 'lastActivityTs': 1677844603287, 'education': [{'degree': "Bachelor's Degree, Linguistics, 3.58", 'school': 'University of Washington', 'startTs': 1009843200, 'endTs': 1104537600, 'location': '', 'major': '', 'description': '* Major: Linguistics \n* Minors: Japanese, Music, and Art History'}, {'degree': "Master's Degree, Teaching English to Speakers of Other Languages, 3.9", 'school': 'University of Washington', 'startTs': 1136073600, 'endTs': 1199145600, 'location': '', 'major': '', 'description': ''}, {'degree': 'Certificate of Completion, Web Development', 'school': 'Code Fellows', 'startTs': 1420070400, 'endTs': 1420070400, 'location': '', 'major': '', 'description': '* Foundations 1 \n* Foundations 2 (Javascript) \n* Front-End Web Development Accelerator (Intensive full-time 8-week course)'}], 'experience': [{'company': 'Seattle', 'startTs': 1157068800, 'title': 'English Language Teacher', 'description': '* Taught and tutored students from grade K-12, undergraduate and graduate students whose English is their second language \n* Created and executed curriculums base on students’ individual learning goals \n* Advised and helped students in college admission materials for undergraduate and graduate programs, including personal statements, CVs, and cover letters', 'location': '', 'endTs': 1409529600, 'isCurrent': False, 'isInternal': False}, {'company': 'University of Washington Professional & Continuing Education', 'startTs': 1212278400, 'title': 'Extension Lecturer', 'description': '* Planned and taught 3-to-10-week university-level English courses to adult learners \n* Assessed and evaluated students’ learning progress \n* Created and implemented course materials and assessment materials \n* Filled in for absent instructors in emergency and on short and medium term assignments \n* Integrated lessons into long-term curriculum plan to ensure continuity of education objectives \n* Implemented use of technology in daily class assignments and activities \n* Courses taught include low, intermediate, and advanced levels \n* Focuses on academic, non-academic, and business English in writing, reading, speaking, listening, pronunciation, lecture listening and note-taking, cross-cultural studies, and TOEFL prep', 'location': '', 'endTs': 1409529600, 'isCurrent': False, 'isInternal': False}, {'company': 'Holy Names Academy', 'startTs': 1346457600, 'title': 'Music Faculty', 'description': "* Teach one-on-one private violin lessons with high school students \n* Coordinate with fellow music faculty on practice room assignments \n* Coordinate with students and parents on students' progress and schedule \n* Follow school-wide guidelines and attend required staff meetings", 'location': '', 'endTs': 1441065600, 'isCurrent': False, 'isInternal': False}, {'company': 'Freelance', 'startTs': 1207008000, 'title': 'Professional Violinist', 'description': '* Perform violin among a variety of genres and groups, for live performance and studio recording. \n* Promote and market my services as a violinist through social media and web presence. \n* Coordinate, negotiate and execute assignments with contractors and employers, and correspond respectfully with prospective clients. \n* Manage travel arrangements for performances and oversee the budget. \n* Prepare before rehearsals independently and during rehearsals with others efficiently on short notices, and collaborate with fellow musicians (colleagues) and directors (superiors). \n* Teach classical violin performance and theory in one-on-one lessons. \n* Create and execute curriculums base on students’ individual learning goals. \n* Groups include Tacoma Symphony Orchestra (9/2011 - Present)', 'location': '', 'endTs': 1677843373, 'isCurrent': False, 'isInternal': False}, {'company': 'Freelance', 'startTs': 1417392000, 'title': 'Web Developer Contractor', 'description': '* Design and execute responsive websites from the ground up for small and mid-sized businesses and artists, including Melissa Sharkey (licensed massage practitioner), Julia Sandler Deak (adjunct faculty), and Nostradamus Junior (local mixed media artist)', 'location': '', 'endTs': 1677843373, 'isCurrent': False, 'isInternal': False}, {'company': 'Foundry Interactive', 'startTs': 1456790400, 'title': 'Software Developer / Accessibility Consultant', 'description': 'Project: healthcare web applications\ndeveloped responsive frontend reactjs web application. Built user interface components from provided designs and acceptance criteria. Developed mocha and enzyme reactjs unit tests and performed cross-browser testing. \n\nproject: healthcare mobile applications\ndeveloped native ios / android mobile applications with nodejs backend and custom python django cms. Performed full accessibility audit for ios and android mobile applications to meet wcag compliance levels at a, aa, and aaa. Developed mobile app features from provided designs and acceptance criteria. Worked closely with qa team to address and fix bugs. Consulted with clients on feature development to drive towards best practices and scalability. Acquired and executed new languages and technologies quickly. Mentored junior team members.', 'location': '', 'endTs': 1525132800, 'isCurrent': False, 'isInternal': False}, {'company': 'Self', 'startTs': 0, 'title': 'Independent Consultant', 'description': '', 'location': '', 'endTs': 0, 'isCurrent': False, 'isInternal': False}, {'company': 'North Highland', 'startTs': 1564617600, 'title': 'Software Engineer', 'description': '', 'location': '', 'endTs': 1677844055, 'isCurrent': False, 'isInternal': False}], 'skills': ['jQuery', 'JavaScript', 'Proofreading', 'Leadership', 'Research', 'NodeJS', 'JSON', 'HTML5', 'CSS', 'AngularJS']}
    return candidate_mapped_data

def get_joborder_mapped_data():
    joborder_mapped_data = {'recruiter': {'name': 'Eightfold API User'}, 'locations': ['123 Address Rd St. Louis'], 'hiringManager': {'name': 'Eightfold', 'email': ''}, 'atsEntityId': 1234, 'title': 'Arjuna 23-SEP Test Position', 'description': 'test', 'company': 'Bullhorn Test', 'status': 'Actively Recruiting', 'open': True, 'businessUnit': 'SG - PERM - BNF - BNF1', 'lastUpdated': 1663940146673, 'createdAt': 1663940146673, 'companyDescription': 'Bullhorn Test'}
    return joborder_mapped_data
