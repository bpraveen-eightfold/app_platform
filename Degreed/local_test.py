from lambda_function import app_handler

# Function for testing on console, adjust as needed locally
if __name__ == "__main__":
    null = None
    true = True
    false = False
    event = {
        "request_data": {
            "current_user_email": "admin.at.redcrackle.com@eightfolddemo-redcrackle.com",
            "term": null,
            "fields": null,
            "fq": {
            "profile_skills": [
                {
                "name": "Microsoft Office"
                },
                {
                "name": "Project Management"
                },
                {
                "name": "Entrepreneurship"
                },
                {
                "name": "Software Engineering"
                },
                {
                "name": "Brand Management"
                }
            ],
            "skill_goals": [
                {
                "name": "Financial Planning and Analysis"
                },
                {
                "name": "Financial Statement Analysis"
                },
                {
                "name": "Financial Data Analysis"
                }
            ]
            },
            "facet_fields": null,
            "start": 0,
            "limit": 5,
            "cursor": null,
            "page_size": 10,
            "sort_by": null,
            "trigger_name": "careerhub_entity_search_results",
            "locale": "en",
            "filters": null,
            "trigger_source": "ch_homepage"
        },
        "app_settings": {
            "degreed_client_id": "",
            "degreed_client_secret": "",
            "degreed_base_url": "eu.degreed.com",
            "language": "",
            "degreed_test_email": "",
            "use_test_email": true,
            "recommended_course_limit": 20,
            "skip_all_images": false,
            "default_image_url": "",
            "user_agent": null,
            "use_recommended_learning_endpoint": true,
            "not_internal_only": true,
            "include_restricted": true
        }
    }
    app_handler(event, None)
