from fastapi import APIRouter, Depends, Request, Form, UploadFile, File, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import os

from app.database.connection import get_db
from app.models.user import User, KYCStatus
from app.models.kyc import KYCDocumentType
from app.auth.dependencies import get_current_user_page, get_current_admin_page
from app.services.kyc_service import kyc_service

router = APIRouter(tags=["KYC"])
templates = Jinja2Templates(directory="templates")

# Pages
@router.get("/kyc", response_class=HTMLResponse)
def get_kyc_page(request: Request, current_user: User = Depends(get_current_user_page), db: Session = Depends(get_db)):
    kyc_status_data = kyc_service.get_kyc_status(db, current_user)
    return templates.TemplateResponse(request, "customer/kyc.html", {"user": current_user, "kyc": kyc_status_data})

@router.get("/admin/kyc-reviews", response_class=HTMLResponse)
def get_admin_kyc_reviews_page(
    request: Request,
    admin: User = Depends(get_current_admin_page),
    db: Session = Depends(get_db)
):
    pending_requests = kyc_service.get_pending_kyc_requests(db)
    return templates.TemplateResponse(request, "admin/kyc_reviews.html", {"user": admin, "requests": pending_requests})

# Form Submissions
@router.post("/kyc/upload")
async def upload_kyc_document(
    document_type: KYCDocumentType = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user_page),
    db: Session = Depends(get_db)
):
    try:
        allowed_extensions = {".pdf", ".png", ".jpg", ".jpeg"}
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format {ext}. Allowed: PDF, PNG, JPG, JPEG"
            )
            
        file_bytes = await file.read()
        kyc_service.upload_document(
            db, current_user, document_type, file_bytes, file.filename, file.content_type
        )
        return RedirectResponse(url="/kyc?success=Document+uploaded+successfully", status_code=303)
    except HTTPException as e:
        return RedirectResponse(url="/kyc?error=" + str(e.detail), status_code=303)
    except Exception as e:
        return RedirectResponse(url="/kyc?error=Document+upload+failed:+storage+is+not+available", status_code=303)

@router.post("/kyc/submit")
def submit_kyc(
    current_user: User = Depends(get_current_user_page),
    db: Session = Depends(get_db)
):
    try:
        kyc_service.submit_kyc_final(db, current_user)
        return RedirectResponse(url="/kyc?success=KYC+submitted+for+verification", status_code=303)
    except HTTPException as e:
        return RedirectResponse(url="/kyc?error=" + str(e.detail), status_code=303)

@router.post("/admin/kyc-reviews/{user_id}/review")
def review_kyc_request(
    user_id: int,
    review_status: KYCStatus = Form(...),
    comments: str = Form(None),
    admin: User = Depends(get_current_admin_page),
    db: Session = Depends(get_db)
):
    try:
        kyc_service.review_kyc(db, user_id, review_status, comments)
        return RedirectResponse(url="/admin/kyc-reviews?success=KYC+request+reviewed+successfully", status_code=303)
    except HTTPException as e:
        return RedirectResponse(url="/admin/kyc-reviews?error=" + str(e.detail), status_code=303)
