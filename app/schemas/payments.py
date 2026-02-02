from datetime import datetime
from pydantic import BaseModel, Field


class PaymentCreateRequest(BaseModel):
    amount: float = Field(gt=0)
    merchant_api_key: str


class PaymentCreateResponse(BaseModel):
    payment_id: int
    address: str
    amount: float
    expires_at: datetime
    status: str


class PaymentStatusResponse(BaseModel):
    payment_id: int
    status: str
    amount: float
    address: str
    expires_at: datetime
