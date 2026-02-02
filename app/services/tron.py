from tronpy import Tron
from tronpy.providers import HTTPProvider

from app.core.config import settings


def get_tron_client() -> Tron:
    return Tron(
        provider=HTTPProvider(
            api_key=None,
            full_node=str(settings.tron_fullnode_url),
            solidity_node=str(settings.tron_solidity_url),
            event_server=str(settings.tron_event_url),
        )
    )


def get_usdt_contract_address() -> str:
    if settings.tron_network.lower() == "mainnet":
        return settings.usdt_contract_mainnet
    return settings.usdt_contract_nile


def validate_usdt_contract(contract_address: str) -> bool:
    return contract_address == get_usdt_contract_address()
