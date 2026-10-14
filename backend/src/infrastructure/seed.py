from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.domain.entities import CourseLevel, SessionStatus
from src.infrastructure.models import (
    AssignmentModel,
    AttemptModel,
    CourseModel,
    LessonModel,
    PlanModel,
    SessionModel,
)

STUDY_PLAN_PREVIEW = " ".join(
    [
        "Сначала оцените доступное время: выделите регулярные учебные блоки",
        "и оставьте место для восстановления.",
    ]
)
FUNCTIONS_PREVIEW = " ".join(
    [
        "Небольшая функция должна решать одну задачу, а её сигнатура —",
        "явно описывать входные и выходные данные.",
    ]
)
API_CONTRACTS_PREVIEW = " ".join(
    [
        "Коды статусов, валидация и схемы ответов образуют контракт,",
        "на который могут полагаться клиенты API.",
    ]
)
REPOSITORY_PREVIEW = " ".join(
    [
        "Сервисы приложения зависят от интерфейсов репозитория,",
        "а адаптеры реализуют детали хранения данных.",
    ]
)


async def seed_demo_data(session_factory: async_sessionmaker[AsyncSession]) -> None:
    async with session_factory() as session:
        courses = [
            CourseModel(
                id="course-learning-basics",
                slug="learning-basics",
                title="Как учиться системно",
                description="Выстройте устойчивую систему обучения с активным воспроизведением и рефлексией.",
                level=CourseLevel.BEGINNER,
                duration_minutes=180,
                skills=["Планирование обучения", "Рефлексия", "Память"],
                prerequisite_ids=[],
            ),
            CourseModel(
                id="course-python-foundations",
                slug="python-foundations",
                title="Основы Python",
                description="Освойте синтаксис Python, управление потоком, функции и практическую отладку.",
                level=CourseLevel.BEGINNER,
                duration_minutes=300,
                skills=["Python", "Алгоритмы", "Отладка"],
                prerequisite_ids=["course-learning-basics"],
            ),
            CourseModel(
                id="course-fastapi-services",
                slug="fastapi-services",
                title="Разработка сервисов на FastAPI",
                description="Проектируйте типизированные API с валидацией, хранением данных и тестами.",
                level=CourseLevel.INTERMEDIATE,
                duration_minutes=360,
                skills=["FastAPI", "Проектирование API", "Тестирование"],
                prerequisite_ids=["course-python-foundations"],
            ),
        ]
        lessons = [
            LessonModel(
                id="lesson-retrieval-practice",
                course_id="course-learning-basics",
                title="Практика активного воспроизведения",
                summary="Замените перечитывание активным воспроизведением.",
                preview=(
                    "Объясните идею, не заглядывая в конспект, затем сравните ответ и исправьте неточности."
                ),
                duration_minutes=45,
                position=1,
            ),
            LessonModel(
                id="lesson-study-plan",
                course_id="course-learning-basics",
                title="Реалистичный учебный план",
                summary="Превратите цель в устойчивое недельное расписание.",
                preview=STUDY_PLAN_PREVIEW,
                duration_minutes=60,
                position=2,
            ),
            LessonModel(
                id="lesson-python-values",
                course_id="course-python-foundations",
                title="Значения и переменные",
                summary="Представляйте данные и давайте им понятные имена.",
                preview="Переменная связывает имя со значением, а тип определяет допустимые операции.",
                duration_minutes=50,
                position=1,
            ),
            LessonModel(
                id="lesson-python-functions",
                course_id="course-python-foundations",
                title="Функции и контракты",
                summary="Выделяйте переиспользуемое поведение с явными входами и выходами.",
                preview=FUNCTIONS_PREVIEW,
                duration_minutes=70,
                position=2,
            ),
            LessonModel(
                id="lesson-api-contracts",
                course_id="course-fastapi-services",
                title="Контракты API",
                summary="Проектируйте предсказуемые HTTP-границы.",
                preview=API_CONTRACTS_PREVIEW,
                duration_minutes=80,
                position=1,
            ),
            LessonModel(
                id="lesson-repository-boundary",
                course_id="course-fastapi-services",
                title="Границы репозитория",
                summary="Отделяйте хранение данных от решений прикладного сценария.",
                preview=REPOSITORY_PREVIEW,
                duration_minutes=90,
                position=2,
            ),
        ]
        now = datetime.now(UTC).replace(tzinfo=None)
        plan = PlanModel(
            id="demo-plan",
            name="Траектория серверного разработчика",
            weekly_minutes=240,
            start_date=date.today() - timedelta(days=7),
            course_ids=[
                "course-learning-basics",
                "course-python-foundations",
                "course-fastapi-services",
            ],
            created_at=now - timedelta(days=7),
        )
        sessions = [
            SessionModel(
                id="demo-session-completed",
                plan_id="demo-plan",
                lesson_id="lesson-retrieval-practice",
                scheduled_for=now - timedelta(days=1),
                duration_minutes=45,
                status=SessionStatus.COMPLETED,
                started_at=now - timedelta(days=1, minutes=45),
                completed_at=now - timedelta(days=1),
                score=88,
            ),
            SessionModel(
                id="demo-session-next",
                plan_id="demo-plan",
                lesson_id="lesson-python-values",
                scheduled_for=now + timedelta(days=1),
                duration_minutes=50,
                status=SessionStatus.PLANNED,
            ),
            SessionModel(
                id="demo-session-later",
                plan_id="demo-plan",
                lesson_id="lesson-api-contracts",
                scheduled_for=now + timedelta(days=3),
                duration_minutes=80,
                status=SessionStatus.PLANNED,
            ),
        ]
        assignments = [
            AssignmentModel(
                id="assignment-active-recall",
                lesson_id="lesson-retrieval-practice",
                topic="Память",
                prompt="Как называется практика воспроизведения информации без обращения к источнику?",
                hint="Это практика воспроизведения материала без обращения к источнику.",
                expected_answer="активное воспроизведение",
                difficulty=1,
                hint_requested=False,
            ),
            AssignmentModel(
                id="assignment-python-type",
                lesson_id="lesson-python-values",
                topic="Типы Python",
                prompt="Какой встроенный тип Python хранит значения истина или ложь?",
                hint="Его название начинается с буквы b.",
                expected_answer="bool",
                difficulty=1,
                hint_requested=False,
            ),
            AssignmentModel(
                id="assignment-http-created",
                lesson_id="lesson-api-contracts",
                topic="Семантика HTTP",
                prompt="Какой код состояния HTTP означает, что ресурс был создан?",
                hint="Он относится к семейству 2xx и заканчивается на 01.",
                expected_answer="201",
                difficulty=2,
                hint_requested=False,
            ),
        ]
        attempts = [
            AttemptModel(
                id="demo-attempt",
                assignment_id="assignment-http-created",
                answer="200",
                is_correct=False,
                score=35,
                hint_used=False,
                created_at=now - timedelta(hours=2),
            )
        ]
        existing_courses = {item.id: item for item in (await session.scalars(select(CourseModel))).all()}
        for course in courses:
            current_course = existing_courses.get(course.id)
            if current_course is None:
                session.add(course)
                continue
            current_course.slug = course.slug
            current_course.title = course.title
            current_course.description = course.description
            current_course.level = course.level
            current_course.duration_minutes = course.duration_minutes
            current_course.skills = list(course.skills)
            current_course.prerequisite_ids = list(course.prerequisite_ids)
        await session.flush()

        existing_lessons = {item.id: item for item in (await session.scalars(select(LessonModel))).all()}
        for lesson in lessons:
            current_lesson = existing_lessons.get(lesson.id)
            if current_lesson is None:
                session.add(lesson)
                continue
            current_lesson.course_id = lesson.course_id
            current_lesson.title = lesson.title
            current_lesson.summary = lesson.summary
            current_lesson.preview = lesson.preview
            current_lesson.duration_minutes = lesson.duration_minutes
            current_lesson.position = lesson.position
        await session.flush()

        existing_plan = await session.get(PlanModel, plan.id)
        if existing_plan is None:
            session.add(plan)
            await session.flush()
        else:
            existing_plan.name = plan.name

        existing_session_ids = set((await session.scalars(select(SessionModel.id))).all())
        session.add_all([item for item in sessions if item.id not in existing_session_ids])
        await session.flush()

        existing_assignments = {
            item.id: item for item in (await session.scalars(select(AssignmentModel))).all()
        }
        for assignment in assignments:
            current_assignment = existing_assignments.get(assignment.id)
            if current_assignment is None:
                session.add(assignment)
                continue
            current_assignment.lesson_id = assignment.lesson_id
            current_assignment.topic = assignment.topic
            current_assignment.prompt = assignment.prompt
            current_assignment.hint = assignment.hint
            current_assignment.expected_answer = assignment.expected_answer
            current_assignment.difficulty = assignment.difficulty
        await session.flush()

        existing_attempt_ids = set((await session.scalars(select(AttemptModel.id))).all())
        session.add_all([item for item in attempts if item.id not in existing_attempt_ids])
        await session.commit()
