from datetime import datetime, timedelta

import bcrypt
import jwt

from .config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_ALGORITHM,
    JWT_SECRET_KEY,
    REFRESH_TOKEN_EXPIRE_DAYS,
)


class AuthService:
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a plain password against its bcrypt hash."""
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), 
            hashed_password.encode("utf-8")
        )

    @staticmethod
    def create_access_token(data: dict) -> str:
        """Generate a JWT access token containing the payload and expiration time."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire, "token_type": "access"})
        encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        return encoded_jwt

    @staticmethod
    def create_refresh_token(data: dict) -> str:
        """Generate a long-lived token used only to renew an access token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "token_type": "refresh"})
        return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    @staticmethod
    def decode_access_token(token: str) -> dict | None:
        """Decode and validate a JWT access token."""
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            return payload if payload.get("token_type", "access") == "access" else None
        except jwt.ExpiredSignatureError:
            # Token expired
            return None
        except jwt.InvalidTokenError:
            # Invalid token
            return None

    @staticmethod
    def decode_refresh_token(token: str) -> dict | None:
        """Decode a refresh token without accepting an access token in its place."""
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            return payload if payload.get("token_type") == "refresh" else None
        except jwt.PyJWTError:
            return None
