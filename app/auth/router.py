from fastapi import APIRouter, Depends, Request, Response, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.services.user_service import user_service
from app.schemas.user import CustomerCreate, AdminCreate, LoginRequest, ForgotPasswordRequest, ResetPasswordRequest
from app.auth.dependencies import get_current_user_optional

router = APIRouter(tags=["Authentication"])
templates = Jinja2Templates(directory="templates")

# Browser HTML Page routes
@router.get("/login", response_class=HTMLResponse)
def get_login_page(request: Request, current_user = Depends(get_current_user_optional)):
    if current_user:
        return RedirectResponse(url="/dashboard", status_code=303)
    return templates.TemplateResponse(request, "auth/login.html", {"error": None})

@router.get("/register", response_class=HTMLResponse)
def get_register_page(request: Request, current_user = Depends(get_current_user_optional)):
    if current_user:
        return RedirectResponse(url="/dashboard", status_code=303)
    return templates.TemplateResponse(request, "auth/register.html", {"error": None})

@router.get("/forgot-password", response_class=HTMLResponse)
def get_forgot_password_page(request: Request):
    return templates.TemplateResponse(request, "auth/forgot_password.html", {"error": None, "success": None})

# HTML Form Submissions or API logins
@router.post("/login")
def login(
    response: Response,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        schema = LoginRequest(email=email, password=password)
        token_data = user_service.login(db, schema)
        
        # Create redirect response
        redirect_url = "/dashboard" if token_data.role == "CUSTOMER" else "/admin/dashboard"
        redirect_response = RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)
        
        # Set access token cookie (HTTP-only)
        redirect_response.set_cookie(
            key="access_token",
            value=token_data.access_token,
            httponly=True,
            max_age=1800, # 30 mins
            samesite="lax",
            secure=False # Set to True in production (HTTPS)
        )
        return redirect_response
    except HTTPException as e:
        # If it's a browser form load, we render the page again with an error
        return RedirectResponse(url="/login?error=" + str(e.detail), status_code=303)

@router.post("/register")
def register(
    full_name: str = Form(...),
    email: str = Form(...),
    mobile_number: str = Form(...),
    password: str = Form(...),
    address: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        schema = CustomerCreate(
            full_name=full_name,
            email=email,
            mobile_number=mobile_number,
            password=password,
            address=address
        )
        user_service.register_customer(db, schema)
        return RedirectResponse(url="/login?success=Account+created.+Please+login.", status_code=303)
    except HTTPException as e:
        return RedirectResponse(url="/register?error=" + str(e.detail), status_code=303)

@router.post("/forgot-password")
def forgot_password(
    email: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        token = user_service.forgot_password(db, email)
        return RedirectResponse(url=f"/forgot-password?success=Simulated+token+printed+to+console.+Token:+{token}", status_code=303)
    except HTTPException as e:
        return RedirectResponse(url="/forgot-password?error=" + str(e.detail), status_code=303)

@router.get("/logout")
def logout(response: Response):
    # Create redirect to login and delete cookie
    redirect = RedirectResponse(url="/login?success=Logged+out+successfully.", status_code=303)
    redirect.delete_cookie("access_token")
    return redirect
