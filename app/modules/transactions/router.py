from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.modules.users.models import User
from app.modules.users.router import get_current_user, get_current_admin
from app.modules.transactions.schemas import DepositRequest, WithdrawRequest, TransferRequest, TransactionResponse
from app.modules.transactions.service import transaction_service

router = APIRouter(prefix="/transactions", tags=["Transactions"])

@router.post("/deposit", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def deposit(
    schema: DepositRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return transaction_service.deposit(db, current_user, schema.account_id, schema.amount, schema.description)

@router.post("/withdraw", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def withdraw(
    schema: WithdrawRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return transaction_service.withdraw(db, current_user, schema.account_id, schema.amount, schema.description)

@router.post("/transfer", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def transfer(
    schema: TransferRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return transaction_service.transfer(db, current_user, schema.source_account_id, schema.destination_account_number, schema.amount, schema.description)

@router.get("/history/{account_id}", response_model=List[TransactionResponse])
def get_transaction_history(
    account_id: int,
    query: Optional[str] = Query(None, description="Search transaction descriptions"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return transaction_service.get_account_statement(db, current_user, account_id, query, skip, limit)

@router.get("/statement/{account_id}/download")
def download_statement(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    url = transaction_service.generate_statement_download_url(db, current_user, account_id)
    return {"download_url": url}

# Admin Endpoints
@router.get("/admin/all", response_model=List[TransactionResponse])
def get_all_transactions(
    query: Optional[str] = Query(None),
    skip: int = Query(0),
    limit: int = Query(100),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    return transaction_service.get_all_transactions(db, query, skip, limit)
