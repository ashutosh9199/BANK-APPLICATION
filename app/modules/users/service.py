from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
from datetime import timedelta, datetime, timezone
from jose import jwt

from app.core.config import settings
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token
)
from app.modules.users.models import User, UserRole, KYCStatus
from app.modules.users.schemas import (
    CustomerCreate,
    AdminCreate,
    LoginRequest,
    TokenResponse,
    UserUpdate,
    PasswordChange,
    ResetPasswordRequest
)
from app.modules.users.repository import user_repo

class UserService:
    def register_customer(self, db: Session, schema: CustomerCreate) -> User:
        # Check if user already exists
        if user_repo.get_by_email(db, schema.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        db_user = User(
            full_name=schema.full_name,
            email=schema.email.lower(),
            mobile_number=schema.mobile_number,
            hashed_password=get_password_hash(schema.password),
            address=schema.address,
            role=UserRole.CUSTOMER,
            kyc_status=KYCStatus.DRAFT,
            is_active=True
        )
        return user_repo.create(db, db_user)

    def register_admin(self, db: Session, schema: AdminCreate) -> User:
        # Check if user already exists
        if user_repo.get_by_email(db, schema.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        db_user = User(
            full_name=schema.full_name,
            email=schema.email.lower(),
            hashed_password=get_password_hash(schema.password),
            role=UserRole.ADMIN,
            kyc_status=KYCStatus.APPROVED, # Admin doesn't need KYC, auto-approve status
            is_active=True
        )
        return user_repo.create(db, db_user)

    def login(self, db: Session, schema: LoginRequest) -> TokenResponse:
        user = user_repo.get_by_email(db, schema.email)
        if not user or not verify_password(schema.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated"
            )
            
        access_token = create_access_token(subject=user.id)
        refresh_token = create_refresh_token(subject=user.id)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            role=user.role,
            full_name=user.full_name,
            email=user.email,
            kyc_status=user.kyc_status,
            kyc_comments=user.kyc_comments
        )

    def refresh_access_token(self, db: Session, refresh_token: str) -> dict:
        user_id_str = decode_token(refresh_token, is_refresh=True)
        if not user_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )
        
        user_id = int(user_id_str)
        user = user_repo.get_by_id(db, user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User not found or deactivated"
            )
            
        access_token = create_access_token(subject=user.id)
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }

    def change_password(self, db: Session, user: User, schema: PasswordChange) -> User:
        if not verify_password(schema.current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect current password"
            )
        user.hashed_password = get_password_hash(schema.new_password)
        return user_repo.update(db, user)

    def update_profile(self, db: Session, user: User, schema: UserUpdate) -> User:
        if schema.full_name is not None:
            user.full_name = schema.full_name
        if schema.mobile_number is not None:
            user.mobile_number = schema.mobile_number
        if schema.address is not None:
            user.address = schema.address
        return user_repo.update(db, user)

    def forgot_password(self, db: Session, email: str) -> str:
        user = user_repo.get_by_email(db, email)
        if not user:
            # We don't want to leak if email exists, but in a bank dashboard we can just return a success message anyway.
            # To simulate, we return a mock success message, but we output the reset token to the server log.
            return "If the email is registered, a password reset link has been simulated."
        
        # Create a password reset token (valid for 15 minutes)
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
        to_encode = {"exp": expire, "sub": str(user.id), "type": "reset"}
        reset_token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        
        # Log the reset token so it can be used for testing password resets easily
        print(f"\n[PASSWORD RECOVERY LOG] Reset token for {email}: {reset_token}\n")
        
        return reset_token

    def reset_password(self, db: Session, schema: ResetPasswordRequest) -> str:
        try:
            payload = jwt.decode(schema.token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            token_type = payload.get("type")
            if token_type != "reset":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid token type"
                )
            user_id = int(payload.get("sub"))
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
            
        user = user_repo.get_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
            
        user.hashed_password = get_password_hash(schema.new_password)
        user_repo.update(db, user)
        return "Password reset successful"

    def list_users(self, db: Session) -> List[User]:
        return user_repo.list_users(db)

    def toggle_user_active(self, db: Session, user_id: int) -> User:
        user = user_repo.get_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        user.is_active = not user.is_active
        return user_repo.update(db, user)

user_service = UserService()
