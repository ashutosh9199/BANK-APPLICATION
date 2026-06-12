from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.modules.users.models import User
from app.modules.users.router import get_current_user, get_current_admin
from app.modules.accounts.schemas import AccountCreate, AccountResponse, AccountStatusUpdate
from app.modules.accounts.service import account_service

router = APIRouter(prefix="/accounts", tags=["Accounts"])

@router.post("/", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
def create_account(
    schema: AccountCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return account_service.create_account(db, current_user, schema.account_type)

@router.get("/my-accounts", response_model=List[AccountResponse])
def get_my_accounts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return account_service.get_user_accounts(db, current_user.id)

@router.get("/{account_id}", response_model=AccountResponse)
def get_account_details(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    account = account_service.get_account_by_id(db, account_id)
    # Check authorization
    if account.user_id != current_user.id and current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this account."
        )
    return account

# Admin Endpoints
@router.get("/admin/all", response_model=List[AccountResponse])
def get_all_accounts(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    return account_service.list_all_accounts(db)

@router.put("/admin/{account_id}/status", response_model=AccountResponse)
def update_account_status(
    account_id: int,
    schema: AccountStatusUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    return account_service.update_account_status(db, account_id, schema.status)
