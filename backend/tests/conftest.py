from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from src.api.main import create_app
from src.api.settings import Settings


@pytest.fixture()
def client(tmp_path) -> Iterator[TestClient]:
    database_path = tmp_path / "test.db"
    settings = Settings(
        app_env="test",
        database_url=f"sqlite+aiosqlite:///{database_path.as_posix()}",
        log_level="WARNING",
    )
    with TestClient(create_app(settings)) as test_client:
        yield test_client
