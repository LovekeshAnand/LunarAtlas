from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Any
from jose import JWTError, jwt

from app.schemas.auth import UserCreate, UserLogin, UserResponse, Token
from app.core.security import get_password_hash, verify_password, create_access_token
from app.database.connection import db
from app.config import settings

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> Any:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = await db.fetch_one("SELECT * FROM app_users WHERE email = $1", email)
    if user is None:
        raise credentials_exception
    return user

@router.post("/register", response_model=UserResponse)
async def register(user_in: UserCreate):
    """
    Register a new user.
    """
    # Check if user already exists
    exists = await db.fetch_one("SELECT id FROM app_users WHERE email = $1", user_in.email)
    if exists:
        raise HTTPException(
            status_code=400,
            detail="User with this email already exists."
        )
        
    hashed_pwd = get_password_hash(user_in.password)
    
    # Insert new user
    query = """
        INSERT INTO app_users (email, institution, interest, hashed_password)
        VALUES ($1, $2, $3, $4)
        RETURNING id, email, institution, interest
    """
    try:
        new_user = await db.fetch_one(
            query, 
            user_in.email, 
            user_in.institution, 
            user_in.interest, 
            hashed_pwd
        )
        return dict(new_user)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to register user")

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 compatible token login, retrieve an access token for future requests.
    """
    user = await db.fetch_one("SELECT * FROM app_users WHERE email = $1", form_data.username)
    if not user or not verify_password(form_data.password, user['hashed_password']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token = create_access_token(subject=user["email"])
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: Any = Depends(get_current_user)):
    """
    Get current logged in user.
    """
    return dict(current_user)
