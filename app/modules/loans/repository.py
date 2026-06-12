from sqlalchemy.orm import Session
from typing import List, Optional
from app.modules.loans.models import Loan, LoanDocument, LoanEMISchedule, LoanRepaymentHistory

class LoanRepository:
    def create(self, db: Session, loan: Loan) -> Loan:
        db.add(loan)
        db.commit()
        db.refresh(loan)
        return loan

    def get_by_id(self, db: Session, loan_id: int) -> Optional[Loan]:
        return db.query(Loan).filter(Loan.id == loan_id).first()

    def get_by_user_id(self, db: Session, user_id: int) -> List[Loan]:
        return db.query(Loan).filter(Loan.user_id == user_id).order_by(Loan.created_at.desc()).all()

    def list_loans(self, db: Session, skip: int = 0, limit: int = 100) -> List[Loan]:
        return db.query(Loan).order_by(Loan.created_at.desc()).offset(skip).limit(limit).all()

    def update(self, db: Session, loan: Loan) -> Loan:
        db.commit()
        db.refresh(loan)
        return loan

    def create_document(self, db: Session, doc: LoanDocument) -> LoanDocument:
        db.add(doc)
        db.commit()
        db.refresh(doc)
        return doc

    def create_emi_schedule(self, db: Session, schedule_items: List[LoanEMISchedule]) -> List[LoanEMISchedule]:
        db.add_all(schedule_items)
        db.commit()
        return schedule_items

    def create_repayment(self, db: Session, repayment: LoanRepaymentHistory) -> LoanRepaymentHistory:
        db.add(repayment)
        db.commit()
        db.refresh(repayment)
        return repayment

loan_repo = LoanRepository()
