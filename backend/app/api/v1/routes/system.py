"""Day 2 API skeleton root + route catalog."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def api_v1_root():
    return {
        "service": "crowdpulse",
        "version": "1.0.0",
        "level": "A",
        "modules": [
            {"name": "venues", "base": "/api/v1/venues"},
            {"name": "videos", "base": "/api/v1/videos"},
            {"name": "pipeline", "base": "/api/v1/pipeline"},
            {"name": "twin", "base": "/api/v1/twin"},
            {"name": "risk", "base": "/api/v1/risk"},
            {"name": "decisions", "base": "/api/v1/decisions"},
            {"name": "simulation", "base": "/api/v1/simulation"},
            {"name": "analytics", "base": "/api/v1/analytics"},
            {"name": "reports", "base": "/api/v1/reports"},
        ],
        "docs": "/docs",
        "health": "/health",
        "websocket": "/ws/twin",
    }
