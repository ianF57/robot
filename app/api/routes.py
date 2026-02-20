from __future__ import annotations

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from config import settings
from app.features.research_service import research_service

router = APIRouter()
templates = Jinja2Templates(directory="app/ui/templates")


@router.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request, "title": settings.app_name})


@router.get("/api/dashboard")
async def dashboard(timeframe: str = Query(default=settings.default_timeframe)) -> dict[str, object]:
    return await research_service.dashboard(settings.default_assets, timeframe)


@router.get("/api/replay")
async def replay(
    asset: str = Query(default="BTCUSDT"),
    timeframe: str = Query(default=settings.default_timeframe),
    at: str = Query(..., description="ISO-8601 timestamp"),
) -> dict[str, object]:
    return await research_service.historical_replay(asset, timeframe, at)
