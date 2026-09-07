from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.core.db import get_db
from app.core.security import get_current_user, require_role
from app.models.jd import JD, Match
from app.models.engineer import Engineer
from app.schemas.jd import JDCreate, JDOut, JDMatchesOut, MatchOut
from app.agents.orchestrator import orchestrator

router = APIRouter(prefix="/jds", tags=["jds"])


@router.get("/", response_model=List[JDOut])
async def list_jds(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    res = await db.execute(select(JD).order_by(JD.created_at.desc()))
    return res.scalars().all()


@router.get("/{jd_id}", response_model=JDOut)
async def get_jd(jd_id: int, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    res = await db.execute(select(JD).where(JD.id == jd_id))
    jd = res.scalar_one_or_none()
    if not jd:
        raise HTTPException(404, "JD not found")
    return jd


@router.post("/", status_code=201)
async def create_jd(
    payload: JDCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin", "leadership")),
):
    result = await orchestrator.process_jd(payload.raw_text, payload.client_name, db)
    jd = (await db.execute(select(JD).where(JD.id == result["jd_id"]))).scalar_one()
    jd.posted_by = current_user.id
    jd.location = payload.location
    jd.employment_type = payload.employment_type
    return result


@router.patch("/{jd_id}/publish", response_model=JDOut)
async def publish_jd(jd_id: int, db: AsyncSession = Depends(get_db), _=Depends(require_role("admin", "leadership"))):
    jd = (await db.execute(select(JD).where(JD.id == jd_id))).scalar_one_or_none()
    if not jd:
        raise HTTPException(404, "JD not found")
    jd.status = "published"
    jd.is_published = True
    await db.flush()
    return jd


@router.patch("/{jd_id}/close", response_model=JDOut)
async def close_jd(jd_id: int, db: AsyncSession = Depends(get_db), _=Depends(require_role("admin", "leadership"))):
    jd = (await db.execute(select(JD).where(JD.id == jd_id))).scalar_one_or_none()
    if not jd:
        raise HTTPException(404, "JD not found")
    jd.status = "closed"
    jd.is_published = False
    await db.flush()
    return jd


@router.get("/{jd_id}/matches", response_model=JDMatchesOut)
async def get_matches(jd_id: int, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    jd_res = await db.execute(select(JD).where(JD.id == jd_id))
    jd = jd_res.scalar_one_or_none()
    if not jd:
        raise HTTPException(404, "JD not found")

    matches_res = await db.execute(
        select(Match, Engineer)
        .join(Engineer, Match.engineer_id == Engineer.id)
        .where(Match.jd_id == jd_id)
        .order_by(Match.jd_match_score.desc())
    )
    candidates = [
        MatchOut(
            engineer_id=eng.id,
            engineer_name=eng.name,
            jd_match_score=m.jd_match_score,
            breakdown=m.breakdown,
            explanation=m.explanation,
        )
        for m, eng in matches_res.all()
    ]
    return JDMatchesOut(jd_id=jd_id, client_name=jd.client_name, candidates=candidates)
