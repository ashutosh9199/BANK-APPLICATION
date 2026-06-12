from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.security import decode_token
from app.modules.users.models import User, UserRole
from app.modules.users.schemas import (
    CustomerCreate,
    AdminCreate,
    LoginRequest,
    TokenResponse,
    TokenRefreshRequest,
    UserResponse,
    UserUpdate,
    PasswordChange,
    ForgotPasswordRequest,
    ResetPasswordRequest
)
from app.modules.users.service import user_service
from app.modules.users.repository import user_repo

router = APIRouter(prefix="/users", tags=["Users"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/users/login")

def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    user_id_str = decode_token(token, is_refresh=False)
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        user_id = int(user_id_str)
    except ValueError:
         raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials payload",
        )
    user = user_repo.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return user

def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions - Admin role required"
        )
    return current_user

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_customer(schema: CustomerCreate, db: Session = Depends(get_db)):
    return user_service.register_customer(db, schema)

@router.post("/register-admin", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_admin(schema: AdminCreate, db: Session = Depends(get_db)):
    return user_service.register_admin(db, schema)

@router.post("/login", response_model=TokenResponse)
def login(schema: LoginRequest, db: Session = Depends(get_db)):
    return user_service.login(db, schema)

@router.post("/refresh")
def refresh_token(schema: TokenRefreshRequest, db: Session = Depends(get_db)):
    return user_service.refresh_access_token(db, schema.refresh_token)

@router.get("/profile", response_model=UserResponse)
def get_profile(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/profile", response_model=UserResponse)
def update_profile(schema: UserUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return user_service.update_profile(db, current_user, schema)

@router.post("/change-password")
def change_password(schema: PasswordChange, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user_service.change_password(db, current_user, schema)
    return {"message": "Password changed successfully"}

@router.post("/forgot-password")
def forgot_password(schema: ForgotPasswordRequest, db: Session = Depends(get_db)):
    token = user_service.forgot_password(db, schema.email)
    return {
        "message": "Password reset token simulated and printed to server console.",
        "token": token # Expose token for frontend convenience in our monolithic build
    }

@router.post("/reset-password")
def reset_password(schema: ResetPasswordRequest, db: Session = Depends(get_db)):
    message = user_service.reset_password(db, schema)
    return {"message": message}

# Admin Endpoints
@router.get("/admin/users", response_model=List[UserResponse])
def get_all_users(admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    return user_service.list_users(db)

@router.post("/admin/users/{user_id}/toggle-active", response_model=UserResponse)
def toggle_user_active(user_id: int, admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    return user_service.toggle_user_active(db, user_id)
