from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime
from typing import Optional
from app.models.transaction import TransactionType

class DepositRequest(BaseModel):
    account_id: int
    amount: Decimal = Field(..., gt=0)
    description: Optional[str] = None

class WithdrawRequest(BaseModel):
    account_id: int
    amount: Decimal = Field(..., gt=0)
    description: Optional[str] = None

class TransferRequest(BaseModel):
    source_account_id: int
    destination_account_number: str = Field(..., min_length=10, max_length=10)
    amount: Decimal = Field(..., gt=0)
    description: Optional[str] = None

class TransactionResponse(BaseModel):
    id: int
    source_account_id: Optional[int] = None
    destination_account_id: Optional[int] = None
    source_account_number: Optional[str] = None
    destination_account_number: Optional[str] = None
    transaction_type: TransactionType
    amount: Decimal
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
