"""Decision queue APIs — GB recommendations + Accept/Dismiss (Day 14)."""

from __future__ import annotations

import time
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.decision.ml_recommender import get_action_recommender
from app.api.deps import AuthUser, get_current_user
from app.infrastructure.persistence.database import get_db
from app.infrastructure.persistence.models import AlertModel, DecisionModel
from app.infrastructure.persistence.twin_store import twin_store

router = APIRouter()


class ActionStatusUpdate(BaseModel):
    alert_id: str
    action_type: str
    status: str = Field(..., pattern="^(accepted|dismissed|executed)$")


def _apply_status(alert: dict, body: ActionStatusUpdate, user: AuthUser) -> dict | None:
    for a in alert.get("actions") or []:
        if a.get("action_type") != body.action_type:
            continue
        a["status"] = body.status
        a["acked_by"] = user.username
        a["acked_by_name"] = user.full_name
        a["acked_at"] = time.time()
        return a
    return None


def _sync_decision_store(alert: dict) -> dict:
    aid = str(alert["id"])
    for d in twin_store.decisions:
        if d.get("alert_id") == aid:
            d["actions"] = alert.get("actions") or []
            d["rationale"] = alert.get("rationale") or ""
            d["zone_code"] = alert.get("zone_code")
            return d
    row = {
        "alert_id": aid,
        "zone_code": alert.get("zone_code"),
        "actions": alert.get("actions") or [],
        "rationale": alert.get("rationale") or "",
    }
    twin_store.decisions.insert(0, row)
    return row


@router.get("/recommender/status")
async def recommender_status():
    """Day 11 — Gradient Boosting recommender health + feature importances."""
    rec = get_action_recommender()
    return rec.status()


@router.get("")
async def list_decisions(limit: int = 20):
    return twin_store.decisions[:limit]


@router.post("/ack")
async def ack_action(
    body: ActionStatusUpdate,
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Accept or dismiss a recommended action (control-room operator)."""
    alert = next((a for a in twin_store.alerts if str(a.get("id")) == body.alert_id), None)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found in decision queue")

    updated = _apply_status(alert, body, user)
    if not updated:
        raise HTTPException(status_code=404, detail="Action not found on this alert")

    decision = _sync_decision_store(alert)

    persisted = False
    try:
        alert_uuid = UUID(body.alert_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid alert_id") from exc

    try:
        db_alert = await db.get(AlertModel, alert_uuid)
        if db_alert:
            expl = dict(db_alert.explanation or {})
            expl["actions"] = alert.get("actions") or []
            expl["rationale"] = alert.get("rationale")
            db_alert.explanation = expl
            if body.status == "accepted":
                db_alert.status = "acknowledged"
            elif body.status == "dismissed":
                db_alert.status = "dismissed"
            db.add(
                DecisionModel(
                    id=uuid4(),
                    alert_id=alert_uuid,
                    rationale=f"{body.status} by {user.username}: {alert.get('rationale') or ''}",
                    actions=alert.get("actions") or [],
                )
            )
            await db.commit()
            persisted = True
        else:
            # Live twin alert not yet in DB — twin_store remains source of truth
            await db.rollback()
    except Exception:  # noqa: BLE001
        await db.rollback()
        persisted = False

    return {
        "ok": True,
        "persisted": persisted,
        "action": updated,
        "alert": alert,
        "decision": decision,
        "operator": {"username": user.username, "full_name": user.full_name, "role": user.role},
    }
