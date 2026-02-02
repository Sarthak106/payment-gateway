import asyncio
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tronpy.exceptions import TronError

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.entities import (
    BlacklistedAddress,
    Payment,
    PaymentStatus,
    Transaction,
    Wallet,
)
from app.services.payments import (
    mark_payment_expired,
    set_payment_completed,
    set_payment_confirmed,
    set_payment_pending,
)
from app.services.tron import get_tron_client, get_usdt_contract_address

LAST_SCANNED_BLOCK: int | None = None


async def _load_active_wallets(session: AsyncSession) -> dict[str, Wallet]:
    wallets = (await session.execute(select(Wallet).where(Wallet.is_active.is_(True)))).scalars().all()
    return {wallet.address: wallet for wallet in wallets}


async def _load_blacklist(session: AsyncSession) -> set[str]:
    addresses = (await session.execute(select(BlacklistedAddress.address))).scalars().all()
    return set(addresses)


async def _load_pending_payments(session: AsyncSession) -> dict[int, Payment]:
    payments = (
        await session.execute(
            select(Payment).where(
                Payment.status.in_({PaymentStatus.created, PaymentStatus.pending})
            )
        )
    ).scalars().all()
    return {payment.wallet_id: payment for payment in payments}


async def _mark_expired_payments(session: AsyncSession) -> None:
    now = datetime.now(timezone.utc)
    payments = (
        await session.execute(
            select(Payment).where(
                Payment.status.in_({PaymentStatus.created, PaymentStatus.pending}),
                Payment.expires_at < now,
            )
        )
    ).scalars().all()
    for payment in payments:
        await mark_payment_expired(session, payment)


async def _confirm_transactions(session: AsyncSession, current_block: int) -> None:
    transactions = (
        await session.execute(select(Transaction).where(Transaction.confirmed.is_(False)))
    ).scalars().all()
    for tx in transactions:
        confirmations = current_block - tx.block_number
        if confirmations >= settings.tron_confirmation_blocks:
            tx.confirmed = True
            if tx.payment_id:
                payment = await session.get(Payment, tx.payment_id)
                if payment:
                    await set_payment_confirmed(session, payment)
                    await set_payment_completed(session, payment)


async def poll_tron() -> None:
    global LAST_SCANNED_BLOCK

    tron = get_tron_client()
    contract = tron.get_contract(get_usdt_contract_address())

    while True:
        async with SessionLocal() as session:
            await _mark_expired_payments(session)

            wallets = await _load_active_wallets(session)
            if not wallets:
                await session.commit()
                await asyncio.sleep(5)
                continue

            payments_by_wallet = await _load_pending_payments(session)
            blacklist = await _load_blacklist(session)

            try:
                current_block = tron.get_latest_block_number()
            except TronError:
                await asyncio.sleep(5)
                continue

            await _confirm_transactions(session, current_block)

            if LAST_SCANNED_BLOCK is None:
                LAST_SCANNED_BLOCK = max(current_block - 100, 1)

            from_block = LAST_SCANNED_BLOCK + 1
            to_block = current_block

            if from_block > to_block:
                await asyncio.sleep(5)
                continue

            try:
                events = contract.events.Transfer.get_event_result(
                    from_block=from_block,
                    to_block=to_block,
                    order_by="block_number",
                    limit=200,
                )
            except TronError:
                await asyncio.sleep(5)
                continue

            for event in events:
                result = event.get("result", {})
                to_address = result.get("to")
                from_address = result.get("from")
                if not to_address or to_address not in wallets:
                    continue
                if from_address in blacklist or to_address in blacklist:
                    continue

                tx_hash = event.get("transaction_id")
                block_number = event.get("block_number")
                amount = int(result.get("value", 0)) / 1_000_000

                existing = (
                    await session.execute(
                        select(Transaction).where(Transaction.tx_hash == tx_hash)
                    )
                ).scalar_one_or_none()
                if existing:
                    continue

                wallet = wallets[to_address]
                payment = payments_by_wallet.get(wallet.id)
                if not payment:
                    continue

                transaction = Transaction(
                    payment_id=payment.id,
                    wallet_id=wallet.id,
                    tx_hash=tx_hash,
                    block_number=block_number,
                    from_address=from_address,
                    to_address=to_address,
                    amount=amount,
                    token_contract=get_usdt_contract_address(),
                    confirmed=False,
                )
                session.add(transaction)

                await set_payment_pending(session, payment)

                if amount >= float(payment.amount):
                    confirmations = current_block - block_number
                    if confirmations >= settings.tron_confirmation_blocks:
                        transaction.confirmed = True
                        await set_payment_confirmed(session, payment)
                        await set_payment_completed(session, payment)

            LAST_SCANNED_BLOCK = to_block
            await session.commit()

        await asyncio.sleep(5)
