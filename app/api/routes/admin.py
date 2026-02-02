from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin, get_db
from app.models.entities import BlacklistedAddress, Payment
from app.schemas.admin import BlacklistRequest, SweepRequest
from app.services.audit import log_audit
from app.services.sweep import sweep_hot_wallets

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/payments")
async def list_payments(
    session: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_admin),
):
    payments = (await session.execute(select(Payment))).scalars().all()
    return [
        {
            "id": payment.id,
            "amount": float(payment.amount),
            "status": payment.status.value,
            "wallet_id": payment.wallet_id,
            "expires_at": payment.expires_at,
        }
        for payment in payments
    ]


@router.post("/sweep-to-cold-wallet")
async def sweep_to_cold_wallet(
    payload: SweepRequest,
    session: AsyncSession = Depends(get_db),
    admin: str = Depends(get_current_admin),
):
    if not payload.max_amount:
        payload.max_amount = None

    result = await sweep_hot_wallets(session, payload.max_amount)
    await log_audit(session, actor=admin, action="sweep_to_cold", details=str(result))
    await session.commit()
    return result


@router.post("/blacklist-address")
async def blacklist_address(
    payload: BlacklistRequest,
    session: AsyncSession = Depends(get_db),
    admin: str = Depends(get_current_admin),
):
    existing = (
        await session.execute(
            select(BlacklistedAddress).where(BlacklistedAddress.address == payload.address)
        )
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Address already blacklisted")

    entry = BlacklistedAddress(address=payload.address, reason=payload.reason)
    session.add(entry)
    await log_audit(session, actor=admin, action="blacklist", details=payload.address)
    await session.commit()
    return {"status": "blacklisted"}
