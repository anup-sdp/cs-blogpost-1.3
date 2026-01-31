# auth.py
from datetime import UTC, datetime, timedelta

import jwt
from fastapi.security import OAuth2PasswordBearer # OAuth2 
from pwdlib import PasswordHash

from config import settings

password_hash = PasswordHash.recommended()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/users/token")


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(
            minutes=settings.access_token_expire_minutes,
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key.get_secret_value(),
        algorithm=settings.algorithm,
    )
    return encoded_jwt


def verify_access_token(token: str) -> str | None:
    """Verify a JWT access token and return the subject (user id) if valid."""
    try:
        payload = jwt.decode(
            token,
            settings.secret_key.get_secret_value(),
            algorithms=[settings.algorithm],
            options={"require": ["exp", "sub"]},
        )
    except jwt.InvalidTokenError:
        return None
    else:
        return payload.get("sub")
    


"""
OAuth2:
OAuth 2.0 is an authorization framework,  It allows applications to obtain limited access to user accounts on an HTTP service.
(for 3rd-party clients, Social login, Public API)
In FastAPI, OAuth2 is a standard way to handle authentication and authorization using access tokens—usually Bearer tokens sent in the Authorization header.
rules for how a user proves who they are and what they're allowed to do, without sharing passwords with every app.

flow -> 
User logs in with username/password, 
Server verifies credentials, 
Server issues an access token (usually a JWT), 
Client sends this token with every request: Authorization: Bearer <token>

for user authorization, although FastAPI 'recommend' OAuth2, using JWT alone is perfectly fine.
OAuth2 gives: Swagger UI login button 🔐, Standardized error handling, Cleaner dependency helpers, Easier future expansion.
Smart middle ground: JWT + OAuth2PasswordBearer. (not implementing full OAuth2, use OAuth2 as a wrapper for JWT)

OAuth2PasswordRequestForm  → login
OAuth2PasswordBearer      → protected routes
OAuth2PasswordBearer: 
A dependency that looks for a Bearer token in the Authorization header of incoming requests. Extracts the token, Raises 401 if missing
"""