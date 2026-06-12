from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
from decimal import Decimal, ROUND_HALF_UP
import datetime
from dateutil.relativedelta import relativedelta

from app.models.loan import Loan, LoanDocument, LoanEMISchedule, LoanRepaymentHistory, LoanStatus, EMIStatus, LoanType
from app.models.user import User
from app.services.storage_service import storage_service
from app.schemas.loan import LoanApplicationRequest

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


class LoanService:
    def _get_interest_rate_by_type(self, loan_type: LoanType) -> Decimal:
        rates = {
            LoanType.PERSONAL: Decimal("12.00"),
            LoanType.HOME: Decimal("8.50"),
            LoanType.VEHICLE: Decimal("9.50"),
            LoanType.EDUCATION: Decimal("7.00")
        }
        return rates.get(loan_type, Decimal("10.00"))

    def _calculate_emi(self, principal: Decimal, annual_rate: Decimal, tenure_months: int) -> Decimal:
        if annual_rate == 0:
            return (principal / Decimal(tenure_months)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        
        r = (annual_rate / Decimal("12")) / Decimal("100")
        n = tenure_months
        
        r_pow = (1 + r) ** n
        emi = principal * r * Decimal(r_pow) / Decimal(r_pow - 1)
        return emi.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def apply_for_loan(self, db: Session, user: User, schema: LoanApplicationRequest) -> Loan:
        if user.kyc_status != "APPROVED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Loan applications are only permitted for users with APPROVED KYC status."
            )
            
        rate = self._get_interest_rate_by_type(schema.loan_type)
        emi = self._calculate_emi(schema.principal_amount, rate, schema.tenure_months)
        
        loan = Loan(
            user_id=user.id,
            loan_type=schema.loan_type,
            principal_amount=schema.principal_amount,
            interest_rate=rate,
            tenure_months=schema.tenure_months,
            emi_amount=emi,
            status=LoanStatus.PENDING,
            outstanding_balance=schema.principal_amount
        )
        return loan_repo.create(db, loan)

    def upload_loan_document(
        self, db: Session, user: User, loan_id: int, document_name: str, file_bytes: bytes, filename: str, content_type: str
    ) -> LoanDocument:
        loan = loan_repo.get_by_id(db, loan_id)
        if not loan or (loan.user_id != user.id and user.role != "ADMIN"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unauthorized access to this loan application."
            )
            
        if loan.status not in [LoanStatus.PENDING]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Supporting documents can only be uploaded for pending loans."
            )
            
        upload_result = storage_service.upload_file(file_bytes, filename, content_type)
        
        doc = LoanDocument(
            loan_id=loan.id,
            document_name=document_name,
            document_url=upload_result["url"],
            blob_name=upload_result["blob_name"]
        )
        return loan_repo.create_document(db, doc)

    def review_loan(self, db: Session, loan_id: int, review_status: LoanStatus, comments: Optional[str] = None) -> Loan:
        loan = loan_repo.get_by_id(db, loan_id)
        if not loan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Loan not found"
            )
            
        if loan.status != LoanStatus.PENDING:
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Loan is already reviewed and is not in PENDING state."
            )
             
        if review_status not in [LoanStatus.APPROVED, LoanStatus.REJECTED]:
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Review status must be APPROVED or REJECTED."
            )

        loan.status = review_status
        loan.comments = comments
        
        if review_status == LoanStatus.APPROVED:
            loan.status = LoanStatus.ACTIVE
            self._generate_amortization_schedule(db, loan)
            
        return loan_repo.update(db, loan)

    def _generate_amortization_schedule(self, db: Session, loan: Loan):
        schedule_items = []
        remaining_principal = loan.principal_amount
        r = (loan.interest_rate / Decimal("12")) / Decimal("100")
        start_date = datetime.date.today()
        
        for i in range(1, loan.tenure_months + 1):
            due_date = start_date + relativedelta(months=i)
            interest_comp = (remaining_principal * r).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            
            if i == loan.tenure_months:
                principal_comp = remaining_principal
                emi_amt = principal_comp + interest_comp
                remaining_principal = Decimal("0.00")
            else:
                principal_comp = (loan.emi_amount - interest_comp).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                if principal_comp > remaining_principal:
                    principal_comp = remaining_principal
                remaining_principal -= principal_comp
                emi_amt = loan.emi_amount
                
            item = LoanEMISchedule(
                loan_id=loan.id,
                installment_number=i,
                due_date=due_date,
                emi_amount=emi_amt,
                principal_component=principal_comp,
                interest_component=interest_comp,
                outstanding_principal=remaining_principal,
                status=EMIStatus.UNPAID
            )
            schedule_items.append(item)
            
        loan_repo.create_emi_schedule(db, schedule_items)

    def repay_loan(self, db: Session, user: User, loan_id: int, amount: Decimal) -> Loan:
        loan = loan_repo.get_by_id(db, loan_id)
        if not loan or (loan.user_id != user.id and user.role != "ADMIN"):
             raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unauthorized access to this loan."
            )
             
        if loan.status != LoanStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Loan is not ACTIVE. Repayments are only accepted for ACTIVE loans."
            )

        history = LoanRepaymentHistory(
            loan_id=loan.id,
            amount_paid=amount,
            payment_method="BANK_TRANSFER"
        )
        loan_repo.create_repayment(db, history)
        
        loan.outstanding_balance -= amount
        if loan.outstanding_balance <= 0:
            loan.outstanding_balance = Decimal("0.00")
            loan.status = LoanStatus.COMPLETED
            
        unpaid_emis = sorted(
            [e for e in loan.emi_schedule if e.status != EMIStatus.PAID],
            key=lambda x: x.installment_number
        )
        
        remaining_payment = amount
        for emi in unpaid_emis:
            if remaining_payment <= 0:
                break
                
            if emi.emi_amount <= remaining_payment:
                remaining_payment -= emi.emi_amount
                emi.status = EMIStatus.PAID
                emi.paid_date = datetime.date.today()
            else:
                emi.emi_amount -= remaining_payment
                remaining_payment = Decimal("0.00")
                
        if loan.status == LoanStatus.COMPLETED:
            for emi in loan.emi_schedule:
                if emi.status != EMIStatus.PAID:
                    emi.status = EMIStatus.PAID
                    emi.paid_date = datetime.date.today()
                    
        return loan_repo.update(db, loan)

    def get_user_loans(self, db: Session, user_id: int) -> List[Loan]:
        return loan_repo.get_by_user_id(db, user_id)

    def get_loan_details(self, db: Session, loan_id: int) -> Loan:
        loan = loan_repo.get_by_id(db, loan_id)
        if not loan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Loan not found"
            )
        return loan

    def list_all_loans(self, db: Session) -> List[Loan]:
        return loan_repo.list_loans(db)

loan_service = LoanService()
