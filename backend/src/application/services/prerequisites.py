from src.application.ports import CatalogReader
from src.application.services.lookups import require_course
from src.domain.entities import Course
from src.domain.exceptions import ConflictError


class PrerequisiteResolver:
    def __init__(self, catalog: CatalogReader) -> None:
        self._catalog = catalog

    async def expand(self, courses: list[Course]) -> list[str]:
        result: list[str] = []
        visiting: set[str] = set()

        async def add(course: Course) -> None:
            if course.id in visiting:
                raise ConflictError("Обнаружен цикл зависимостей между курсами")
            if course.id in result:
                return
            visiting.add(course.id)
            for prerequisite_id in course.prerequisite_ids:
                prerequisite = await require_course(self._catalog, prerequisite_id)
                await add(prerequisite)
            visiting.remove(course.id)
            result.append(course.id)

        for course in courses:
            await add(course)
        return result
