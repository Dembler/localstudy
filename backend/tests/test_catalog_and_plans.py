from datetime import date, timedelta


def test_catalog_search_detail_prerequisites_and_preview(client) -> None:
    listing = client.get("/api/v1/courses", params={"level": "beginner"})
    assert listing.status_code == 200
    assert listing.json()["data"]["total"] == 2
    assert {item["lesson_count"] for item in listing.json()["data"]["items"]} == {2}

    search = client.get("/api/v1/courses/search", params={"q": "FastAPI"})
    assert search.status_code == 200
    assert search.json()["data"]["items"][0]["id"] == "course-fastapi-services"

    detail = client.get("/api/v1/courses/course-python-foundations")
    assert detail.json()["data"]["lesson_count"] == 2

    prerequisites = client.get("/api/v1/courses/course-fastapi-services/prerequisites").json()["data"]
    assert [item["id"] for item in prerequisites["items"]] == [
        "course-learning-basics",
        "course-python-foundations",
    ]

    preview = client.get("/api/v1/lessons/lesson-python-values/preview")
    assert preview.status_code == 200
    assert "переменная" in preview.json()["data"]["preview"].lower()


def test_create_plan_adds_transitive_prerequisites_and_supports_management(client) -> None:
    response = client.post(
        "/api/v1/plans",
        json={
            "name": "My API path",
            "weekly_minutes": 180,
            "start_date": str(date.today()),
            "course_ids": ["course-fastapi-services"],
        },
    )
    assert response.status_code == 201
    plan = response.json()["data"]
    assert plan["course_ids"] == [
        "course-learning-basics",
        "course-python-foundations",
        "course-fastapi-services",
    ]

    workload = client.patch(f"/api/v1/plans/{plan['id']}/workload", json={"weekly_minutes": 300})
    assert workload.json()["data"]["weekly_minutes"] == 300

    goal = client.post(
        f"/api/v1/plans/{plan['id']}/goals",
        json={
            "title": "Finish the path",
            "target_date": str(date.today() + timedelta(days=30)),
            "target_minutes": 500,
        },
    )
    assert goal.status_code == 201
    assert goal.json()["data"]["progress_percent"] == 0

    forecast = client.get(f"/api/v1/plans/{plan['id']}/forecast")
    assert forecast.status_code == 200
    assert forecast.json()["data"]["weekly_minutes"] == 300


def test_missing_course_uses_stable_error_envelope(client) -> None:
    response = client.get("/api/v1/courses/missing-course", headers={"X-Request-ID": "test-request"})
    assert response.status_code == 404
    assert response.json() == {
        "status": "error",
        "error": {
            "code": "not_found",
            "message": "Курс не найден",
            "details": {"course_id": "missing-course"},
            "request_id": "test-request",
        },
    }


def test_invalid_payload_uses_same_error_envelope(client) -> None:
    response = client.post(
        "/api/v1/plans",
        json={"name": "x", "weekly_minutes": 5, "course_ids": []},
    )
    assert response.status_code == 422
    body = response.json()
    assert body["status"] == "error"
    assert body["error"]["code"] == "request_validation"
    assert body["error"]["details"]


def test_framework_errors_use_same_error_envelope(client) -> None:
    missing = client.get("/api/v1/not-a-route", headers={"X-Request-ID": "missing-request"})
    assert missing.status_code == 404
    assert missing.json() == {
        "status": "error",
        "error": {
            "code": "not_found",
            "message": "Ресурс не найден",
            "details": {},
            "request_id": "missing-request",
        },
    }

    wrong_method = client.put("/api/v1/courses", headers={"X-Request-ID": "method-request"})
    assert wrong_method.status_code == 405
    assert wrong_method.json()["error"] == {
        "code": "method_not_allowed",
        "message": "Метод не поддерживается",
        "details": {},
        "request_id": "method-request",
    }


def test_openapi_documents_custom_validation_error(client) -> None:
    operation = client.get("/openapi.json").json()["paths"]["/api/v1/plans"]["post"]
    schema = operation["responses"]["422"]["content"]["application/json"]["schema"]
    assert schema == {"$ref": "#/components/schemas/ErrorResponse"}
