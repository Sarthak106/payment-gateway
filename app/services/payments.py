from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import Merchant, Payment, PaymentStatus, Wallet
from app.services.wallets import generate_wallet_address

DEFAULT_EXPIRATION_MINUTES = 30


async def create_payment(
    session: AsyncSession,
    merchant_api_key: str,
    amount: float,
    mnemonic: str,
) -> Payment:
    merchant = (
        await session.execute(select(Merchant).where(Merchant.api_key == merchant_api_key))
    ).scalar_one_or_none()
    if not merchant or not merchant.is_active:
        raise ValueError("Invalid merchant API key")
    if amount < float(merchant.min_amount) or amount > float(merchant.max_amount):
        raise ValueError("Amount outside merchant limits")

    wallet = await generate_wallet_address(session, mnemonic=mnemonic, is_hot=True)
    payment = Payment(
        merchant_id=merchant.id,
        wallet_id=wallet.id,
        amount=amount,
        status=PaymentStatus.created,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=DEFAULT_EXPIRATION_MINUTES),
    )
    session.add(payment)
    await session.flush()
    return payment


async def get_payment(session: AsyncSession, payment_id: int) -> Payment | None:
    return (
        await session.execute(select(Payment).where(Payment.id == payment_id))
    ).scalar_one_or_none()


async def mark_payment_expired(session: AsyncSession, payment: Payment) -> None:
    if payment.status in {PaymentStatus.completed, PaymentStatus.confirmed}:
        return
    payment.status = PaymentStatus.expired
    await session.flush()


async def set_payment_pending(session: AsyncSession, payment: Payment) -> None:
    if payment.status == PaymentStatus.created:
        payment.status = PaymentStatus.pending
        await session.flush()


async def set_payment_confirmed(session: AsyncSession, payment: Payment) -> None:
    if payment.status in {PaymentStatus.pending, PaymentStatus.created}:
        payment.status = PaymentStatus.confirmed
        await session.flush()


async def set_payment_completed(session: AsyncSession, payment: Payment) -> None:
    if payment.status != PaymentStatus.completed:
        payment.status = PaymentStatus.completed
        await session.flush()
