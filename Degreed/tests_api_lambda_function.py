import unittest
import lambda_function


class MyTestCase(unittest.TestCase):
    def setUp(self):

        self.data = {
            "request_data": {
                "trigger_name": "careerhub_entity_search_results",
                "trigger_source": "ch_search",  # ch_career_planner, ch_search, ch_jobs, ch_projects, ch_homepage
                "current_user_email": "payal.sonawane@redcrackle.com",
                "skills": ["Management", "Business Strategy"],
                "limit": 10,
                "start": 10,
                "cursor": None,
                "term": None,
                "fq": {
                    "position_skills": [
                        {"name": "Microsoft Office"},
                        {"name": "Leadership"},
                        {"name": "Brand Management"},
                        {"name": "Project Management"},
                        {"name": "Soft Skills"},
                        {"name": "Public Speaking"},
                        {"name": "Interactive Media"},
                        {"name": "Soft Skills"},
                        {"name": "Brand Identity"},
                        {"name": "Business Requirements"},
                        {"name": "Project Manager"},
                        {"name": "AWS"},
                        {"name": "Proofing"},
                    ],
                    "required_skills": [
                        {"name": "Research"},
                        {"name": "Public Speaking"},
                        {"name": "Strategic Planning"},
                        {"name": "Software Engineering"},
                        {"name": "Leadership"},
                        {"name": "Microsoft Office"},
                        {"name": "Sales"},
                        {"name": "Linux"},
                        {"name": "CSS"},
                        {"name": "Navy"},
                        {"name": "Dod"},
                        {"name": "Entrepreneurship"},
                        {"name": "Information Assurance"},
                        {"name": "Integration"},
                        {"name": "Accounting"},
                        {"name": "Event Planning"},
                        {"name": "Negotiation"},
                        {"name": "New Business Development"},
                        {"name": "Small Business"},
                        {"name": "Team Building"},
                        {"name": "Financial Accountability"},
                        {"name": "Daily Accounting"},
                        {"name": "Other Accounting"},
                        {"name": "Accounting Information Systems"},
                        {"name": "Revenue Accounting"},
                        {"name": "Accounts Payable"},
                        {"name": "Account Payables"},
                        {"name": "Collating"},
                        {"name": "Portfolio Accounting"},
                        {"name": "Large Accounts"},
                        {"name": "Global Cross-Functional Team Leadership"},
                        {"name": "Project Leadership"},
                     ],
                     "project_skills": [
                         {"name": "Business Strategy"},
                         {"name": "Management"},
                     ],
                    "profile_skills": [
                        {"name": "Business Strategy"},
                        {"name": "Management"},
                    ],
                    "skill_goals": [
                        {"name": "Soft Skills"},
                        {"name": "AWS"},
                        {"name": "Product Marketing"},
                        {"name": "Marketing Strategy"},
                        {"name": "Business Development"},
                    ],
                },
            },
            "app_settings": {
                "degreed_client_id": "7b5a18386173507b",
                # "degreed_client_id": "76438e9b795c4618",
                "degreed_client_secret": "259ad32f98f366ea5b29b9cb8c3cd4c8",
                # "degreed_client_secret": "8f32f1dd52a4aec175dd7711b46d5b2a",
                "degreed_base_url": "betatest.degreed.com",
                "language": "en",
                "recommended_course_limit": 20,
                # "degreed_test_email": "aolenchikov11@amazonaws.com",
                "degreed_test_email": "payal.sonawane@redcrackle.com",
                "use_test_email": "True",
            },
        }

    def test_careehub_entity_search_results(self):
        self.data["request_data"]["trigger_name"] = "careerhub_entity_search_results"
        self.data["request_data"]["trigger_source"] = "ch_search"
        result = lambda_function.careerhub_entity_search_results_handler(
            self.data, None
        )
        self.assertEqual(200, result["statusCode"])

    def test_careerhub_get_entity_details(self):
        self.data["request_data"] = {
            "trigger_name": "careerhub_get_entity_details",
            "email": "payal.sonawane@redcrackle.com",
            "entity_id": "rwoA7p5",
        }
        result = lambda_function.careerhub_get_entity_details_handler(
            self.data, None
        )
        self.assertEqual(200, result["statusCode"])

    def test_careerhub_homepage_recommended_courses(self):
        self.data["request_data"]["trigger_name"] = "careerhub_entity_search_results"
        self.data["request_data"]["trigger_source"] = "ch_homepage"
        result = lambda_function.careerhub_homepage_recommended_courses_handler(
            self.data, None
        )
        self.assertEqual(200, result["statusCode"])

    def test_careerhub_profile_course_attendance(self):
        self.data["request_data"]["trigger_name"] = "careerhub_profile_course_attendance"
        result = lambda_function.careerhub_profile_course_attendance_handler(
            self.data, None
        )
        self.assertEqual(200, result["statusCode"])


if __name__ == "__main__":
    unittest.main()
