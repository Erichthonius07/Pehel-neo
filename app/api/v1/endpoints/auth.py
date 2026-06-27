"""Auth endpoints for citizens (OTP) and authorities (password)."""
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import Optional

from app.db.base import get_db
from app.services.auth_service import (
    create_otp_record,
    verify_otp_code,
    get_or_create_user,
    create_citizen_tokens,
    authenticate_authority,
    create_authority_tokens,
    get_current_user_from_token,
)
from app.schemas.auth import (
    PhoneRequest,
    OTPVerifyRequest,
    TokenResponse,
    AuthorityLoginRequest,
    AuthorityTokenResponse,
    MeResponse,
    OTPResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/send-otp", response_model=OTPResponse)
def send_otp(request: PhoneRequest, db: Session = Depends(get_db)):
    """Send OTP to phone number (mocked — returns OTP in response)."""
    otp, expires_at = create_otp_record(db, request.phone)
    return OTPResponse(
        message="OTP sent successfully",
        otp=otp,
        expires_in=600,  # 10 minutes
    )


@router.post("/verify-otp", response_model=TokenResponse)
def verify_otp(request: OTPVerifyRequest, db: Session = Depends(get_db)):
    """Verify OTP and return JWT tokens."""
    if not verify_otp_code(db, request.phone, request.otp):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired OTP",
        )
    
    user, is_new = get_or_create_user(db, request.phone)
    access_token, refresh_token = create_citizen_tokens(user.id)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        is_new_user=is_new,
    )


@router.post("/authority/login", response_model=AuthorityTokenResponse)
def authority_login(request: AuthorityLoginRequest, db: Session = Depends(get_db)):
    """Authority user login with email/password."""
    user = authenticate_authority(db, request.email, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    
    access_token, refresh_token = create_authority_tokens(user)
    
    return AuthorityTokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        authority_id=user.authority_id,
        role=user.role,
    )


@router.get("/me", response_model=MeResponse)
def get_me(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """Get current user from JWT token."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
        )
    
    token = authorization.replace("Bearer ", "")
    user = get_current_user_from_token(db, token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    
    return MeResponse(**user)
