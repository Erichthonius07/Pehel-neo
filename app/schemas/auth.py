from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID

class PhoneRequest(BaseModel):
    phone: str = Field(..., pattern=r'^\+91[0-9]{10}$')

class OTPVerifyRequest(BaseModel):
    phone: str = Field(..., pattern=r'^\+91[0-9]{10}$')
    otp: str = Field(..., pattern=r'^[0-9]{6}$')

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    is_new_user: bool

class AuthorityLoginRequest(BaseModel):
    email: str
    password: str

class AuthorityTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    authority_id: UUID
    role: str

class MeResponse(BaseModel):
    id: UUID
    type: str
    pseudonym: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    authority_id: Optional[UUID] = None
    ward_id: Optional[UUID] = None

class OTPResponse(BaseModel):
    message: str
    otp: str
    expires_in: int
