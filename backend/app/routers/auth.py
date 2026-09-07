from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.db import get_db
from app.core.security import verify_password, hash_password, create_access_token
from app.models.engineer import Engineer
from app.schemas.auth import Token, LoginRequest
from app.schemas.engineer import EngineerCreate, EngineerOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=EngineerOut, status_code=201)
async def register(payload: EngineerCreate, db: AsyncSession = Depends(get_db)):
    """Public registration always creates an engineer account.

    Privileged roles must be provisioned through an administrative workflow;
    accepting role from an unauthenticated request would allow privilege escalation.
    """
    res = await db.execute(select(Engineer).where(Engineer.email == payload.email))
    if res.scalar_one_or_none():
        raise HTTPException(400, "Email already registered")
    eng = Engineer(
        name=payload.name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role="engineer",
        seniority=payload.seniority,
        bio=payload.bio,
    )
    db.add(eng)
    await db.flush()
    return eng


@router.post("/login", response_model=Token)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Engineer).where(Engineer.email == payload.email))
    user = res.scalar_one_or_none()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token({"sub": user.email, "role": user.role})
    return Token(access_token=token)
