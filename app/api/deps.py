from typing import Optional
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import decode_access_token

security = HTTPBearer(auto_error=False)


async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> str:
    """Dependency that verifies JWT Bearer token and returns user_hash, or falls back to guest user."""
    if credentials and credentials.credentials:
        token = credentials.credentials
        user_hash = decode_access_token(token)
        if user_hash:
            return user_hash
    return "guest_user"
