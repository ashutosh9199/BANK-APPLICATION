from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from app.modules.transactions.models import Transaction

class TransactionRepository:
    def create(self, db: Session, transaction: Transaction) -> Transaction:
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        return transaction

    def get_by_id(self, db: Session, transaction_id: int) -> Optional[Transaction]:
        return db.query(Transaction).filter(Transaction.id == transaction_id).first()

    def list_by_account_id(
        self, db: Session, account_id: int, query: Optional[str] = None, skip: int = 0, limit: int = 100
    ) -> List[Transaction]:
        db_query = db.query(Transaction).filter(
            or_(
                Transaction.source_account_id == account_id,
                Transaction.destination_account_id == account_id
            )
        )
        if query:
            db_query = db_query.filter(Transaction.description.ilike(f"%{query}%"))
            
        return db_query.order_by(Transaction.created_at.desc()).offset(skip).limit(limit).all()

    def list_all(
        self, db: Session, query: Optional[str] = None, skip: int = 0, limit: int = 100
    ) -> List[Transaction]:
        db_query = db.query(Transaction)
        if query:
            db_query = db_query.filter(Transaction.description.ilike(f"%{query}%"))
        return db_query.order_by(Transaction.created_at.desc()).offset(skip).limit(limit).all()

transaction_repo = TransactionRepository()
