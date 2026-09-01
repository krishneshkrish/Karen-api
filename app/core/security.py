import hmac
import hashlib
import bcrypt
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from app.core.config import settings


# ── Password hashing ──────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    """Hashes password using bcrypt with 72-byte truncation safety."""
    pwd_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verifies plain password against hashed password."""
    pwd_bytes = plain.encode("utf-8")[:72]
    hashed_bytes = hashed.encode("utf-8")
    return bcrypt.checkpw(pwd_bytes, hashed_bytes)


# ── User ID hashing ───────────────────────────────────────────────────────────
# We store a deterministic HMAC hash of the user's email as their cloud ID.
# Raw email never leaves the backend after registration.

def hash_user_id(email: str) -> str:
    """HMAC-SHA256 hash of email — used as the Supabase user identifier."""
    return hmac.new(
        settings.secret_key.encode(),
        email.lower().strip().encode(),
        hashlib.sha256,
    ).hexdigest()


# ── JWT ───────────────────────────────────────────────────────────────────────

def create_access_token(user_hash: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {"sub": user_hash, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> str | None:
    """Returns user_hash if valid, None if invalid/expired."""
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.jwt_algorithm]
        )
        return payload.get("sub")
    except JWTError:
        return None
