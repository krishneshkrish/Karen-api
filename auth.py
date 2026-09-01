from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr
from app.core.security import hash_password, verify_password, hash_user_id, create_access_token
from app.core.database import get_supabase
import logging

router = APIRouter(prefix="/auth", tags=["Auth"])
logger = logging.getLogger(__name__)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_hash: str             # Client stores this locally to identify the user


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest):
    db = get_supabase()
    user_hash = hash_user_id(payload.email)

    # Check if user already exists
    existing = db.table("users").select("user_hash").eq("user_hash", user_hash).execute()
    if existing.data:
        raise HTTPException(status_code=409, detail="Account already exists")

    hashed_pw = hash_password(payload.password)

    db.table("users").insert({
        "user_hash": user_hash,
        "password_hash": hashed_pw,
    }).execute()

    token = create_access_token(user_hash)
    logger.info(f"New user registered: {user_hash[:8]}...")
    return AuthResponse(access_token=token, user_hash=user_hash)


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginRequest):
    db = get_supabase()
    user_hash = hash_user_id(payload.email)

    result = db.table("users").select("user_hash, password_hash").eq("user_hash", user_hash).execute()
    if not result.data:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user = result.data[0]
    if not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(user_hash)
    return AuthResponse(access_token=token, user_hash=user_hash)
