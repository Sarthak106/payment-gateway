from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.security import verify_webhook_signature
from app.models.entities import Webhook
from app.services.audit import log_audit

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/merchant")
async def merchant_webhook_endpoint(
    request: Request,
    session: AsyncSession = Depends(get_db),
    x_signature: str = Header(default=""),
):
    payload = await request.body()
    if not verify_webhook_signature(payload, x_signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    body = await request.json()
    payment_id = body.get("payment_id")
    status = body.get("status")

    webhook = Webhook(payment_id=payment_id, status=status, delivered=True)
    session.add(webhook)
    await log_audit(session, actor="webhook", action="received", details=str(body))
    await session.commit()
    return {"status": "accepted"}
