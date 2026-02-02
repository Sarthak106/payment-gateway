from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tronpy.keys import PrivateKey

from app.core.config import settings
from app.core.security import decrypt_secret
from app.models.entities import Wallet
from app.services.tron import get_tron_client, get_usdt_contract_address


async def sweep_hot_wallets(session: AsyncSession, max_amount: float | None) -> dict:
    if not settings.cold_wallet_address:
        raise ValueError("Cold wallet address not configured")

    tron = get_tron_client()
    contract = tron.get_contract(get_usdt_contract_address())
    wallets = (
        await session.execute(select(Wallet).where(Wallet.is_hot.is_(True), Wallet.is_active.is_(True)))
    ).scalars().all()

    transfers = []
    for wallet in wallets:
        private_key = decrypt_secret(wallet.encrypted_private_key)
        account = tron.get_account(wallet.address)
        _ = account
        balance = contract.functions.balanceOf(wallet.address)
        amount = int(balance)
        if amount <= 0:
            continue
        if max_amount is not None:
            amount = min(amount, int(max_amount * 1_000_000))
        if amount <= 0:
            continue

        tx = (
            contract.functions.transfer(settings.cold_wallet_address, amount)
            .with_owner(wallet.address)
            .fee_limit(10_000_000)
            .build()
            .sign(PrivateKey(bytes.fromhex(private_key)))
        )
        result = tron.broadcast(tx)
        transfers.append({"wallet": wallet.address, "tx_id": result.get("txid")})

    return {"transfers": transfers, "count": len(transfers)}
