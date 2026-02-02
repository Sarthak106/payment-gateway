from pydantic import BaseModel, Field


class SweepRequest(BaseModel):
    max_amount: float | None = Field(default=None, gt=0)


class BlacklistRequest(BaseModel):
    address: str
    reason: str | None = None
