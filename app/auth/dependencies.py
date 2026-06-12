from typing import Optional
from fastapi import Request, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.core.security import decode_token
from app.services.user_service import user_repo
from app.models.user import User, UserRole

class UnauthenticatedException(Exception):
    """Exception raised when page routes are accessed by unauthenticated users."""
    pass

class UnauthorizedAdminException(Exception):
    """Exception raised when admin pages are accessed by customer users."""
    pass

def get_current_user_optional(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    token = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    
    if not token:
        token = request.cookies.get("access_token")
        
    if not token:
        return None
        
    user_id_str = decode_token(token, is_refresh=False)
    if not user_id_str:
        return None
        
    try:
        user_id = int(user_id_str)
    except ValueError:
        return None
        
    user = user_repo.get_by_id(db, user_id)
    if not user or not user.is_active:
        return None
        
    return user

def get_current_user_api(request: Request, db: Session = Depends(get_db)) -> User:
    user = get_current_user_optional(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    return user

def get_current_admin_api(current_user: User = Depends(get_current_user_api)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Unauthorized - Admins only")
    return current_user

# Jinja2 HTML Page Dependencies
def get_current_user_page(request: Request, db: Session = Depends(get_db)) -> User:
    user = get_current_user_optional(request, db)
    if not user:
        raise UnauthenticatedException()
    return user

def get_current_admin_page(user: User = Depends(get_current_user_page)) -> User:
    if user.role != UserRole.ADMIN:
        raise UnauthorizedAdminException()
    return user

