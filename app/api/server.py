from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from config import settings
from app.api.routes import router


settings.log_path.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=settings.log_path,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)
    app.mount("/static", StaticFiles(directory="app/ui/static"), name="static")
    app.include_router(router)
    return app


app = create_app()
