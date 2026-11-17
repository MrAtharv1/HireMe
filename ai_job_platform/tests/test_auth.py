"""
Tests for Authentication & Security Layer.
Verifies:
- Bcrypt hashing & verification
- JWT token encoding, decoding, and expiration
- User registration and login flow
- Duplicate email rejection
- Password validation
"""

import pytest
import uuid
from datetime import timedelta
from fastapi import HTTPException

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)
from app.core.database import async_session_factory, init_db
from app.schemas.auth_dto import RegisterRequest, LoginRequest
from app.routers.auth import register, login


def test_password_hashing():
    pw = "SuperSecretPassword123!"
    hashed = hash_password(pw)
    assert hashed != pw
    assert verify_password(pw, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_jwt_token_creation_and_validation():
    data = {"sub": "123e4567-e89b-12d3-a456-426614174000", "email": "test@example.com"}
    token = create_access_token(data, expires_delta=timedelta(minutes=15))
    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded["sub"] == data["sub"]
    assert decoded["email"] == data["email"]


def test_expired_jwt_token():
    data = {"sub": "123e4567-e89b-12d3-a456-426614174000"}
    token = create_access_token(data, expires_delta=timedelta(seconds=-10))
    decoded = decode_access_token(token)
    assert decoded is None


@pytest.mark.asyncio
async def test_auth_router_flow():
    await init_db()
    async with async_session_factory() as db:
        unique_email = f"user_{uuid.uuid4().hex[:8]}@example.com"
        password = "SecurePassword123!"

        # 1. Register new user
        reg_req = RegisterRequest(
            email=unique_email,
            password=password,
            full_name="Alex Turner"
        )
        auth_resp = await register(reg_req, db=db)
        assert auth_resp.access_token is not None
        assert auth_resp.user.email == unique_email
        assert auth_resp.user.full_name == "Alex Turner"

        # 2. Duplicate registration raises 409 Conflict
        with pytest.raises(HTTPException) as exc_info:
            await register(reg_req, db=db)
        assert exc_info.value.status_code == 409

        # 3. Successful login
        login_req = LoginRequest(email=unique_email, password=password)
        login_resp = await login(login_req, db=db)
        assert login_resp.access_token is not None
        assert login_resp.user.email == unique_email

        # 4. Incorrect password raises 401 Unauthorized
        bad_login = LoginRequest(email=unique_email, password="WrongPassword!")
        with pytest.raises(HTTPException) as exc_bad:
            await login(bad_login, db=db)
        assert exc_bad.value.status_code == 401
