import enum
from sqlalchemy import Column, Integer, String, Enum, Numeric, ForeignKey, DateTime, Date, func
from sqlalchemy.orm import relationship
from app.database.connection import Base

class LoanType(str, enum.Enum):
    PERSONAL = "PERSONAL"
    HOME = "HOME"
    VEHICLE = "VEHICLE"
    EDUCATION = "EDUCATION"

class LoanStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    DEFAULTED = "DEFAULTED"

class EMIStatus(str, enum.Enum):
    UNPAID = "UNPAID"
    PAID = "PAID"
    OVERDUE = "OVERDUE"

class Loan(Base):
    __tablename__ = "loans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    loan_type = Column(Enum(LoanType), nullable=False)
    principal_amount = Column(Numeric(precision=15, scale=2), nullable=False)
    interest_rate = Column(Numeric(precision=5, scale=2), nullable=False)
    tenure_months = Column(Integer, nullable=False)
    emi_amount = Column(Numeric(precision=15, scale=2), default=0.00, nullable=False)
    status = Column(Enum(LoanStatus), default=LoanStatus.PENDING, nullable=False)
    outstanding_balance = Column(Numeric(precision=15, scale=2), default=0.00, nullable=False)
    comments = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="loans")
    documents = relationship("LoanDocument", back_populates="loan", cascade="all, delete-orphan")
    emi_schedule = relationship("LoanEMISchedule", back_populates="loan", cascade="all, delete-orphan")
    repayments = relationship("LoanRepaymentHistory", back_populates="loan", cascade="all, delete-orphan")

class LoanDocument(Base):
    __tablename__ = "loan_documents"

    id = Column(Integer, primary_key=True, index=True)
    loan_id = Column(Integer, ForeignKey("loans.id", ondelete="CASCADE"), nullable=False)
    document_name = Column(String, nullable=False)
    document_url = Column(String, nullable=False)
    blob_name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    loan = relationship("Loan", back_populates="documents")

class LoanEMISchedule(Base):
    __tablename__ = "loan_emi_schedules"

    id = Column(Integer, primary_key=True, index=True)
    loan_id = Column(Integer, ForeignKey("loans.id", ondelete="CASCADE"), nullable=False)
    installment_number = Column(Integer, nullable=False)
    due_date = Column(Date, nullable=False)
    emi_amount = Column(Numeric(precision=15, scale=2), nullable=False)
    principal_component = Column(Numeric(precision=15, scale=2), nullable=False)
    interest_component = Column(Numeric(precision=15, scale=2), nullable=False)
    outstanding_principal = Column(Numeric(precision=15, scale=2), nullable=False)
    status = Column(Enum(EMIStatus), default=EMIStatus.UNPAID, nullable=False)
    paid_date = Column(Date, nullable=True)

    # Relationships
    loan = relationship("Loan", back_populates="emi_schedule")

class LoanRepaymentHistory(Base):
    __tablename__ = "loan_repayment_histories"

    id = Column(Integer, primary_key=True, index=True)
    loan_id = Column(Integer, ForeignKey("loans.id", ondelete="CASCADE"), nullable=False)
    amount_paid = Column(Numeric(precision=15, scale=2), nullable=False)
    payment_date = Column(DateTime(timezone=True), server_default=func.now())
    payment_method = Column(String, default="BANK_TRANSFER", nullable=False)

    # Relationships
    loan = relationship("Loan", back_populates="repayments")
