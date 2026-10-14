from datetime import UTC, date, datetime, timedelta


def test_session_lifecycle_and_invalid_transition(client) -> None:
    scheduled = datetime.now(UTC) + timedelta(days=5)
    created = client.post(
        "/api/v1/sessions",
        json={
            "plan_id": "demo-plan",
            "lesson_id": "lesson-python-functions",
            "scheduled_for": scheduled.isoformat(),
            "duration_minutes": 70,
        },
    )
    assert created.status_code == 201
    session_id = created.json()["data"]["id"]

    started = client.post(f"/api/v1/sessions/{session_id}/start")
    assert started.status_code == 200
    assert started.json()["data"]["status"] == "in_progress"

    completed = client.post(f"/api/v1/sessions/{session_id}/complete", json={"score": 91})
    assert completed.status_code == 200
    assert completed.json()["data"]["status"] == "completed"

    invalid = client.post(
        f"/api/v1/sessions/{session_id}/reschedule",
        json={"scheduled_for": (scheduled + timedelta(days=1)).isoformat()},
    )
    assert invalid.status_code == 409
    assert invalid.json()["error"]["code"] == "invalid_state"


def test_calendar_and_rebalance(client) -> None:
    response = client.get(
        "/api/v1/sessions/calendar",
        params={
            "from_date": str(date.today() - timedelta(days=2)),
            "to_date": str(date.today() + timedelta(days=10)),
        },
    )
    assert response.status_code == 200
    assert response.json()["data"]["total"] == 3

    rebalanced = client.post("/api/v1/plans/demo-plan/rebalance")
    assert rebalanced.status_code == 200
    assert rebalanced.json()["data"]["sessions_updated"] == 2


def test_practice_hint_attempt_retry_and_history(client) -> None:
    assignment_id = "assignment-python-type"
    hint = client.post(f"/api/v1/practice/assignments/{assignment_id}/hint")
    assert hint.status_code == 200
    assert hint.json()["data"]["penalty_percent"] == 15

    attempt = client.post(
        f"/api/v1/practice/assignments/{assignment_id}/attempts",
        json={"answer": "bool"},
    )
    assert attempt.status_code == 201
    assert attempt.json()["data"]["is_correct"] is True
    assert attempt.json()["data"]["score"] == 85
    assert attempt.json()["data"]["hint_used"] is True

    second_hint = client.post(f"/api/v1/practice/assignments/{assignment_id}/hint")
    assert second_hint.status_code == 200

    retry = client.post(f"/api/v1/practice/assignments/{assignment_id}/retry")
    assert retry.status_code == 200
    assert retry.json()["data"]["previous_best_score"] == 85

    retried_attempt = client.post(
        f"/api/v1/practice/assignments/{assignment_id}/attempts",
        json={"answer": "bool"},
    )
    assert retried_attempt.status_code == 201
    assert retried_attempt.json()["data"]["score"] == 100
    assert retried_attempt.json()["data"]["hint_used"] is False

    history = client.get(f"/api/v1/practice/assignments/{assignment_id}/attempts")
    assert history.status_code == 200
    assert history.json()["data"]["total"] == 2


def test_next_assignment_is_scoped_to_plan_courses(client) -> None:
    created = client.post(
        "/api/v1/plans",
        json={
            "name": "FastAPI only",
            "weekly_minutes": 180,
            "course_ids": ["course-fastapi-services"],
        },
    )
    assert created.status_code == 201

    response = client.get(
        "/api/v1/practice/next",
        params={
            "plan_id": created.json()["data"]["id"],
            "course_id": "course-fastapi-services",
        },
    )

    assert response.status_code == 200
    assert response.json()["data"]["lesson_id"] == "lesson-api-contracts"

    unrelated_course = client.get(
        "/api/v1/practice/next",
        params={
            "plan_id": created.json()["data"]["id"],
            "course_id": "course-sql-analytics",
        },
    )
    assert unrelated_course.status_code == 409

    missing_plan = client.get(
        "/api/v1/practice/next",
        params={"course_id": "course-fastapi-services"},
    )
    assert missing_plan.status_code == 422

    basics = client.post(
        "/api/v1/plans",
        json={
            "name": "Learning basics only",
            "weekly_minutes": 180,
            "course_ids": ["course-learning-basics"],
        },
    )
    basics_response = client.get(
        "/api/v1/practice/next",
        params={"plan_id": basics.json()["data"]["id"]},
    )
    assert basics_response.json()["data"]["lesson_id"] in {
        "lesson-retrieval-practice",
        "lesson-study-plan",
    }


def test_numeric_answer_accepts_a_trailing_status_phrase(client) -> None:
    response = client.post(
        "/api/v1/practice/assignments/assignment-http-created/attempts",
        json={"answer": "201 Created"},
    )

    assert response.status_code == 201
    assert response.json()["data"]["is_correct"] is True
    assert response.json()["data"]["score"] == 100

    contradictory = client.post(
        "/api/v1/practice/assignments/assignment-http-created/attempts",
        json={"answer": "201 404"},
    )
    assert contradictory.status_code == 201
    assert contradictory.json()["data"]["is_correct"] is False


def test_analytics_endpoints_return_meaningful_demo_data(client) -> None:
    overview = client.get("/api/v1/analytics/overview")
    assert overview.status_code == 200
    assert overview.json()["data"]["courses_in_plan"] == 3
    assert overview.json()["data"]["completed_sessions"] == 1

    skills = client.get("/api/v1/analytics/skills")
    assert skills.status_code == 200
    assert any(item["skill"] == "Python" for item in skills.json()["data"]["items"])

    streak = client.get("/api/v1/analytics/streak")
    assert streak.status_code == 200
    assert streak.json()["data"]["last_study_date"] is not None

    weak_topics = client.get("/api/v1/analytics/weak-topics")
    assert weak_topics.status_code == 200
    assert weak_topics.json()["data"]["items"][0]["topic"] == "Семантика HTTP"

    recommendations = client.get("/api/v1/analytics/recommendations")
    assert recommendations.status_code == 200
    assert recommendations.json()["data"]["items"]


def test_duplicate_long_session_does_not_inflate_curriculum_progress(client) -> None:
    before_forecast = client.get("/api/v1/plans/demo-plan/forecast").json()["data"]
    before_overview = client.get("/api/v1/analytics/overview").json()["data"]

    scheduled = datetime.now(UTC) + timedelta(days=8)
    created = client.post(
        "/api/v1/sessions",
        json={
            "plan_id": "demo-plan",
            "lesson_id": "lesson-retrieval-practice",
            "scheduled_for": scheduled.isoformat(),
            "duration_minutes": 480,
        },
    )
    session_id = created.json()["data"]["id"]
    assert client.post(f"/api/v1/sessions/{session_id}/start").status_code == 200
    assert client.post(f"/api/v1/sessions/{session_id}/complete", json={"score": 100}).status_code == 200

    after_forecast = client.get("/api/v1/plans/demo-plan/forecast").json()["data"]
    after_overview = client.get("/api/v1/analytics/overview").json()["data"]

    assert after_forecast["remaining_minutes"] == before_forecast["remaining_minutes"]
    assert after_overview["completion_percent"] == before_overview["completion_percent"]
    assert after_overview["study_minutes"] == before_overview["study_minutes"] + 480
