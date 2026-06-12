from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.modules.users.models import User
from app.modules.users.router import get_current_user, get_current_admin
from app.modules.kyc.models import KYCDocumentType
from app.modules.kyc.schemas import KYCDocumentResponse, KYCStatusResponse, KYCReviewRequest
from app.modules.kyc.service import kyc_service

router = APIRouter(prefix="/kyc", tags=["KYC"])

@router.post("/upload", response_model=KYCDocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_kyc_document(
    document_type: KYCDocumentType = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Validate file type
    allowed_extensions = {".pdf", ".png", ".jpg", ".jpeg"}
    import os
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format {ext}. Allowed: PDF, PNG, JPG, JPEG"
        )
        
    file_bytes = await file.read()
    return kyc_service.upload_document(
        db, current_user, document_type, file_bytes, file.filename, file.content_type
    )

@router.post("/submit", response_model=KYCStatusResponse)
def submit_kyc(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    updated_user = kyc_service.submit_kyc_final(db, current_user)
    return kyc_service.get_kyc_status(db, updated_user)

@router.get("/status", response_model=KYCStatusResponse)
def get_kyc_status(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return kyc_service.get_kyc_status(db, current_user)

# Admin Endpoints
@router.get("/admin/pending", response_model=List[KYCStatusResponse])
def get_pending_kyc_requests(admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    return kyc_service.get_pending_kyc_requests(db)

@router.post("/admin/review/{user_id}", response_model=KYCStatusResponse)
def review_kyc_request(
    user_id: int,
    schema: KYCReviewRequest,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    reviewed_user = kyc_service.review_kyc(db, user_id, schema.status, schema.comments)
    return kyc_service.get_kyc_status(db, reviewed_user)
