# LocalStudy

Учебный full-stack проект: адаптивный трекер обучения с каталогом курсов,
персональным планом, календарём занятий, практикой и аналитикой.

Проект содержит ровно **25 прикладных HTTP-операций** — по пять на каждый
модуль. Полный перечень находится в [docs/api-contract.md](docs/api-contract.md).
Технический `GET /health` в это количество не входит.

## Структура

```text
localstudy/
├── backend/     # FastAPI, Dishka, async SQLAlchemy, Alembic, Pytest
├── frontend/    # Vue 3, TypeScript, Vite, Pinia, shadcn-vue, Tailwind CSS 4
└── docs/        # границы продукта, архитектура и API-контракт
```

Backend следует направлению зависимостей `api -> application -> domain`, а
инфраструктура реализует порты приложения. Frontend разделён на bootstrap в
`app`, маршрутные модули в `pages` и переиспользуемые части в `shared`.

Авторизации пока нет. Приватные шаблонные пакеты авторизации, логгирования и
общих backend-контрактов не используются. Логирование, ошибки и response
envelope реализованы внутри проекта.

## Быстрый запуск в Windows PowerShell

Требуются Python 3.11+ и Node.js 20.19+.

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
python run.py
```

API будет доступен на `http://127.0.0.1:8000`, Swagger UI — на
`http://127.0.0.1:8000/docs`. При первом запуске создаётся локальная SQLite БД
с детерминированными демонстрационными данными.

### Frontend

Во втором терминале:

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

Интерфейс будет доступен на `http://127.0.0.1:5173`. Dev-server проксирует
`/api` и `/health` на backend.

## Проверки

```powershell
cd backend
python -m ruff format --check .
python -m ruff check .
python -m pytest -q
python -m mypy

cd ..\frontend
npm.cmd run lint
npm.cmd run format:check
npm.cmd run typecheck
npm.cmd run check:api-contract
npm.cmd run build
```

## Данные и ограничения первой версии

- Первый вход начинается с настройки цели, недельного времени и стартового
  курса; демонстрационный план не выдаётся за план пользователя.
- В API v1 намеренно нет операции чтения активного плана. Созданный план
  сохраняется в браузере версионированным снимком и при следующем открытии
  проверяется через прогноз; устаревший идентификатор с ответом 404 удаляется.
- Рекомендации строятся на прозрачных правилах, без ML.
- SQLite выбран для локального обучения; repository port позволяет позже
  заменить адаптер хранения.
