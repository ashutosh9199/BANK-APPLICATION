from fastapi import APIRouter, Depends, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List

from app.database.connection import get_db
from app.models.user import User, UserRole
from app.auth.dependencies import get_current_user_page, get_current_admin_page, get_current_user_api, get_current_admin_api
from app.schemas.user import UserResponse, UserUpdate, PasswordChange
from app.services.user_service import user_service

router = APIRouter(tags=["Users"])
templates = Jinja2Templates(directory="templates")

# Pages
@router.get("/profile", response_class=HTMLResponse)
def get_profile_page(request: Request, current_user: User = Depends(get_current_user_page)):
    return templates.TemplateResponse(request, "customer/profile.html", {"user": current_user, "error": None, "success": None})

@router.get("/admin/users", response_class=HTMLResponse)
def get_admin_users_page(request: Request, admin: User = Depends(get_current_admin_page), db: Session = Depends(get_db)):
    users = user_service.list_users(db)
    return templates.TemplateResponse(request, "admin/users.html", {"user": admin, "users": users})

# HTML Form Handlers / REST APIs
@router.post("/profile/update")
def update_profile(
    full_name: str = Form(None),
    mobile_number: str = Form(None),
    address: str = Form(None),
    current_user: User = Depends(get_current_user_page),
    db: Session = Depends(get_db)
):
    try:
        schema = UserUpdate(
            full_name=full_name,
            mobile_number=mobile_number,
            address=address
        )
        user_service.update_profile(db, current_user, schema)
        return RedirectResponse(url="/profile?success=Profile+updated+successfully", status_code=303)
    except HTTPException as e:
        return RedirectResponse(url="/profile?error=" + str(e.detail), status_code=303)

@router.post("/profile/change-password")
def change_password(
    current_password: str = Form(...),
    new_password: str = Form(...),
    current_user: User = Depends(get_current_user_page),
    db: Session = Depends(get_db)
):
    try:
        schema = PasswordChange(
            current_password=current_password,
            new_password=new_password
        )
        user_service.change_password(db, current_user, schema)
        return RedirectResponse(url="/profile?success=Password+changed+successfully", status_code=303)
    except HTTPException as e:
        return RedirectResponse(url="/profile?error=" + str(e.detail), status_code=303)

# Admin API
@router.post("/admin/users/{user_id}/toggle-active")
def toggle_user_active(
    user_id: int,
    admin: User = Depends(get_current_admin_page),
    db: Session = Depends(get_db)
):
    try:
        user_service.toggle_user_active(db, user_id)
        return RedirectResponse(url="/admin/users?success=User+active+status+toggled", status_code=303)
    except HTTPException as e:
        return RedirectResponse(url="/admin/users?error=" + str(e.detail), status_code=303)
