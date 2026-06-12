from fastapi import APIRouter, Depends, Request, Form, Query, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from decimal import Decimal
from typing import Optional

from app.database.connection import get_db
from app.models.user import User
from app.auth.dependencies import get_current_user_page, get_current_admin_page
from app.services.account_service import account_service
from app.services.transaction_service import transaction_service

router = APIRouter(tags=["Transactions"])
templates = Jinja2Templates(directory="templates")

# Pages
@router.get("/transactions", response_class=HTMLResponse)
def get_transactions_page(
    request: Request,
    account_id: Optional[int] = Query(None),
    query: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user_page),
    db: Session = Depends(get_db)
):
    accounts = account_service.get_user_accounts(db, current_user.id)
    selected_account = None
    transactions = []
    
    if accounts:
        # Default to first account if none selected
        if not account_id:
            account_id = accounts[0].id
        
        selected_account = next((a for a in accounts if a.id == account_id), None)
        if selected_account:
            transactions = transaction_service.get_account_statement(db, current_user, selected_account.id, query)
            
    return templates.TemplateResponse(
        request,
        "customer/transactions.html",
        {
            "user": current_user,
            "accounts": accounts,
            "selected_account": selected_account,
            "transactions": transactions,
            "query": query or ""
        }
    )

@router.get("/statements", response_class=HTMLResponse)
def get_statements_page(
    request: Request,
    account_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user_page),
    db: Session = Depends(get_db)
):
    accounts = account_service.get_user_accounts(db, current_user.id)
    selected_account = None
    transactions = []
    
    if accounts:
        if not account_id:
            account_id = accounts[0].id
        selected_account = next((a for a in accounts if a.id == account_id), None)
        if selected_account:
            transactions = transaction_service.get_account_statement(db, current_user, selected_account.id, limit=10) # Mini statement
            
    return templates.TemplateResponse(
        request,
        "customer/statements.html",
        {
            "user": current_user,
            "accounts": accounts,
            "selected_account": selected_account,
            "transactions": transactions
        }
    )

@router.get("/admin/transactions", response_class=HTMLResponse)
def get_admin_transactions_page(
    request: Request,
    query: Optional[str] = Query(None),
    admin: User = Depends(get_current_admin_page),
    db: Session = Depends(get_db)
):
    transactions = transaction_service.get_all_transactions(db, query)
    return templates.TemplateResponse(
        request,
        "admin/transactions.html",
        {"user": admin, "transactions": transactions, "query": query or ""}
    )

# Action Forms
@router.post("/transactions/deposit")
def deposit(
    account_id: int = Form(...),
    amount: Decimal = Form(...),
    description: str = Form(None),
    current_user: User = Depends(get_current_user_page),
    db: Session = Depends(get_db)
):
    try:
        transaction_service.deposit(db, current_user, account_id, amount, description)
        return RedirectResponse(url=f"/transactions?account_id={account_id}&success=Deposited+${amount:,.2f}+successfully", status_code=303)
    except HTTPException as e:
        return RedirectResponse(url=f"/transactions?account_id={account_id}&error=" + str(e.detail), status_code=303)

@router.post("/transactions/withdraw")
def withdraw(
    account_id: int = Form(...),
    amount: Decimal = Form(...),
    description: str = Form(None),
    current_user: User = Depends(get_current_user_page),
    db: Session = Depends(get_db)
):
    try:
        transaction_service.withdraw(db, current_user, account_id, amount, description)
        return RedirectResponse(url=f"/transactions?account_id={account_id}&success=Withdrew+${amount:,.2f}+successfully", status_code=303)
    except HTTPException as e:
        return RedirectResponse(url=f"/transactions?account_id={account_id}&error=" + str(e.detail), status_code=303)

@router.post("/transactions/transfer")
def transfer(
    source_account_id: int = Form(...),
    destination_account_number: str = Form(...),
    amount: Decimal = Form(...),
    description: str = Form(None),
    current_user: User = Depends(get_current_user_page),
    db: Session = Depends(get_db)
):
    try:
        transaction_service.transfer(db, current_user, source_account_id, destination_account_number, amount, description)
        return RedirectResponse(url=f"/transactions?account_id={source_account_id}&success=Transferred+${amount:,.2f}+successfully", status_code=303)
    except HTTPException as e:
        return RedirectResponse(url=f"/transactions?account_id={source_account_id}&error=" + str(e.detail), status_code=303)

@router.post("/statements/{account_id}/download")
def download_statement(
    account_id: int,
    current_user: User = Depends(get_current_user_page),
    db: Session = Depends(get_db)
):
    try:
        download_url = transaction_service.generate_statement_download_url(db, current_user, account_id)
        # Direct redirect to the statement download URL (either Azure Blob or local fallback)
        return RedirectResponse(url=download_url, status_code=303)
    except HTTPException as e:
        return RedirectResponse(url=f"/statements?account_id={account_id}&error=" + str(e.detail), status_code=303)
