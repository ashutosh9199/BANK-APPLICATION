from sqlalchemy.orm import Session
from typing import List, Optional
from app.modules.kyc.models import KYCDocument

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
