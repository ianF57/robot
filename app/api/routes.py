from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.api.schemas import DashboardResponse, ReplayResponse
from app.features.research_service import research_service
from config import settings

router = APIRouter()
templates = Jinja2Templates(directory="app/ui/templates")


@router.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request, "title": settings.app_name})


@router.get("/api/dashboard", response_model=DashboardResponse)
async def dashboard(timeframe: str = Query(default=settings.default_timeframe)) -> DashboardResponse:
    return await research_service.dashboard(settings.default_assets, timeframe)


@router.get("/api/replay", response_model=ReplayResponse)
async def replay(
    asset: str = Query(default="BTCUSDT"),
    timeframe: str = Query(default=settings.default_timeframe),
    at: datetime = Query(..., description="ISO-8601 timestamp"),
) -> ReplayResponse:
    return await research_service.historical_replay(asset, timeframe, at)
