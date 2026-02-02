from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyUrl, Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "TRON USDT Payment Gateway"
    environment: str = "development"
    api_prefix: str = "/api"
    https_only: bool = True

    database_url: AnyUrl = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/payment_gateway"
    )

    jwt_secret: str = Field(default="change-me")
    jwt_algorithm: str = "HS256"
    jwt_access_token_minutes: int = 15

    encryption_key_b64: str = Field(
        default="",
        description="Base64-encoded 32-byte key for AES-256-GCM encryption",
    )

    tron_network: str = "nile"
    tron_fullnode_url: AnyUrl = Field(default="https://nile.trongrid.io")
    tron_solidity_url: AnyUrl = Field(default="https://nile.trongrid.io")
    tron_event_url: AnyUrl = Field(default="https://nile.trongrid.io")
    tron_confirmation_blocks: int = 20

    usdt_contract_mainnet: str = "TXLAQ63Xg1NAzckPwKHvzw7CSEmLMEqcdj"
    usdt_contract_nile: str = "TXLAQ63Xg1NAzckPwKHvzw7CSEmLMEqcdj"

    hot_wallet_xpub: str = Field(default="")
    hot_wallet_master_encrypted: str = Field(default="")
    cold_wallet_address: str = Field(default="")

    webhook_secret: str = Field(default="change-me")

    rate_limit_requests: int = 60
    rate_limit_window_seconds: int = 60


settings = Settings()
