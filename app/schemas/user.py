from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from app.models.user import UserRole, KYCStatus

class UserBase(BaseModel):
    email: EmailStr
    full_name: str

class CustomerCreate(UserBase):
    mobile_number: str = Field(..., pattern=r"^\+?[1-9]\d{1,14}$|^[0-9]{10}$")
    password: str = Field(..., min_length=6)
    address: str

class AdminCreate(UserBase):
    password: str = Field(..., min_length=6)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenRefreshRequest(BaseModel):
    refresh_token: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: UserRole
    full_name: str
    email: str
    kyc_status: KYCStatus
    kyc_comments: Optional[str] = None

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    mobile_number: Optional[str] = None
    address: Optional[str] = None

class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6)

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=6)

class UserResponse(UserBase):
    id: int
    mobile_number: Optional[str] = None
    address: Optional[str] = None
    role: UserRole
    kyc_status: KYCStatus
    kyc_comments: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
