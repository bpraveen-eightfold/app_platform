import unittest
import lambda_function


class MyTestCase(unittest.TestCase):
    def setUp(self):

        self.data = {
            "request_data": {
                "trigger_name": "career_hub_profile_view",
                "custom_fields": {
                    "purpose_plot_list": [
                        {
                            "purpose_plot": {
                                "plot": "Creativity",
                                "score": 3.2
                            }
                        },
                        {
                            "purpose_plot": {
                                "plot": "Flexibility",
                                "score": 3.3
                            }
                        },
                        {
                            "purpose_plot": {
                                "plot": "Legacy",
                                "score": 3.69
                            }
                        },
                        {
                            "purpose_plot": {
                                "plot": "Certainty",
                                "score": 3.4
                            }
                        },
                        {
                            "purpose_plot": {
                                "plot": "Quality",
                                "score": 3.32
                            }
                        },
                        {
                            "purpose_plot": {
                                "plot": "Cohesion",
                                "score": 3.31
                            }
                        },
                        {
                            "purpose_plot": {
                                "plot": "Service",
                                "score": 3.37
                            }
                        },
                        {
                            "purpose_plot": {
                                "plot": "Equity",
                                "score": 3.05
                            }
                        },
                        {
                            "purpose_plot": {
                                "plot": "Competition",
                                "score": 3.78
                            }
                        },
                        {
                            "purpose_plot": {
                                "plot": "Authority",
                                "score": 4.13
                            }
                        }
                    ],
                    "purpose_priority_list": [
                        {
                            "purpose_priority": {
                                "priority": "Primary Value",
                                "description": "This individual's most prioritized value is Authority (Perform). This "
                                               "means that they value opportunities to control, and influence people "
                                               "and resources. "
                            }
                        },
                        {
                            "purpose_priority": {
                                "priority": "Lowest Value",
                                "description": "This individual's least prioritized value is Equity (Protect). This "
                                               "means that they are less focused on the fair distribution of "
                                               "resources, inclusive consideration of underrepresented groups, "
                                               "and equal rights. "
                            }
                        },
                        {
                            "purpose_priority": {
                                "priority": "ESG Values",
                                "description": "This individual is more likely than others to consider ESG "
                                               "implications in their decision-making. When gathering information and "
                                               "identifying options for consideration, they are prone to asking "
                                               "questions and requiring evidence around ESG issues to ensure they are "
                                               "making positive strides in improving everyone’s lives now and in the "
                                               "future. "
                            }
                        }
                    ],
                    "purpose_list": [
                        {
                            "purpose_details": {
                                "purpose_ranking_value": "Creativity",
                                "purpose_ranking_value_group": "Pivot",
                                "purpose_ranking_description": "Values pursing less conventional ideas and novel "
                                                               "experiences, taking calculated risks, and engaging in"
                                                               " self-expression.",
                                "purpose_rank": 5
                            }
                        },
                        {
                            "purpose_details": {
                                "purpose_ranking_value": "Flexibility",
                                "purpose_ranking_value_group": "Pivot",
                                "purpose_ranking_description": "Values thriving in new contexts, leading through "
                                                               "change, and persevering in times of uncertainty.",
                                "purpose_rank": 7
                            }
                        },
                        {
                            "purpose_details": {
                                "purpose_ranking_value": "Legacy",
                                "purpose_ranking_value_group": "Preserve",
                                "purpose_ranking_description": "Values preserving tradition and history while "
                                                               "maintaining alignment with an entity greater than "
                                                               "oneself.",
                                "purpose_rank": 9
                            }

                        },
                        {
                            "purpose_details": {
                                "purpose_ranking_value": "Certainty",
                                "purpose_ranking_value_group": "Preserve",
                                "purpose_ranking_description": "Values predictability, safety, consistency, "
                                                               "and reliability.",
                                "purpose_rank": 3
                            }

                        },
                        {
                            "purpose_details": {
                                "purpose_ranking_value": "Quality",
                                "purpose_ranking_value_group": "Preserve",
                                "purpose_ranking_description": "Values precision, objectivity, and performing to high "
                                                               "standards.",
                                "purpose_rank": 6
                            }

                        },
                        {
                            "purpose_details": {
                                "purpose_ranking_value": "Cohesion",
                                "purpose_ranking_value_group": "Protect",
                                "purpose_ranking_description": "Values being part of and contributing to a "
                                                               "supportive, collaborative, and successful team.",
                                "purpose_rank": 2
                            }

                        },
                        {
                            "purpose_details": {
                                "purpose_ranking_value": "Service",
                                "purpose_ranking_value_group": None,
                                "purpose_ranking_description": "Values caring for those in need and placing the needs "
                                                               "of others, society, and the environment over their "
                                                               "own.",
                                "purpose_rank": 8
                            }

                        },
                        {
                            "purpose_details": {
                                "purpose_ranking_value": "Equity",
                                "purpose_ranking_value_group": "Protect",
                                "purpose_ranking_description": "Values the fair distribution of resources, inclusive "
                                                               "consideration of underrepresented groups, "
                                                               "and equal rights.",
                                "purpose_rank": 10
                            }

                        },
                        {
                            "purpose_details": {
                                "purpose_ranking_value": "Competition",
                                "purpose_ranking_value_group": "Perform",
                                "purpose_ranking_description": "Values the challenges and rewards associated with "
                                                               "outperforming one’s rivals.",
                                "purpose_rank": 4
                            }

                        },
                        {
                            "purpose_details": {
                                "purpose_ranking_value": "Authority",
                                "purpose_ranking_value_group": "Perform",
                                "purpose_ranking_description": "Values opportunities to control, and influence people "
                                                               "and resources.",
                                "purpose_rank": 1
                            }

                        }
                    ],
                    "lead_expertise_list": [
                        {
                            "lead_expertise": {
                                "expertise": "Human Capital",
                                "score": 2,
                                "level": "Competent"
                            }
                        },
                        {
                            "lead_expertise": {
                                "expertise": "Operations & Execution",
                                "score": 2.09,
                                "level": "Advanced Beginner"
                            }
                        },
                        {
                            "lead_expertise": {
                                "expertise": "Strategy & Innovation",
                                "score": 4.4,
                                "level": "Advanced Beginner"
                            }
                        },
                        {
                            "lead_expertise": {
                                "expertise": "Commercial",
                                "score": 1.8,
                                "level": "Learner"
                            }
                        },
                        {
                            "lead_expertise": {
                                "expertise": "Finance",
                                "score": 3.17,
                                "level": "Competent"
                            }
                        }
                    ],
                    # "lead_expertise_list": []
                }

            }
        }

    def test_profile_app(self):
        if self.data["request_data"]['trigger_name'] == 'ch_profile_view_main_content':
            result = lambda_function.ch_profile_view_main_content_handler(self.data, None)
            self.assertEqual(200, result["statusCode"])
        if self.data["request_data"]['trigger_name'] == 'ch_profile_view_main_content_on_expand':
            result = lambda_function.ch_profile_view_main_content_on_expand_handler(self.data, None)
            self.assertEqual(200, result["statusCode"])
        if self.data["request_data"]['trigger_name'] == 'career_hub_profile_view':
            result = lambda_function.career_hub_profile_view_handler(self.data, None)
            self.assertEqual(200, result["statusCode"])


if __name__ == '__main__':
    unittest.main()
