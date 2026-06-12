from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal
import os

from app.core.config import settings
from app.database.connection import engine, Base, SessionLocal, get_db
from app.models.user import User, UserRole, KYCStatus
from app.models.account import Account, AccountStatus
from app.models.loan import Loan, LoanStatus
from app.models.transaction import Transaction
from app.core.security import get_password_hash
from app.auth.dependencies import (
    UnauthenticatedException,
    UnauthorizedAdminException,
    get_current_user_optional,
    get_current_user_page,
    get_current_admin_page
)

# Import routers
from app.auth.router import router as auth_router
from app.users.router import router as users_router
from app.kyc.router import router as kyc_router
from app.accounts.router import router as accounts_router
from app.transactions.router import router as transactions_router
from app.loans.router import router as loans_router

app = FastAPI(title=settings.PROJECT_NAME)

# Exception handlers for page level redirects
@app.exception_handler(UnauthenticatedException)
def unauthenticated_exception_handler(request: Request, exc: UnauthenticatedException):
    return RedirectResponse(url="/login?error=Session+expired.+Please+log+in.", status_code=status.HTTP_303_SEE_OTHER)

@app.exception_handler(UnauthorizedAdminException)
def unauthorized_admin_exception_handler(request: Request, exc: UnauthorizedAdminException):
    return RedirectResponse(url="/dashboard?error=Access+denied.+Admins+only.", status_code=status.HTTP_303_SEE_OTHER)

# Mount static files (served by the app)
os.makedirs("static/uploads", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Jinja2 Templates
templates = Jinja2Templates(directory="templates")

# Register routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(kyc_router)
app.include_router(accounts_router)
app.include_router(transactions_router)
app.include_router(loans_router)

# Serve local upload fallback files (so uploads work in dev fallbacks)
@app.get("/api/uploads/{filename}")
def serve_upload(filename: str):
    local_path = os.path.join("static/uploads", filename)
    if os.path.exists(local_path):
        from fastapi.responses import FileResponse
        return FileResponse(local_path)
    raise HTTPException(status_code=404, detail="File not found")

# DB Auto-generation & Seeds on Startup
@app.on_event("startup")
def startup_event():
    # 1. Create tables automatically in PostgreSQL
    try:
        Base.metadata.create_all(bind=engine)
        print("[DB LOG] Tables verified and created successfully.")
    except Exception as e:
        print(f"[DB ERROR] Failed to create tables: {e}")
        
    # 2. Seed a default Admin account if missing
    db = SessionLocal()
    try:
        admin_email = "admin@bank.com"
        admin = db.query(User).filter(User.email == admin_email).first()
        if not admin:
            hashed_pw = get_password_hash("adminpassword")
            default_admin = User(
                full_name="System Administrator",
                email=admin_email,
                hashed_password=hashed_pw,
                role=UserRole.ADMIN,
                kyc_status=KYCStatus.APPROVED,
                is_active=True
            )
            db.add(default_admin)
            db.commit()
            print("\n======================================================================")
            print("[SEED LOG] Seeding default administrator account:")
            print("Username: admin@bank.com")
            print("Password: adminpassword")
            print("======================================================================\n")
    except Exception as e:
        print(f"[SEED ERROR] Failed to seed default admin: {e}")
    finally:
        db.close()

# Overview Pages
@app.get("/", response_class=HTMLResponse)
def get_landing_page(request: Request, current_user = Depends(get_current_user_optional)):
    if current_user:
        redirect_url = "/dashboard" if current_user.role == UserRole.CUSTOMER else "/admin/dashboard"
        return RedirectResponse(url=redirect_url, status_code=303)
    return templates.TemplateResponse(request, "landing.html", {})

@app.get("/dashboard", response_class=HTMLResponse)
def get_customer_dashboard(
    request: Request,
    current_user: User = Depends(get_current_user_page),
    db: Session = Depends(get_db)
):
    if current_user.role != UserRole.CUSTOMER:
         return RedirectResponse(url="/admin/dashboard", status_code=303)
         
    # Combined calculations
    accounts = db.query(Account).filter(Account.user_id == current_user.id).all()
    total_balance = sum(acc.balance for acc in accounts)
    
    loans = db.query(Loan).filter(
        Loan.user_id == current_user.id, 
        Loan.status == LoanStatus.ACTIVE
    ).all()
    total_loan_debt = sum(ln.outstanding_balance for ln in loans)
    
    # 5 Recent Transactions across all accounts
    account_ids = [acc.id for acc in accounts]
    transactions = []
    if account_ids:
        transactions = db.query(Transaction).filter(
            (Transaction.source_account_id.in_(account_ids)) | 
            (Transaction.destination_account_id.in_(account_ids))
        ).order_by(Transaction.created_at.desc()).limit(5).all()
        
    return templates.TemplateResponse(
        request,
        "customer/dashboard.html",
        {
            "user": current_user,
            "total_balance": total_balance,
            "kyc_status": current_user.kyc_status,
            "total_loan_debt": total_loan_debt,
            "accounts": accounts,
            "transactions": transactions
        }
    )

@app.get("/admin/dashboard", response_class=HTMLResponse)
def get_admin_dashboard(
    request: Request,
    admin: User = Depends(get_current_admin_page),
    db: Session = Depends(get_db)
):
    # Total combined liquid balance deposits in the entire bank
    total_deposits = db.query(func.sum(Account.balance)).scalar() or Decimal("0.00")
    
    # Total outstanding credit sum
    total_loan_portfolio = db.query(func.sum(Loan.outstanding_balance)).scalar() or Decimal("0.00")
    
    # Pending KYC actions
    pending_kyc_count = db.query(User).filter(User.kyc_status.in_([KYCStatus.SUBMITTED, KYCStatus.UNDER_REVIEW])).count()
    
    # Total registered customer users
    total_users = db.query(User).filter(User.role == UserRole.CUSTOMER).count()
    
    # Lists
    recent_users = db.query(User).filter(User.role == UserRole.CUSTOMER).order_by(User.created_at.desc()).limit(5).all()
    recent_loans = db.query(Loan).order_by(Loan.created_at.desc()).limit(5).all()
    
    return templates.TemplateResponse(
        request,
        "admin/dashboard.html",
        {
            "user": admin,
            "total_deposits": total_deposits,
            "total_loan_portfolio": total_loan_portfolio,
            "pending_kyc_count": pending_kyc_count,
            "total_users": total_users,
            "users": recent_users,
            "loans": recent_loans
        }
    )
