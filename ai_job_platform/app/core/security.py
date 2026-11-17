"""
Production-grade authentication & security utilities.
- Secure bcrypt password hashing
- Signed JWT token creation and verification
- Google OAuth2 ID token verification
- FastAPI dependency for injecting the current authenticated user
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import bcrypt
import jwt
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.db_models import User

logger = logging.getLogger(__name__)

# Bearer token extractor (auto_error=False to support optional user / guests)
bearer_scheme = HTTPBearer(auto_error=False)


# ---------------------------------------------------------------------------
# Password Hashing & Verification (Bcrypt)
# ---------------------------------------------------------------------------

def hash_password(plain_password: str) -> str:
    """Hashes a plaintext password using bcrypt with salt rounds."""
    if not plain_password or len(plain_password) < 6:
        raise ValueError("Password must be at least 6 characters.")
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against a stored bcrypt hash."""
    if not plain_password or not hashed_password:
        return False
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception as e:
        logger.warning("Bcrypt password verification failed: %s", e)
        return False


# ---------------------------------------------------------------------------
# JWT Token Generation & Verification
# ---------------------------------------------------------------------------

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Encodes a signed JWT access token.
    Claims: sub (user_id), email, iat, exp.
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=settings.JWT_ACCESS_TOKEN_EXPIRE_DAYS)

    to_encode.update({
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    })

    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decodes and validates a signed JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_exp": True},
        )
        return payload
    except jwt.ExpiredSignatureError:
        logger.info("JWT token has expired.")
        return None
    except jwt.PyJWTError as e:
        logger.warning("JWT token decoding failed: %s", e)
        return None


# ---------------------------------------------------------------------------
# Google OAuth2 Token Verification
# ---------------------------------------------------------------------------

def verify_google_id_token(credential_jwt: str) -> Optional[Dict[str, Any]]:
    """
    Validates a Google ID Token (issued by Google Sign-In) against Google's public keys.
    In development mode (DEBUG=True), supports simulated dev credentials for local testing.
    """
    if settings.DEBUG and credential_jwt.startswith("dev-google-mock:"):
        parts = credential_jwt.split(":")
        mock_email = parts[1] if len(parts) > 1 and parts[1] else "alex.mercer@gmail.com"
        mock_name = parts[2] if len(parts) > 2 and parts[2] else "Alex Mercer"
        return {
            "google_sub": f"google_sub_{mock_email}",
            "email": mock_email,
            "full_name": mock_name,
            "avatar_url": "https://api.dicebear.com/7.x/avataaars/svg?seed=Alex",
            "email_verified": True,
        }

    try:
        client_id = settings.GOOGLE_CLIENT_ID or None
        id_info = google_id_token.verify_oauth2_token(
            credential_jwt,
            google_requests.Request(),
            audience=client_id,
        )
        # Google's user ID is in 'sub', email in 'email', name in 'name', avatar in 'picture'
        return {
            "google_sub": id_info.get("sub"),
            "email": id_info.get("email"),
            "full_name": id_info.get("name") or "",
            "avatar_url": id_info.get("picture") or "",
            "email_verified": id_info.get("email_verified", False),
        }
    except Exception as e:
        logger.warning("Google ID token verification failed: %s", e)
        return None


# ---------------------------------------------------------------------------
# FastAPI Auth Dependencies
# ---------------------------------------------------------------------------

async def get_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Strict dependency: Requires a valid Bearer JWT token.
    Raises 401 Unauthorized if missing, expired, or user not found.
    """
    if not auth or not auth.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(auth.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session token. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id_str = payload["sub"]
    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed user ID in session token.",
        )

    result = await db.execute(select(User).where(User.id == user_uuid, User.is_active == True))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found or has been deactivated.",
        )

    return user


async def get_optional_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """
    Flexible dependency: Returns User if valid Bearer token provided, otherwise None.
    Allows public / guest browsing while seamlessly associating data if logged in.
    """
    if not auth or not auth.credentials:
        return None

    payload = decode_access_token(auth.credentials)
    if not payload or "sub" not in payload:
        return None

    try:
        user_uuid = uuid.UUID(payload["sub"])
    except ValueError:
        return None

    result = await db.execute(select(User).where(User.id == user_uuid, User.is_active == True))
    return result.scalar_one_or_none()
