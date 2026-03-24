def get_data():
    data = {
        "type": "required-learning",
        "id": "72YeaV",
        "attributes": {
            "employee-id": None,
            "assignment-type": "Assigned",
            "status": "Pending",
            "due-at": None,
            "created-at": "2022-03-16T10:15:29.5034801",
            "modified-at": None,
        },
        "links": {
            "self": "https://api.betatest.degreed.com/api/v2/required-learning/72YeaV"
        },
        "relationships": [
            {"user": {"data": {"id": "zk3jPZ", "type": "users"}}},
            {"content": {"data": {"id": "zQV1pwa", "type": "content"}}},
            {"provider": {"data": {"id": None, "type": "providers"}}},
        ],
        "included": [
            {
                "type": "content",
                "id": "zQV1pwa",
                "attributes": {
                    "content-type": "Article",
                    "url": "https://www.exitcertified.com/blog/focus-on-the-right-it-training-for-the-future?reseller=7",
                    "title": "Focus on the Right IT Training for the Future",
                    "provider": None,
                },
                "links": {
                    "self": "https://api.betatest.degreed.com/api/v2/content/zQV1pwa"
                },
            }
        ],
    }
    return data
