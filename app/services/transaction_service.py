from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import HTTPException, status
from typing import List, Optional
from decimal import Decimal
import datetime

from app.models.transaction import Transaction, TransactionType
from app.models.account import Account, AccountStatus
from app.services.account_service import account_repo
from app.models.user import User
from app.services.storage_service import storage_service
from app.schemas.transaction import TransactionResponse

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


class TransactionService:
    def _validate_account_active(self, account: Account):
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found"
            )
        if account.status == AccountStatus.FROZEN:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Account {account.account_number} is FROZEN. Transactions are suspended."
            )
        if account.status == AccountStatus.CLOSED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Account {account.account_number} is CLOSED. Transactions are disabled."
            )

    def deposit(self, db: Session, user: User, account_id: int, amount: Decimal, description: Optional[str] = None) -> Transaction:
        account = account_repo.get_by_id(db, account_id)
        if not account or (account.user_id != user.id and user.role != "ADMIN"):
             raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unauthorized access to this account."
            )
             
        self._validate_account_active(account)
        
        account.balance += amount
        account_repo.update(db, account)
        
        tx = Transaction(
            destination_account_id=account.id,
            transaction_type=TransactionType.DEPOSIT,
            amount=amount,
            description=description or f"Deposit of ${amount:,.2f}"
        )
        return transaction_repo.create(db, tx)

    def withdraw(self, db: Session, user: User, account_id: int, amount: Decimal, description: Optional[str] = None) -> Transaction:
        account = account_repo.get_by_id(db, account_id)
        if not account or (account.user_id != user.id and user.role != "ADMIN"):
             raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unauthorized access to this account."
            )
             
        self._validate_account_active(account)
        
        if account.balance < amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sufficient balance required."
            )
            
        account.balance -= amount
        account_repo.update(db, account)
        
        tx = Transaction(
            source_account_id=account.id,
            transaction_type=TransactionType.WITHDRAW,
            amount=amount,
            description=description or f"Withdrawal of ${amount:,.2f}"
        )
        return transaction_repo.create(db, tx)

    def transfer(
        self, db: Session, user: User, source_account_id: int, destination_account_number: str, amount: Decimal, description: Optional[str] = None
    ) -> Transaction:
        source_account = account_repo.get_by_id(db, source_account_id)
        if not source_account or (source_account.user_id != user.id and user.role != "ADMIN"):
             raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unauthorized access to the source account."
            )
             
        self._validate_account_active(source_account)
        
        destination_account = account_repo.get_by_number(db, destination_account_number)
        if not destination_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Destination account number {destination_account_number} does not exist."
            )
            
        self._validate_account_active(destination_account)
        
        if source_account.id == destination_account.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot transfer to the same account."
            )

        if source_account.balance < amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient balance for transfer."
            )
            
        source_account.balance -= amount
        destination_account.balance += amount
        
        account_repo.update(db, source_account)
        account_repo.update(db, destination_account)
        
        tx = Transaction(
            source_account_id=source_account.id,
            destination_account_id=destination_account.id,
            transaction_type=TransactionType.TRANSFER,
            amount=amount,
            description=description or f"Transfer of ${amount:,.2f} to {destination_account_number}"
        )
        return transaction_repo.create(db, tx)

    def get_account_statement(
        self, db: Session, user: User, account_id: int, query: Optional[str] = None, skip: int = 0, limit: int = 100
    ) -> List[TransactionResponse]:
        account = account_repo.get_by_id(db, account_id)
        if not account or (account.user_id != user.id and user.role != "ADMIN"):
             raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unauthorized access to this account."
            )
             
        txs = transaction_repo.list_by_account_id(db, account_id, query, skip, limit)
        return self._map_transactions_response(txs)

    def get_all_transactions(self, db: Session, query: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[TransactionResponse]:
        txs = transaction_repo.list_all(db, query, skip, limit)
        return self._map_transactions_response(txs)

    def _map_transactions_response(self, txs: List[Transaction]) -> List[TransactionResponse]:
        response = []
        for tx in txs:
            res = TransactionResponse.model_validate(tx)
            res.source_account_number = tx.source_account.account_number if tx.source_account else None
            res.destination_account_number = tx.destination_account.account_number if tx.destination_account else None
            response.append(res)
        return response

    def generate_statement_download_url(self, db: Session, user: User, account_id: int) -> str:
        account = account_repo.get_by_id(db, account_id)
        if not account or (account.user_id != user.id and user.role != "ADMIN"):
             raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unauthorized access to this account."
            )
        
        txs = transaction_repo.list_by_account_id(db, account_id, query=None, skip=0, limit=1000)
        
        statement_text = f"==================================================\n"
        statement_text += f"              ANTIGRAVITY BANK STATEMENT\n"
        statement_text += f"==================================================\n"
        statement_text += f"Account Number: {account.account_number}\n"
        statement_text += f"Account Type  : {account.account_type}\n"
        statement_text += f"Customer Name : {user.full_name}\n"
        statement_text += f"Current Balance: ${account.balance:,.2f}\n"
        statement_text += f"Generated At  : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        statement_text += f"--------------------------------------------------\n"
        statement_text += f"{'Date':<20} | {'Type':<10} | {'Amount':<10} | {'Description'}\n"
        statement_text += f"--------------------------------------------------\n"
        
        for tx in txs:
            amount_str = f"${tx.amount:,.2f}"
            if tx.transaction_type == TransactionType.WITHDRAW or (tx.transaction_type == TransactionType.TRANSFER and tx.source_account_id == account.id):
                amount_str = f"-{amount_str}"
            else:
                amount_str = f"+{amount_str}"
                
            date_str = tx.created_at.strftime('%Y-%m-%d %H:%M:%S') if tx.created_at else "Pending"
            statement_text += f"{date_str:<20} | {tx.transaction_type:<10} | {amount_str:<10} | {tx.description or ''}\n"
            
        statement_text += f"==================================================\n"
        
        filename = f"statement_{account.account_number}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.txt"
        file_bytes = statement_text.encode("utf-8")
        upload_result = storage_service.upload_file(file_bytes, filename, "text/plain")
        
        return upload_result["url"]

transaction_service = TransactionService()
