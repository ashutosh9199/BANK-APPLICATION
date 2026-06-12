from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional

from app.models.kyc import KYCDocument, KYCDocumentType, KYCDocumentStatus
from app.models.user import User, KYCStatus, UserRole
from app.services.user_service import user_repo
from app.services.storage_service import storage_service
from app.services.notification_service import notification_service
from app.schemas.kyc import KYCStatusResponse

class KYCDocumentRepository:
    def create(self, db: Session, doc: KYCDocument) -> KYCDocument:
        db.add(doc)
        db.commit()
        db.refresh(doc)
        return doc

    def get_by_id(self, db: Session, doc_id: int) -> Optional[KYCDocument]:
        return db.query(KYCDocument).filter(KYCDocument.id == doc_id).first()

    def get_by_user_id(self, db: Session, user_id: int) -> List[KYCDocument]:
        return db.query(KYCDocument).filter(KYCDocument.user_id == user_id).all()

    def delete_by_user_id(self, db: Session, user_id: int) -> List[KYCDocument]:
        docs = self.get_by_user_id(db, user_id)
        for doc in docs:
            db.delete(doc)
        db.commit()
        return docs

kyc_repo = KYCDocumentRepository()


class KYCService:
    def upload_document(
        self, db: Session, user: User, doc_type: KYCDocumentType, file_bytes: bytes, filename: str, content_type: str
    ) -> KYCDocument:
        if user.kyc_status == KYCStatus.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="KYC is already approved. Cannot upload more documents."
            )

        if user.kyc_status == KYCStatus.REJECTED:
            # Delete old documents in storage and DB
            old_docs = kyc_repo.get_by_user_id(db, user.id)
            for doc in old_docs:
                storage_service.delete_file(doc.blob_name)
            kyc_repo.delete_by_user_id(db, user.id)
            user.kyc_status = KYCStatus.DRAFT
            user.kyc_comments = None
            db.commit()

        upload_result = storage_service.upload_file(file_bytes, filename, content_type)
        
        doc = KYCDocument(
            user_id=user.id,
            document_type=doc_type,
            document_url=upload_result["url"],
            blob_name=upload_result["blob_name"],
            status=KYCDocumentStatus.SUBMITTED
        )
        created_doc = kyc_repo.create(db, doc)

        if user.kyc_status in [KYCStatus.DRAFT, KYCStatus.REJECTED]:
            user.kyc_status = KYCStatus.SUBMITTED
        
        db.commit()
        db.refresh(user)
        notification_service.publish(
            "kyc.document_uploaded",
            {
                "user_id": user.id,
                "email": user.email,
                "document_id": created_doc.id,
                "document_type": str(created_doc.document_type),
                "blob_name": created_doc.blob_name,
                "document_url": created_doc.document_url,
                "kyc_status": str(user.kyc_status)
            }
        )
        return created_doc

    def submit_kyc_final(self, db: Session, user: User) -> User:
        docs = kyc_repo.get_by_user_id(db, user.id)
        if not docs:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please upload at least one document before submitting KYC."
            )
        
        user.kyc_status = KYCStatus.SUBMITTED
        db.commit()
        db.refresh(user)
        notification_service.publish(
            "kyc.submitted",
            {
                "user_id": user.id,
                "email": user.email,
                "document_count": len(docs),
                "kyc_status": str(user.kyc_status)
            }
        )
        return user

    def review_kyc(self, db: Session, target_user_id: int, review_status: KYCStatus, comments: str) -> User:
        user = user_repo.get_by_id(db, target_user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if user.role == UserRole.ADMIN:
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Admin users do not require KYC verification"
            )

        if review_status not in [KYCStatus.APPROVED, KYCStatus.REJECTED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid review status. Must be APPROVED or REJECTED."
            )

        user.kyc_status = review_status
        user.kyc_comments = comments

        docs = kyc_repo.get_by_user_id(db, target_user_id)
        doc_status = KYCDocumentStatus.APPROVED if review_status == KYCStatus.APPROVED else KYCDocumentStatus.REJECTED
        for doc in docs:
            doc.status = doc_status
            doc.comments = comments
            
        db.commit()
        db.refresh(user)
        notification_service.publish(
            "kyc.reviewed",
            {
                "user_id": user.id,
                "email": user.email,
                "review_status": str(review_status),
                "document_count": len(docs)
            }
        )
        return user

    def get_kyc_status(self, db: Session, user: User) -> KYCStatusResponse:
        docs = kyc_repo.get_by_user_id(db, user.id)
        return KYCStatusResponse(
            user_id=user.id,
            full_name=user.full_name,
            email=user.email,
            kyc_status=user.kyc_status,
            kyc_comments=user.kyc_comments,
            documents=docs
        )

    def get_pending_kyc_requests(self, db: Session) -> List[KYCStatusResponse]:
        users = db.query(User).filter(User.kyc_status.in_([KYCStatus.SUBMITTED, KYCStatus.UNDER_REVIEW])).all()
        results = []
        for u in users:
            docs = kyc_repo.get_by_user_id(db, u.id)
            results.append(
                KYCStatusResponse(
                    user_id=u.id,
                    full_name=u.full_name,
                    email=u.email,
                    kyc_status=u.kyc_status,
                    kyc_comments=u.kyc_comments,
                    documents=docs
                )
            )
        return results

kyc_service = KYCService()
