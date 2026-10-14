"""Initial LocalStudy schema.

Revision ID: 0001
Revises:
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "courses",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("slug", sa.String(100), nullable=False, unique=True),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("level", sa.String(20), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("skills", sa.JSON(), nullable=False),
        sa.Column("prerequisite_ids", sa.JSON(), nullable=False),
    )
    op.create_index("ix_courses_slug", "courses", ["slug"])
    op.create_index("ix_courses_level", "courses", ["level"])
    op.create_table(
        "lessons",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("course_id", sa.String(36), sa.ForeignKey("courses.id"), nullable=False),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("preview", sa.Text(), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
    )
    op.create_index("ix_lessons_course_id", "lessons", ["course_id"])
    op.create_table(
        "study_plans",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("weekly_minutes", sa.Integer(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("course_ids", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "goals",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("plan_id", sa.String(36), sa.ForeignKey("study_plans.id"), nullable=False),
        sa.Column("title", sa.String(120), nullable=False),
        sa.Column("target_date", sa.Date(), nullable=False),
        sa.Column("target_minutes", sa.Integer(), nullable=False),
        sa.Column("progress_percent", sa.Integer(), nullable=False),
    )
    op.create_index("ix_goals_plan_id", "goals", ["plan_id"])
    op.create_table(
        "study_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("plan_id", sa.String(36), sa.ForeignKey("study_plans.id"), nullable=False),
        sa.Column("lesson_id", sa.String(36), sa.ForeignKey("lessons.id"), nullable=False),
        sa.Column("scheduled_for", sa.DateTime(), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("score", sa.Integer(), nullable=True),
    )
    op.create_index("ix_study_sessions_plan_id", "study_sessions", ["plan_id"])
    op.create_index("ix_study_sessions_lesson_id", "study_sessions", ["lesson_id"])
    op.create_index("ix_study_sessions_scheduled_for", "study_sessions", ["scheduled_for"])
    op.create_index("ix_study_sessions_status", "study_sessions", ["status"])
    op.create_table(
        "assignments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("lesson_id", sa.String(36), sa.ForeignKey("lessons.id"), nullable=False),
        sa.Column("topic", sa.String(100), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("hint", sa.Text(), nullable=False),
        sa.Column("expected_answer", sa.Text(), nullable=False),
        sa.Column("difficulty", sa.Integer(), nullable=False),
        sa.Column("hint_requested", sa.Boolean(), nullable=False),
    )
    op.create_index("ix_assignments_lesson_id", "assignments", ["lesson_id"])
    op.create_index("ix_assignments_topic", "assignments", ["topic"])
    op.create_table(
        "attempts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("assignment_id", sa.String(36), sa.ForeignKey("assignments.id"), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("hint_used", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_attempts_assignment_id", "attempts", ["assignment_id"])
    op.create_index("ix_attempts_created_at", "attempts", ["created_at"])


def downgrade() -> None:
    op.drop_table("attempts")
    op.drop_table("assignments")
    op.drop_table("study_sessions")
    op.drop_table("goals")
    op.drop_table("study_plans")
    op.drop_table("lessons")
    op.drop_table("courses")
