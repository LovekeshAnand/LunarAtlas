from pydantic import BaseModel, EmailStr
from typing import Optional

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenPayload(BaseModel):
    sub: Optional[str] = None

class UserBase(BaseModel):
    email: EmailStr
    institution: Optional[str] = None
    interest: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserInDB(UserBase):
    id: int
    hashed_password: str

class UserResponse(UserBase):
    id: int
    role: Optional[str] = "researcher"
    created_at: Optional[str] = None
    api_key_count: Optional[int] = 0
    
    class Config:
        from_attributes = True

class UserProfileUpdate(BaseModel):
    role: Optional[str] = None
    institution: Optional[str] = None
    interest: Optional[str] = None
