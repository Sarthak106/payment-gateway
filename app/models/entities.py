import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class PaymentStatus(str, enum.Enum):
    created = "CREATED"
    pending = "PENDING"
    confirmed = "CONFIRMED"
    completed = "COMPLETED"
    expired = "EXPIRED"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Merchant(Base):
    __tablename__ = "merchants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    api_key: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    webhook_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    min_amount: Mapped[float] = mapped_column(Numeric(18, 6), default=1)
    max_amount: Mapped[float] = mapped_column(Numeric(18, 6), default=10000)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Wallet(Base):
    __tablename__ = "wallets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    merchant_id: Mapped[int | None] = mapped_column(ForeignKey("merchants.id"))
    address: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    encrypted_private_key: Mapped[str] = mapped_column(Text)
    derivation_index: Mapped[int] = mapped_column(Integer, index=True)
    is_hot: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    merchant: Mapped[Merchant | None] = relationship("Merchant")


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"))
    wallet_id: Mapped[int] = mapped_column(ForeignKey("wallets.id"))
    amount: Mapped[float] = mapped_column(Numeric(18, 6))
    currency: Mapped[str] = mapped_column(String(16), default="USDT")
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus), default=PaymentStatus.created
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    merchant: Mapped[Merchant] = relationship("Merchant")
    wallet: Mapped[Wallet] = relationship("Wallet")


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (UniqueConstraint("tx_hash", name="uq_tx_hash"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    payment_id: Mapped[int | None] = mapped_column(ForeignKey("payments.id"))
    wallet_id: Mapped[int | None] = mapped_column(ForeignKey("wallets.id"))
    tx_hash: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    block_number: Mapped[int] = mapped_column(Integer)
    from_address: Mapped[str] = mapped_column(String(64))
    to_address: Mapped[str] = mapped_column(String(64))
    amount: Mapped[float] = mapped_column(Numeric(18, 6))
    token_contract: Mapped[str] = mapped_column(String(64))
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    payment: Mapped[Payment | None] = relationship("Payment")
    wallet: Mapped[Wallet | None] = relationship("Wallet")


class Webhook(Base):
    __tablename__ = "webhooks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    payment_id: Mapped[int] = mapped_column(ForeignKey("payments.id"))
    status: Mapped[str] = mapped_column(String(32))
    delivered: Mapped[bool] = mapped_column(Boolean, default=False)
    response_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor: Mapped[str] = mapped_column(String(255))
    action: Mapped[str] = mapped_column(String(255))
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class BlacklistedAddress(Base):
    __tablename__ = "blacklisted_addresses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    address: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
