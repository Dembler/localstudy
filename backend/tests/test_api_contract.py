from src.api.main import create_app
from src.api.settings import Settings

EXPECTED_BUSINESS_ROUTES = {
    ("GET", "/api/v1/courses"),
    ("GET", "/api/v1/courses/search"),
    ("GET", "/api/v1/courses/{course_id}"),
    ("GET", "/api/v1/courses/{course_id}/prerequisites"),
    ("GET", "/api/v1/lessons/{lesson_id}/preview"),
    ("POST", "/api/v1/plans"),
    ("PATCH", "/api/v1/plans/{plan_id}/workload"),
    ("POST", "/api/v1/plans/{plan_id}/goals"),
    ("POST", "/api/v1/plans/{plan_id}/rebalance"),
    ("GET", "/api/v1/plans/{plan_id}/forecast"),
    ("DELETE", "/api/v1/plans/{plan_id}"),
    ("DELETE", "/api/v1/plans/{plan_id}/goals/{goal_id}"),
    ("DELETE", "/api/v1/plans/{plan_id}/courses/{course_id}"),
    ("GET", "/api/v1/sessions/calendar"),
    ("POST", "/api/v1/sessions"),
    ("POST", "/api/v1/sessions/{session_id}/start"),
    ("POST", "/api/v1/sessions/{session_id}/complete"),
    ("POST", "/api/v1/sessions/{session_id}/reschedule"),
    ("DELETE", "/api/v1/sessions/{session_id}"),
    ("GET", "/api/v1/practice/next"),
    ("POST", "/api/v1/practice/assignments/{assignment_id}/attempts"),
    ("POST", "/api/v1/practice/assignments/{assignment_id}/hint"),
    ("POST", "/api/v1/practice/assignments/{assignment_id}/retry"),
    ("GET", "/api/v1/practice/assignments/{assignment_id}/attempts"),
    ("GET", "/api/v1/analytics/overview"),
    ("GET", "/api/v1/analytics/skills"),
    ("GET", "/api/v1/analytics/streak"),
    ("GET", "/api/v1/analytics/weak-topics"),
    ("GET", "/api/v1/analytics/recommendations"),
}


def test_exactly_29_business_routes() -> None:
    app = create_app(Settings(app_env="test", log_level="WARNING"))
    actual = {
        (method.upper(), path)
        for path, operations in app.openapi()["paths"].items()
        if path.startswith("/api/v1")
        for method in operations
        if method in {"get", "post", "put", "patch", "delete", "head", "options"}
    }

    assert len(actual) == 29
    assert actual == EXPECTED_BUSINESS_ROUTES


def test_health_is_technical_and_hidden_from_openapi(client) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert "/health" not in client.get("/openapi.json").json()["paths"]
