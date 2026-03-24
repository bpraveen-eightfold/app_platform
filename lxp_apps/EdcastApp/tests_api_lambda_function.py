import unittest
import lambda_function


class MyTestCase(unittest.TestCase):
    def setUp(self):

        self.data = {
            "request_data": {
                "trigger_name": "careerhub_entity_search_results",
                # "trigger_name": "careerhub_homepage_recommended_courses",
                "trigger_source": "ch_homepage",  # ch_career_planner, ch_search, ch_jobs, ch_projects, ch_homepage
                "current_user_email": "payal.sonawane@redcrackle.com",
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
                    # "project_skills": [
                    #     {"name": "Business Strategy"},
                    #     {"name": "Management"},
                    # ],
                    "profile_skills": [
                        {"name": "Business Strategy"},
                        {"name": "Management"},
                    ],
                    # "skill_goals": [
                    #     {"name": "Soft Skills"},
                    #     {"name": "AWS"},
                    #     {"name": "Product Marketing"},
                    #     {"name": "Marketing Strategy"},
                    #     {"name": "Business Development"},
                    # ],
                },
            },
            # "request_data": {
            #     "trigger_name": "careerhub_get_entity_details",
            #     # "trigger_name": "careerhub_profile_course_attendance",
            #     "email": "payal.sonawane@redcrackle.com",
            #     "entity_id": "rwoA7p5",
            #     # "entity_id": "PkZQnA",
            #     "course_id": "zQx8v9W",
            # },
            "app_settings": {
                "edcast_api_key": "886f7b0e6b83739155728ece872fe145",
                "edcast_client_secret": "17f8502c0f86bd6d307d71e33ceef4185f8996c4dc9c6e097281108d79f8d242",
                "edcast_base_url": "https://partner.edcastpreview.com/api/developer/v5",
                "language": "en",
                "edcast_test_email": "swati.aher@edcast.com",
                "use_test_email": "True",
            },
        }

    def test_course_attendance(self):
        if (
            self.data["request_data"]["trigger_name"]
            == "careerhub_entity_search_results"
        ):
            result = lambda_function.careerhub_entity_search_results_handler(
                self.data, None
            )
            self.assertEqual(200, result["statusCode"])
        if self.data["request_data"]["trigger_name"] == "careerhub_get_entity_details":
            result = lambda_function.careerhub_get_entity_details_handler(
                self.data, None
            )
            self.assertEqual(200, result["statusCode"])
        if (
            self.data["request_data"]["trigger_name"]
            == "careerhub_homepage_recommended_courses"
        ):
            result = lambda_function.career_planner_recommended_courses_handler(
                self.data, None
            )
            self.assertEqual(200, result["statusCode"])
        # if (
        #     self.data["request_data"]["trigger_name"]
        #     == "careerhub_profile_course_attendance"
        # ):
        #     result = lambda_function.careerhub_profile_course_attendance_handler(
        #         self.data, None
        #     )
        #     self.assertEqual(200, result["statusCode"])


if __name__ == "__main__":
    unittest.main()
