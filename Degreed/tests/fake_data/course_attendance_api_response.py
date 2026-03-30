def get_data():
    data = [
        {
            "type": "completions",
            "id": "zrNodlZ",
            "attributes": {
                "employee-id": None,
                "completed-at": "2022-02-17T00:00:00",
                "added-at": "2022-02-17T09:11:26.947",
                "points-earned": "0.7093333",
                "is-verified": False,
                "rating": 0,
                "access-method": "Mac Web",
            },
            "links": {
                "self": "https://api.betatest.degreed.com/api/v2/completions/zrNodlZ"
            },
            "relationships": [
                {"content": {"data": {"id": "zQV15vW", "type": "content"}}},
                {"provider": {"data": {"id": None, "type": "providers"}}},
                {"user": {"data": {"id": "zk3jPZ", "type": "users"}}},
            ],
            "included": [
                {
                    "type": "content",
                    "id": "zQV15vW",
                    "attributes": {
                        "content-type": "Article",
                        "url": "https://www.exitcertified.com/blog/aws-trends-to-watch-for-in-2021?reseller=7",
                        "title": "AWS Trends to Watch for in 2021",
                        "provider": None,
                        "content-duration": 4000.0,
                        "content-duration-type": None,
                        "is-internal": True,
                    },
                    "links": {
                        "self": "https://api.betatest.degreed.com/api/v2/content/zQV15vW"
                    },
                }
            ],
        },
        {
            "type": "completions",
            "id": "zrNodoQ",
            "attributes": {
                "employee-id": None,
                "completed-at": "2022-02-17T00:00:00",
                "added-at": "2022-02-17T09:40:49.81",
                "points-earned": "1.2413333",
                "is-verified": False,
                "rating": 0,
                "access-method": "Mac Web",
            },
            "links": {
                "self": "https://api.betatest.degreed.com/api/v2/completions/zrNodoQ"
            },
            "relationships": [
                {"content": {"data": {"id": "zQV1w6Z", "type": "content"}}},
                {"provider": {"data": {"id": None, "type": "providers"}}},
                {"user": {"data": {"id": "zk3jPZ", "type": "users"}}},
            ],
            "included": [
                {
                    "type": "content",
                    "id": "zQV1w6Z",
                    "attributes": {
                        "content-type": "Article",
                        "url": "https://www.exitcertified.com/blog/the-top-10-programming-languages-in-2021?reseller=7",
                        "title": "The Top 10 Programming Languages in 2021",
                        "provider": None,
                        "content-duration": 7000.0,
                        "content-duration-type": None,
                        "is-internal": True,
                    },
                    "links": {
                        "self": "https://api.betatest.degreed.com/api/v2/content/zQV1w6Z"
                    },
                }
            ],
        },
        {
            "type": "completions",
            "id": "zrz2OWm",
            "attributes": {
                "employee-id": None,
                "completed-at": "2022-03-01T00:00:00",
                "added-at": "2022-03-01T14:10:09.077",
                "points-earned": "0.6206667",
                "is-verified": False,
                "rating": 0,
                "access-method": "Mac Web",
            },
            "links": {
                "self": "https://api.betatest.degreed.com/api/v2/completions/zrz2OWm"
            },
            "relationships": [
                {"content": {"data": {"id": "zQV100Q", "type": "content"}}},
                {"provider": {"data": {"id": None, "type": "providers"}}},
                {"user": {"data": {"id": "zk3jPZ", "type": "users"}}},
            ],
            "included": [
                {
                    "type": "content",
                    "id": "zQV100Q",
                    "attributes": {
                        "content-type": "Article",
                        "url": "https://www.goskills.com/Soft-Skills/Resources/Business-skills-list?utm_source=degreed",
                        "title": "Business Skills List: Top Skills to Thrive in Any Workplace",
                        "provider": None,
                        "content-duration": 3500.0,
                        "content-duration-type": None,
                        "is-internal": True,
                    },
                    "links": {
                        "self": "https://api.betatest.degreed.com/api/v2/content/zQV100Q"
                    },
                }
            ],
        },
    ]
    return data
