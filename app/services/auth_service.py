"""Auth service layer for OTP, JWT, and user management."""
import hashlib
import random
import string
from datetime import datetime, timedelta
from typing import Optional, Tuple
from uuid import UUID, uuid4

from sqlalchemy.orm import Session
from jose import JWTError, jwt

from app.core.config import get_settings
from app.core.security import get_password_hash, verify_password, create_access_token, ALGORITHM, ALGORITHM
from app.models import User, AuthorityUser, OTPStore

settings = get_settings()


def hash_phone(phone: str) -> str:
    """Consistent phone hashing for OTP store lookup."""
    return hashlib.sha256(phone.encode()).hexdigest()[:32]


def generate_otp() -> str:
    """Generate 6-digit OTP."""
    return "".join(random.choices(string.digits, k=6))


def create_otp_record(db: Session, phone: str) -> Tuple[str, datetime]:
    """Create OTP record, return (otp, expires_at)."""
    phone_hash = hash_phone(phone)
    otp = generate_otp()
    
    # Delete old OTPs for this phone
    db.query(OTPStore).filter(OTPStore.phone_hash == phone_hash).delete()
    
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    
    otp_record = OTPStore(
        phone_hash=phone_hash,
        otp_code=otp,
        expires_at=expires_at,
    )
    db.add(otp_record)
    db.commit()
    
    return otp, expires_at


def verify_otp_code(db: Session, phone: str, otp: str) -> bool:
    """Verify OTP code against stored record."""
    phone_hash = hash_phone(phone)
    
    record = db.query(OTPStore).filter(
        OTPStore.phone_hash == phone_hash,
        OTPStore.otp_code == otp,
        OTPStore.expires_at > datetime.utcnow(),
        OTPStore.is_used == False,
    ).first()
    
    if not record:
        return False
    
    record.is_used = True
    db.commit()
    return True


def get_or_create_user(db: Session, phone: str) -> Tuple[User, bool]:
    """Get existing user or create new one. Returns (user, is_new)."""
    user = db.query(User).filter(User.phone_hash == hash_phone(phone)).first()
    
    if user:
        return user, False
    
    # Create new user with pseudonym
    pseudonym = f"citizen_{random.randint(100000, 999999)}"
    user = User(
        id=uuid4(),
        phone_hash=hash_phone(phone),
        pseudonym=pseudonym,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user, True


def create_citizen_tokens(user_id: UUID) -> Tuple[str, str]:
    """Create access and refresh tokens for citizen."""
    access_token = create_access_token(
        data={"sub": str(user_id), "type": "citizen"},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    refresh_token = create_access_token(
        data={"sub": str(user_id), "type": "citizen", "refresh": True},
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    return access_token, refresh_token


def authenticate_authority(db: Session, email: str, password: str) -> Optional[AuthorityUser]:
    """Authenticate authority user by email/password."""
    user = db.query(AuthorityUser).filter(
        AuthorityUser.email == email,
        AuthorityUser.is_active == True,
    ).first()
    
    if not user:
        return None
    
    if not verify_password(password, user.password_hash):
        return None
    
    return user


def create_authority_tokens(user: AuthorityUser) -> Tuple[str, str]:
    """Create access and refresh tokens for authority user."""
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "type": "authority",
            "role": user.role,
            "authority_id": str(user.authority_id),
        },
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    refresh_token = create_access_token(
        data={
            "sub": str(user.id),
            "type": "authority",
            "refresh": True,
            "authority_id": str(user.authority_id),
        },
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    return access_token, refresh_token


def get_current_user_from_token(db: Session, token: str) -> Optional[dict]:
    """Decode token and return user info dict."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        user_type: str = payload.get("type")
        
        if user_id is None or user_type is None:
            return None
        
        if user_type == "citizen":
            user = db.query(User).filter(User.id == UUID(user_id)).first()
            if not user:
                return None
            return {
                "id": user.id,
                "type": "citizen",
                "pseudonym": user.pseudonym,
            }
        
        elif user_type == "authority":
            user = db.query(AuthorityUser).filter(AuthorityUser.id == UUID(user_id)).first()
            if not user:
                return None
            return {
                "id": user.id,
                "type": "authority",
                "name": user.name,
                "email": user.email,
                "role": user.role,
                "authority_id": user.authority_id,
                "ward_id": user.ward_id,
            }
        
        return None
        
    except JWTError:
        return None
