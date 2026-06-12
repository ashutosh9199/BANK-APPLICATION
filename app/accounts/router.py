from fastapi import APIRouter, Depends, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List

from app.database.connection import get_db
from app.models.user import User
from app.models.account import AccountType, AccountStatus
from app.auth.dependencies import get_current_user_page, get_current_admin_page
from app.services.account_service import account_service

router = APIRouter(tags=["Accounts"])
templates = Jinja2Templates(directory="templates")

# Pages
@router.get("/accounts", response_class=HTMLResponse)
def get_accounts_page(
    request: Request,
    current_user: User = Depends(get_current_user_page),
    db: Session = Depends(get_db)
):
    accounts = account_service.get_user_accounts(db, current_user.id)
    return templates.TemplateResponse(
        request,
        "customer/accounts.html", 
        {"user": current_user, "accounts": accounts}
    )

@router.get("/admin/accounts", response_class=HTMLResponse)
def get_admin_accounts_page(
    request: Request,
    admin: User = Depends(get_current_admin_page),
    db: Session = Depends(get_db)
):
    accounts = account_service.list_all_accounts(db)
    return templates.TemplateResponse(
        request,
        "admin/accounts.html", 
        {"user": admin, "accounts": accounts}
    )

# Form Handlers
@router.post("/accounts/create")
def create_account(
    account_type: AccountType = Form(...),
    current_user: User = Depends(get_current_user_page),
    db: Session = Depends(get_db)
):
    try:
        account_service.create_account(db, current_user, account_type)
        return RedirectResponse(url="/accounts?success=Account+created+successfully", status_code=303)
    except HTTPException as e:
        return RedirectResponse(url="/accounts?error=" + str(e.detail), status_code=303)

@router.post("/admin/accounts/{account_id}/status")
def update_account_status(
    account_id: int,
    account_status: AccountStatus = Form(...),
    admin: User = Depends(get_current_admin_page),
    db: Session = Depends(get_db)
):
    try:
        account_service.update_account_status(db, account_id, account_status)
        return RedirectResponse(url="/admin/accounts?success=Account+status+updated+successfully", status_code=303)
    except HTTPException as e:
        return RedirectResponse(url="/admin/accounts?error=" + str(e.detail), status_code=303)
