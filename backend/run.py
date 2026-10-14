import uvicorn

from src.api.main import create_app
from src.api.settings import get_settings

app = create_app()


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(app, host=settings.host, port=settings.port)
