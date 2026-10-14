# LocalStudy backend

FastAPI backend for an adaptive learning tracker. The code is split into `api`,
`application`, `domain`, and `infrastructure` layers. It has no authentication or
private package dependencies and uses async SQLAlchemy with SQLite by default.

## Run locally

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -e ".[dev]"
copy .env.example .env
python run.py
```

Swagger UI: <http://127.0.0.1:8000/docs>. Health check: `GET /health`.
The database is created and populated with demo courses, lessons, a study plan,
sessions, and practice assignments on first startup.

## Quality checks

```bash
pytest
ruff check .
mypy
```

## Database migrations

The application can bootstrap an empty local SQLite database automatically. For
managed environments, apply the included migration instead:

```bash
alembic upgrade head
```

## Architecture

- `src/api`: HTTP routers, settings, middleware, handlers, DI assembly.
- `src/application`: use-case service, repository port, request/response schemas.
- `src/domain`: entities, enums, and domain exceptions.
- `src/infrastructure`: SQLAlchemy models, repository, logging, demo seed.
- `tests`: route contract and representative behavior/error tests.

The API intentionally has exactly 25 business operations. `/health`, OpenAPI,
Swagger UI, and ReDoc are technical endpoints and are excluded from that count.
