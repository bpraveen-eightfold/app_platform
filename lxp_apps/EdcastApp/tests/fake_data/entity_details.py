def get_data_sample1():
    cards = {
        "card": {
            "author": {
                "id": 177117,
                "handle": "@maulik",
                "avatarimages": {
                    "tiny": "https://dp598loym07sk.cloudfront.net/users/avatars/000/177/117/tiny/unnamed.png?1602848820",
                    "small": "https://dp598loym07sk.cloudfront.net/users/avatars/000/177/117/small/unnamed.png?1602848820",
                    "medium": "https://dp598loym07sk.cloudfront.net/users/avatars/000/177/117/medium/unnamed.png?1602848820",
                    "large": "https://dp598loym07sk.cloudfront.net/users/avatars/000/177/117/large/unnamed.png?1602848820",
                },
                "fullName": "Maulik Soni",
                "profile": {
                    "id": 20886,
                    "timeZone": "Asia/Kolkata",
                    "language": "en",
                    "expertTopics": [],
                    "learningTopics": [
                        {
                            "topic_name": "qa.hard_skills.planning_tools",
                            "topic_id": "5048474091679274781",
                            "topic_label": "Planning Tools",
                            "domain_name": "edcast.hard_skills",
                            "domain_id": "5176881040914734998",
                            "domain_label": "hard_skills",
                        },
                        {
                            "topic_name": "qa.hard_skills.java_virtual_machine",
                            "topic_id": "5048473327782939474",
                            "topic_label": "Java Virtual Machine (JVM)",
                            "domain_name": "edcast.hard_skills",
                            "domain_id": "5176881040914734998",
                            "domain_label": "hard_skills",
                        },
                    ],
                    "jobTitle": "JS Dev",
                },
                "isSuspended": False,
            },
            "cardMetadatum": {
                "id": 2185993,
                "plan": "paid",
                "level": None,
                "custom_data": None,
            },
            "cardSubtype": "file",
            "cardType": "media",
            "channels": [{"id": 65753, "label": "mnbvcxz"}],
            "createdAt": "2020-11-17T10:15:24.000Z",
            "duration": 0,
            "externalId": "5512530",
            "id": "ECL-05b7ab0f-b0ec-4345-9fd0-aa1a5505c5cd",
            "isPaid": True,
            "isPublic": True,
            "message": "Not_Working.pdf",
            "prices": [
                {"id": 79918, "amount": "12.00", "currency": "USD", "symbol": "$"}
            ],
            "provider": "User Generated Content",
            "readableCardType": "Action Step",
            "resource": None,
            "slug": "not_working-pdf",
            "tags": [{"id": 76924, "name": "PDF"}],
            "teams": [
                {"id": 37901, "name": "Group4"},
                {"id": 48626, "name": "non private channel1"},
                {"id": 13062, "name": "Lahu Channel"},
            ],
            "language": "un",
            "shareUrl": "https://edqa.cmnetwork.co/insights/5512530",
            "additionalMetadata": {
                "promotion": False,
                "discount": False,
                "allow_enrollment": False,
            },
            "contentLanguages": [{"id": 1798763, "message": "", "language": "un"}],
            "publishedAt": "2020-11-17T10:15:24.000Z",
        }
    }
    return cards


def get_data_sample2():
    cards = {
        "card": {
            "id": "ECL-9eeb3886-c01e-4bde-b97e-7204eb2be35b",
            "slug": "python-tutorial-with",
            "cardType": "media",
            "createdAt": "2020-03-23T10:28:43.000Z",
            "duration": 0,
            "title": "Python Tutorial with tag",
            "message": "Python Tutorial with tag",
            "language": "en",
            "prices": [],
            "provider": "User Generated Content",
            "readableCardType": "Article",
            "resource": {
                "id": 5664145,
                "imageUrl": "https://www.edcast.com/corp/wp-content/uploads/elementor/thumbs/CS-EdCast-pm014vjo752gl4ml7c5stenic0t4w3nithpn388o0w.png",
                "title": "Python Tutorial",
                "description": "",
                "url": "https://www.w3schools.com/python/default.asp",
                "siteName": None,
                "type": "Article",
                "videoUrl": None,
                "embedHtml": None,
            },
            "additionalMetadata": {
                "promotion": False,
                "discount": False,
                "allow_enrollment": False,
                "cpe_credits": "",
                "cpe_subject": "",
            },
            "providerImage": None,
            "shareUrl": "https://edqa.cmnetwork.co/insights/4591754",
            "publishedAt": "2020-03-23T10:28:43.000Z",
            "contentLanguages": [
                {
                    "id": 744475,
                    "message": "",
                    "language": "en",
                    "resource": {
                        "id": 5664145,
                        "imageUrl": "https://cdn.filestackcontent.com/xIOzdWuZTB2HLZ8Dkp0K",
                        "title": "Python Tutorial",
                        "description": "",
                        "url": "https://www.w3schools.com/python/default.asp",
                        "siteName": None,
                        "type": "Article",
                        "videoUrl": None,
                        "embedHtml": None,
                    },
                }
            ],
        }
    }
    return cards


def entity_resp_data_sample1():
    data = {
        "entity_id": "ECL-05b7ab0f-b0ec-4345-9fd0-aa1a5505c5cd",
        "cta_label": "View in EdCast",
        "card_label": "Course",
        "cta_url": "https://edqa.cmnetwork.co/insights/5512530",
        "custom_sections": [],
        "description": "",
        "fields": [
            {"name": "Provider", "value": "User Generated Content"},
            {"name": "Duration Hours", "value": 0},
            {"name": "Content Type", "value": "Course"},
            {"name": "Language", "value": "un"},
            {"name": "Author", "value": "Maulik Soni"},
            {"name": "Created Date", "value": "17/11/2020"},
            {"name": "Published Date", "value": "17/11/2020"},
        ],
        "image_url": "https://integrations.edcast.com/assets/images/logo-icon.png",
        "last_modified_ts": "",
        "metadata": [],
        "source_name": "User Generated Content",
        "subtitle": "",
        "tags": "",
        "title": "",
    }

    return data


def entity_resp_data_sample2():
    data = {
        "entity_id": "ECL-9eeb3886-c01e-4bde-b97e-7204eb2be35b",
        "cta_label": "View in EdCast",
        "card_label": "Article",
        "cta_url": "https://edqa.cmnetwork.co/insights/4591754",
        "custom_sections": [],
        "description": "",
        "fields": [
            {"name": "Provider", "value": "User Generated Content"},
            {"name": "Duration Hours", "value": 0},
            {"name": "Content Type", "value": "Article"},
            {"name": "Language", "value": "en"},
            {"name": "Author", "value": ""},
            {"name": "Created Date", "value": "23/03/2020"},
            {"name": "Published Date", "value": "23/03/2020"},
        ],
        "image_url": "https://www.edcast.com/corp/wp-content/uploads/elementor/thumbs/CS-EdCast-pm014vjo752gl4ml7c5stenic0t4w3nithpn388o0w.png",
        "last_modified_ts": "",
        "metadata": [],
        "source_name": "User Generated Content",
        "subtitle": "",
        "tags": "",
        "title": "Python Tutorial",
    }

    return data
