from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime
from app.models.account import AccountType, AccountStatus

class AccountCreate(BaseModel):
    account_type: AccountType

class AccountResponse(BaseModel):
    id: int
    user_id: int
    account_number: str
    account_type: AccountType
    balance: Decimal
    status: AccountStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class AccountStatusUpdate(BaseModel):
    status: AccountStatus
