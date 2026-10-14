from datetime import UTC, date, datetime, timedelta


def _create_plan(client, course_id: str = "course-python-foundations") -> dict:
    response = client.post(
        "/api/v1/plans",
        json={
            "name": "Temporary plan",
            "weekly_minutes": 180,
            "start_date": str(date.today()),
            "course_ids": [course_id],
        },
    )
    assert response.status_code == 201
    return response.json()["data"]


def test_delete_goal_and_plan_with_dependent_data(client) -> None:
    plan = _create_plan(client)
    goal = client.post(
        f"/api/v1/plans/{plan['id']}/goals",
        json={
            "title": "Finish",
            "target_date": str(date.today() + timedelta(days=30)),
            "target_minutes": 120,
        },
    ).json()["data"]
    session = client.post(
        "/api/v1/sessions",
        json={
            "plan_id": plan["id"],
            "lesson_id": "lesson-python-functions",
            "scheduled_for": (datetime.now(UTC) + timedelta(days=2)).isoformat(),
            "duration_minutes": 45,
        },
    ).json()["data"]

    deleted_goal = client.delete(f"/api/v1/plans/{plan['id']}/goals/{goal['id']}")
    assert deleted_goal.status_code == 204
    assert client.delete(f"/api/v1/plans/{plan['id']}/goals/{goal['id']}").status_code == 404

    deleted_plan = client.delete(f"/api/v1/plans/{plan['id']}")
    assert deleted_plan.status_code == 204
    assert client.get(f"/api/v1/plans/{plan['id']}/forecast").status_code == 404
    assert client.delete(f"/api/v1/sessions/{session['id']}").status_code == 404
    assert client.delete(f"/api/v1/plans/{plan['id']}").status_code == 404


def test_remove_course_preserves_plan_invariants(client) -> None:
    required = client.delete("/api/v1/plans/demo-plan/courses/course-learning-basics")
    assert required.status_code == 409

    removed = client.delete("/api/v1/plans/demo-plan/courses/course-fastapi-services")
    assert removed.status_code == 204
    assert client.delete("/api/v1/sessions/demo-session-later").status_code == 404

    rejected_session = client.post(
        "/api/v1/sessions",
        json={
            "plan_id": "demo-plan",
            "lesson_id": "lesson-api-contracts",
            "scheduled_for": (datetime.now(UTC) + timedelta(days=2)).isoformat(),
            "duration_minutes": 45,
        },
    )
    assert rejected_session.status_code == 409

    single_course_plan = _create_plan(client, "course-learning-basics")
    last_course = client.delete(f"/api/v1/plans/{single_course_plan['id']}/courses/course-learning-basics")
    assert last_course.status_code == 409


def test_delete_only_planned_session(client) -> None:
    deleted = client.delete("/api/v1/sessions/demo-session-next")
    assert deleted.status_code == 204
    assert client.delete("/api/v1/sessions/demo-session-next").status_code == 404

    completed = client.delete("/api/v1/sessions/demo-session-completed")
    assert completed.status_code == 409
    assert completed.json()["error"]["code"] == "invalid_state"
