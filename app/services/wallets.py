from bip_utils import Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import encrypt_secret
from app.models.entities import Wallet


async def generate_wallet_address(session: AsyncSession, mnemonic: str, is_hot: bool) -> Wallet:
    result = await session.execute(select(func.max(Wallet.derivation_index)))
    last_index = result.scalar() or 0
    derivation_index = last_index + 1

    seed_bytes = Bip39SeedGenerator(mnemonic).Generate()
    bip44_mst = Bip44.FromSeed(seed_bytes, Bip44Coins.TRON)
    bip44_acc = bip44_mst.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT)
    bip44_addr = bip44_acc.AddressIndex(derivation_index)

    address = bip44_addr.PublicKey().ToAddress()
    private_key = bip44_addr.PrivateKey().Raw().ToHex()
    encrypted_private_key = encrypt_secret(private_key)

    wallet = Wallet(
        address=address,
        encrypted_private_key=encrypted_private_key,
        derivation_index=derivation_index,
        is_hot=is_hot,
        is_active=True,
    )
    session.add(wallet)
    await session.flush()
    return wallet
