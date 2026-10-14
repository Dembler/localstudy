# Архитектура LocalStudy

## Backend

```text
HTTP request
    |
    v
api/routers + schemas
    |
    v
application/LearningService
    |
    v
application/LearningRepository (port)
    ^
    |
infrastructure/SqlAlchemyLearningRepository
    |
    v
SQLite / другой SQLAlchemy backend
```

- `src/domain` содержит сущности, статусы и прикладные исключения без FastAPI и
  SQLAlchemy.
- `src/application` содержит DTO, порт репозитория и сценарии пяти модулей.
- `src/api` отвечает за HTTP, Dishka wiring, конфигурацию, middleware и единый
  формат ошибок.
- `src/infrastructure` содержит модели SQLAlchemy, repository adapter,
  миграции, seed и собственный JSON-логгер.
- Сессия БД, repository и service имеют request scope; engine и session factory
  — application scope.

Авторизация будет добавлена отдельным boundary. Прикладные сервисы не должны
получать или разбирать токены напрямую.

## Frontend

```text
src/
├── app/        # bootstrap, Router, глобальная монохромная тема
├── components/ # локальные исходники компонентов shadcn-vue
├── lib/        # утилиты shadcn-vue
├── pages/      # Plan, Catalog, Sessions, Practice, Analytics
└── shared/
    ├── api/   # типизированные 25 операций и единый HTTP client
    ├── stores/# глобальный Pinia store учебного workspace
    ├── data/  # явно помеченные демонстрационные данные
    └── ui/    # переиспользуемые UI primitives
```

- Компоненты не вызывают `fetch` напрямую.
- UI построен на shadcn-vue (Reka UI) и Tailwind CSS 4; компоненты хранятся в
  репозитории и используют только нейтральную чёрно-бело-серую палитру.
- Каждый рабочий экран имеет одно основное действие.
- Расписание в интерфейсе отфильтровывается по идентификатору активного плана.
- Следующее практическое задание запрашивается с `plan_id` и выбирается только из уроков,
  входящих в маршрут плана, включая обязательные курсы-основы.
- `/` перенаправляет на `/plan`.
- На ширине до 760 px sidebar заменяется нижней навигацией, а контент получает
  безопасный нижний отступ.
- Демо-данные никогда не маскируются под серверные: интерфейс показывает
  отдельное уведомление.

## Собственные общие механизмы

- Все успешные ответы имеют envelope `{status, data}`.
- Все ошибки, включая 404/405/422, имеют envelope
  `{status, error: {code, message, details, request_id}}`.
- Request middleware принимает или генерирует `X-Request-ID` и пишет
  структурный JSON-лог стандартными средствами Python.
- Прогресс курса считается по уникальным завершённым урокам и их канонической
  длительности; фактическое учебное время считается отдельно.
