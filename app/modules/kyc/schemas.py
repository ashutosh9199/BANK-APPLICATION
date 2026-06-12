from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.modules.kyc.models import KYCDocumentType, KYCDocumentStatus
from app.modules.users.models import KYCStatus

class KYCDocumentResponse(BaseModel):
    id: int
    user_id: int
    document_type: KYCDocumentType
    document_url: str
    blob_name: str
    status: KYCDocumentStatus
    comments: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class KYCStatusResponse(BaseModel):
    user_id: int
    full_name: str
    email: str
    kyc_status: KYCStatus
    kyc_comments: Optional[str] = None
    documents: List[KYCDocumentResponse]

class KYCReviewRequest(BaseModel):
    status: KYCStatus  # APPROVED or REJECTED
    comments: Optional[str] = None
