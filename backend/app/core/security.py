
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pwdlib import PasswordHash

from .config import get_settings
from .db import get_db


settings = get_settings()

# Password hashing
# Uses Argon2, which avoids the Passlib + bcrypt compatibility
# problems you're currently seeing.
password_hash = PasswordHash.recommended()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain-text password against its stored hash."""
    return password_hash.verify(plain, hashed)


def hash_password(plain: str) -> str:
    """Hash a plain-text password."""
    return password_hash.hash(plain)


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + (
        expires_delta
        or timedelta(minutes=settings.access_token_expire_minutes)
    )

    to_encode.update({"exp": expire})

    return jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm,
    )


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    from app.models.engineer import Engineer

    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )

        email = payload.get("sub")

        if email is None:
            raise credentials_exc

    except JWTError:
        raise credentials_exc

    result = await db.execute(
        select(Engineer).where(Engineer.email == email)
    )

    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exc

    return user


def require_role(*roles: str):
    """Require the authenticated user to have one of the specified roles."""

    async def _check(
        current_user=Depends(get_current_user),
    ):
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

        return current_user

    return _check
