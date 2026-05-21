import secrets
from datetime import timedelta, datetime
from typing import Union, Any

import bcrypt
from jose import jwt
from pytz import utc

from config.config import ACCESS_SECRET_KEY, ACCESS_TOKEN_ALGORITHM, REFRESH_SECRET_KEY, REFRESH_TOKEN_ALGORITHM


async def hash_password(plain_password: str) -> str:
    """
    Hashes a plaintext password using bcrypt.

    Args:
        plain_password (str): The user's raw password input.

    Returns:
        str: The bcrypt hashed password, encoded as a UTF-8 string.
    """
    password_bytes = plain_password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


async def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plaintext password against a stored bcrypt hash.

    Args:
        plain_password (str): The raw password input.
        hashed_password (str): The stored hashed password.

    Returns:
        bool: True if passwords match, False otherwise.
    """
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)


async def create_access_token(subject: Union[str, Any], expires_delta: timedelta, permissions: list[str]) -> str:
    """Create a JWT access token."""

    expire = datetime.now(utc) + expires_delta

    to_encode = {"exp": expire, "sub": str(subject), "type": "access", "permissions": permissions}
    encoded_jwt = jwt.encode(to_encode, ACCESS_SECRET_KEY, algorithm=ACCESS_TOKEN_ALGORITHM)
    return encoded_jwt


async def create_refresh_token(subject: Union[str, Any], expires_delta: timedelta) -> tuple[str, datetime]:
    """Create a JWT refresh token."""

    expire = datetime.now(utc) + expires_delta

    # Add jitter to prevent token reuse and timing attacks
    jitter = secrets.randbelow(3600)  # Random seconds up to an hour
    expire = expire + timedelta(seconds=jitter)

    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    encoded_jwt = jwt.encode(to_encode, REFRESH_SECRET_KEY, algorithm=REFRESH_TOKEN_ALGORITHM)
    return encoded_jwt, expire


async def decode_token(token: str, token_type: str = "access") -> dict:
    """Decode and validate a JWT token."""
    if token_type == "access":
        return jwt.decode(token, ACCESS_SECRET_KEY, algorithms=[ACCESS_TOKEN_ALGORITHM])
    elif token_type == "refresh":
        return jwt.decode(token, REFRESH_SECRET_KEY, algorithms=[REFRESH_TOKEN_ALGORITHM])
    else:
        raise ValueError("Invalid token type")
