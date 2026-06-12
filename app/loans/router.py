from fastapi import APIRouter, Depends, Request, Form, UploadFile, File, Query, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from decimal import Decimal
from typing import Optional

from app.database.connection import get_db
from app.models.user import User
from app.models.loan import LoanType, LoanStatus
from app.auth.dependencies import get_current_user_page, get_current_admin_page
from app.services.loan_service import loan_service
from app.schemas.loan import LoanApplicationRequest

router = APIRouter(tags=["Loans"])
templates = Jinja2Templates(directory="templates")

# Pages
@router.get("/loans", response_class=HTMLResponse)
def get_loans_page(
    request: Request,
    loan_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user_page),
    db: Session = Depends(get_db)
):
    loans = loan_service.get_user_loans(db, current_user.id)
    selected_loan = None
    if loans:
        if not loan_id:
            loan_id = loans[0].id
        selected_loan = loan_service.get_loan_details(db, loan_id)
        # Check authorization
        if selected_loan.user_id != current_user.id:
            selected_loan = None
            
    return templates.TemplateResponse(
        request,
        "customer/loans.html",
        {
            "user": current_user,
            "loans": loans,
            "selected_loan": selected_loan
        }
    )

@router.get("/admin/loans", response_class=HTMLResponse)
def get_admin_loans_page(
    request: Request,
    admin: User = Depends(get_current_admin_page),
    db: Session = Depends(get_db)
):
    loans = loan_service.list_all_loans(db)
    return templates.TemplateResponse(
        request,
        "admin/loans.html",
        {"user": admin, "loans": loans}
    )

# Actions
@router.post("/loans/apply")
def apply_loan(
    loan_type: LoanType = Form(...),
    principal_amount: Decimal = Form(...),
    tenure_months: int = Form(...),
    current_user: User = Depends(get_current_user_page),
    db: Session = Depends(get_db)
):
    try:
        schema = LoanApplicationRequest(
            loan_type=loan_type,
            principal_amount=principal_amount,
            tenure_months=tenure_months
        )
        loan_service.apply_for_loan(db, current_user, schema)
        return RedirectResponse(url="/loans?success=Loan+application+submitted+successfully", status_code=303)
    except HTTPException as e:
        return RedirectResponse(url="/loans?error=" + str(e.detail), status_code=303)

@router.post("/loans/{loan_id}/upload-doc")
async def upload_supporting_doc(
    loan_id: int,
    document_name: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user_page),
    db: Session = Depends(get_db)
):
    try:
        file_bytes = await file.read()
        loan_service.upload_loan_document(
            db, current_user, loan_id, document_name, file_bytes, file.filename, file.content_type
        )
        return RedirectResponse(url=f"/loans?loan_id={loan_id}&success=Supporting+document+uploaded+successfully", status_code=303)
    except HTTPException as e:
        return RedirectResponse(url=f"/loans?loan_id={loan_id}&error=" + str(e.detail), status_code=303)

@router.post("/loans/{loan_id}/repay")
def repay_loan(
    loan_id: int,
    amount: Decimal = Form(...),
    current_user: User = Depends(get_current_user_page),
    db: Session = Depends(get_db)
):
    try:
        loan_service.repay_loan(db, current_user, loan_id, amount)
        return RedirectResponse(url=f"/loans?loan_id={loan_id}&success=EMI+repayment+of+${amount:,.2f}+processed+successfully", status_code=303)
    except HTTPException as e:
        return RedirectResponse(url=f"/loans?loan_id={loan_id}&error=" + str(e.detail), status_code=303)

@router.post("/admin/loans/{loan_id}/review")
def review_loan(
    loan_id: int,
    status: LoanStatus = Form(...),
    comments: str = Form(None),
    admin: User = Depends(get_current_admin_page),
    db: Session = Depends(get_db)
):
    try:
        loan_service.review_loan(db, loan_id, status, comments)
        return RedirectResponse(url="/admin/loans?success=Loan+application+reviewed+successfully", status_code=303)
    except HTTPException as e:
        return RedirectResponse(url="/admin/loans?error=" + str(e.detail), status_code=303)
