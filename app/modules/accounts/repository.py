from sqlalchemy.orm import Session
from typing import List, Optional
from app.modules.accounts.models import Account

class AccountRepository:
    def create(self, db: Session, account: Account) -> Account:
        db.add(account)
        db.commit()
        db.refresh(account)
        return account

    def get_by_id(self, db: Session, account_id: int) -> Optional[Account]:
        return db.query(Account).filter(Account.id == account_id).first()

    def get_by_number(self, db: Session, account_number: str) -> Optional[Account]:
        return db.query(Account).filter(Account.account_number == account_number).first()

    def get_by_user_id(self, db: Session, user_id: int) -> List[Account]:
        return db.query(Account).filter(Account.user_id == user_id).all()

    def list_accounts(self, db: Session, skip: int = 0, limit: int = 100) -> List[Account]:
        return db.query(Account).offset(skip).limit(limit).all()

    def update(self, db: Session, account: Account) -> Account:
        db.commit()
        db.refresh(account)
        return account

account_repo = AccountRepository()
