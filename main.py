from __future__ import annotations

import threading
import webbrowser

import uvicorn

from config import settings


def _open_browser() -> None:
    webbrowser.open(f"http://{settings.host}:{settings.port}")


def main() -> None:
    if settings.auto_open_browser:
        threading.Timer(1.2, _open_browser).start()
    uvicorn.run("app.api.server:app", host=settings.host, port=settings.port, reload=False)


if __name__ == "__main__":
    main()
