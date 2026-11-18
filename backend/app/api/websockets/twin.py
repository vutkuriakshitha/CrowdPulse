import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.application.use_cases.evaluate_risk import EvaluateVenueRiskUseCase

twin_ws_router = APIRouter()


@twin_ws_router.websocket("/ws/twin")
async def twin_ws(websocket: WebSocket):
    await websocket.accept()
    uc = EvaluateVenueRiskUseCase()
    try:
        while True:
            payload = uc.execute()
            await websocket.send_text(json.dumps(payload, default=str))
            await asyncio.sleep(3)
    except WebSocketDisconnect:
        return
