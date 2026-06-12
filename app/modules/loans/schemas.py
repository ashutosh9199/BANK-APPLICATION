from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import date, datetime
from typing import Optional, List
from app.modules.loans.models import LoanType, LoanStatus, EMIStatus

class LoanApplicationRequest(BaseModel):
    loan_type: LoanType
    principal_amount: Decimal = Field(..., gt=0)
    tenure_months: int = Field(..., gt=0, le=360) # Up to 30 years

class LoanDocumentResponse(BaseModel):
    id: int
    loan_id: int
    document_name: str
    document_url: str
    created_at: datetime

    class Config:
        from_attributes = True

class LoanEMIScheduleResponse(BaseModel):
    id: int
    loan_id: int
    installment_number: int
    due_date: date
    emi_amount: Decimal
    principal_component: Decimal
    interest_component: Decimal
    outstanding_principal: Decimal
    status: EMIStatus
    paid_date: Optional[date] = None

    class Config:
        from_attributes = True

class LoanRepaymentResponse(BaseModel):
    id: int
    loan_id: int
    amount_paid: Decimal
    payment_date: datetime
    payment_method: str

    class Config:
        from_attributes = True

class LoanResponse(BaseModel):
    id: int
    user_id: int
    loan_type: LoanType
    principal_amount: Decimal
    interest_rate: Decimal
    tenure_months: int
    emi_amount: Decimal
    status: LoanStatus
    outstanding_balance: Decimal
    comments: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    documents: List[LoanDocumentResponse] = []
    emi_schedule: Optional[List[LoanEMIScheduleResponse]] = []
    repayments: Optional[List[LoanRepaymentResponse]] = []

    class Config:
        from_attributes = True

class LoanReviewRequest(BaseModel):
    status: LoanStatus  # APPROVED or REJECTED
    comments: Optional[str] = None

class LoanRepaymentRequest(BaseModel):
    amount: Decimal = Field(..., gt=0)
