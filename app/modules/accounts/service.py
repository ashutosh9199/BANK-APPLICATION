import random
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List

from app.modules.accounts.models import Account, AccountType, AccountStatus
from app.modules.accounts.repository import account_repo
from app.modules.users.models import User, KYCStatus

class AccountService:
    def generate_unique_account_number(self, db: Session) -> str:
        # Generate a unique 10-digit account number starting with a random digit (1-9)
        while True:
            first_digit = str(random.randint(1, 9))
            remaining_digits = "".join([str(random.randint(0, 9)) for _ in range(9)])
            account_number = f"{first_digit}{remaining_digits}"
            # Ensure it is unique
            if not account_repo.get_by_number(db, account_number):
                return account_number

    def create_account(self, db: Session, user: User, account_type: AccountType) -> Account:
        # Check KYC Business Rule
        if user.kyc_status != KYCStatus.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Accounts can only be created when KYC Status is APPROVED."
            )
        
        # Generate number
        account_number = self.generate_unique_account_number(db)
        
        account = Account(
            user_id=user.id,
            account_number=account_number,
            account_type=account_type,
            balance=0.00,
            status=AccountStatus.ACTIVE
        )
        return account_repo.create(db, account)

    def get_user_accounts(self, db: Session, user_id: int) -> List[Account]:
        return account_repo.get_by_user_id(db, user_id)

    def get_account_by_id(self, db: Session, account_id: int) -> Account:
        account = account_repo.get_by_id(db, account_id)
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found"
            )
        return account

    def update_account_status(self, db: Session, account_id: int, new_status: AccountStatus) -> Account:
        account = self.get_account_by_id(db, account_id)
        
        # Once closed, an account cannot be unclosed or modified (standard bank rule)
        if account.status == AccountStatus.CLOSED:
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Closed accounts cannot be updated."
            )
             
        account.status = new_status
        return account_repo.update(db, account)

    def list_all_accounts(self, db: Session) -> List[Account]:
        return account_repo.list_accounts(db)

account_service = AccountService()
