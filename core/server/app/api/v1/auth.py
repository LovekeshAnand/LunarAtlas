from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Any
from jose import JWTError, jwt
import logging

from app.schemas.auth import UserCreate, UserLogin, UserResponse, Token, UserProfileUpdate
from app.core.security import get_password_hash, verify_password, create_access_token
from app.database.connection import db
from app.config import settings

logger = logging.getLogger(__name__)

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
        
    # Check if username already exists
    if user_in.username and user_in.username.strip():
        username_clean = user_in.username.strip()
        exists_username = await db.fetch_one("SELECT id FROM app_users WHERE username = $1", username_clean)
        if exists_username:
            raise HTTPException(
                status_code=400,
                detail="User with this username already exists."
            )
            
    hashed_pwd = get_password_hash(user_in.password)
    
    # Insert new user
    query = """
        INSERT INTO app_users (email, username, role, institution, interest, hashed_password)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING id, email, username, role, institution, interest, created_at::text
    """
    try:
        new_user = await db.fetch_one(
            query, 
            user_in.email, 
            user_in.username.strip() if user_in.username else None,
            user_in.role.strip() if user_in.role else "researcher",
            user_in.institution, 
            user_in.interest, 
            hashed_pwd
        )
        user_dict = dict(new_user)
        user_dict["api_key_count"] = 0
        return user_dict
    except Exception as e:
        logger.error(f"Failed to register user: {e}")
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
    user_dict = dict(current_user)
    # Get active api keys count
    count_row = await db.fetch_one(
        "SELECT COUNT(*) AS cnt FROM api_keys WHERE user_id = $1 AND is_active = TRUE",
        user_dict["id"]
    )
    user_dict["api_key_count"] = count_row["cnt"] if count_row else 0
    user_dict["created_at"] = str(user_dict["created_at"]) if user_dict.get("created_at") else None
    return user_dict

@router.patch("/profile", response_model=UserResponse)
async def update_profile(
    body: UserProfileUpdate,
    current_user: Any = Depends(get_current_user)
):
    """
    Update profile details for the authenticated user.
    """
    user_id = current_user["id"]
    
    # Build dynamic update query
    updates = []
    params = []
    param_idx = 1
    
    if body.role is not None:
        updates.append(f"role = ${param_idx}")
        params.append(body.role)
        param_idx += 1
        
    if body.institution is not None:
        updates.append(f"institution = ${param_idx}")
        params.append(body.institution)
        param_idx += 1
        
    if body.interest is not None:
        updates.append(f"interest = ${param_idx}")
        params.append(body.interest)
        param_idx += 1
        
    if not updates:
        # No updates requested, just return the current user
        return await read_users_me(current_user)
        
    query = f"""
        UPDATE app_users
        SET {", ".join(updates)}
        WHERE id = ${param_idx}
        RETURNING id, email, username, role, institution, interest, created_at::text
    """
    params.append(user_id)
    
    try:
        updated_row = await db.fetch_one(query, *params)
        if not updated_row:
            raise HTTPException(status_code=404, detail="User not found")
            
        user_dict = dict(updated_row)
        
        # Get active api keys count
        count_row = await db.fetch_one(
            "SELECT COUNT(*) AS cnt FROM api_keys WHERE user_id = $1 AND is_active = TRUE",
            user_id
        )
        user_dict["api_key_count"] = count_row["cnt"] if count_row else 0
        return user_dict
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to update profile info")
