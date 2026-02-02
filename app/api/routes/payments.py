from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.config import settings
from app.models.entities import PaymentStatus, Wallet
from app.schemas.payments import (
    PaymentCreateRequest,
    PaymentCreateResponse,
    PaymentStatusResponse,
)
from app.core.security import decrypt_secret
from app.services.payments import create_payment, get_payment

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/create", response_model=PaymentCreateResponse)
async def create_payment_endpoint(
    payload: PaymentCreateRequest,
    session: AsyncSession = Depends(get_db),
):
    if not settings.hot_wallet_master_encrypted:
        raise HTTPException(status_code=500, detail="Hot wallet not configured")

    try:
        mnemonic = decrypt_secret(settings.hot_wallet_master_encrypted)
        payment = await create_payment(
            session=session,
            merchant_api_key=payload.merchant_api_key,
            amount=payload.amount,
            mnemonic=mnemonic,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    wallet = await session.get(Wallet, payment.wallet_id)
    if not wallet:
        raise HTTPException(status_code=500, detail="Wallet not found")

    await session.commit()
    return PaymentCreateResponse(
        payment_id=payment.id,
        address=wallet.address,
        amount=float(payment.amount),
        expires_at=payment.expires_at,
        status=payment.status.value,
    )


@router.get("/status/{payment_id}", response_model=PaymentStatusResponse)
async def payment_status_endpoint(
    payment_id: int, session: AsyncSession = Depends(get_db)
):
    payment = await get_payment(session, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    wallet = await session.get(Wallet, payment.wallet_id)
    if not wallet:
        raise HTTPException(status_code=500, detail="Wallet not found")

    return PaymentStatusResponse(
        payment_id=payment.id,
        status=payment.status.value,
        amount=float(payment.amount),
        address=wallet.address,
        expires_at=payment.expires_at,
    )
