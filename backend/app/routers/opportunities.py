from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import get_current_user, require_role
from app.models.application import Application
from app.models.engineer import Engineer
from app.models.jd import JD, Match
from app.models.resume import Resume
from app.models.assessment import Assessment
from app.schemas.application import ApplicationCreate, ApplicationDetail, ApplicationOut, ApplicationStatusUpdate, OpportunityOut

router = APIRouter(tags=["opportunities"])


@router.get("/opportunities", response_model=List[OpportunityOut])
async def list_opportunities(db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    jds = (await db.execute(select(JD).where(JD.is_published.is_(True), JD.status == "published").order_by(JD.created_at.desc()))).scalars().all()
    applications = (await db.execute(select(Application).where(Application.engineer_id == current_user.id))).scalars().all()
    app_by_jd = {item.jd_id: item for item in applications}
    matches = (await db.execute(select(Match).where(Match.engineer_id == current_user.id))).scalars().all()
    match_by_jd = {item.jd_id: item.jd_match_score for item in matches}
    return [
        {**jd.__dict__, "application_status": app_by_jd.get(jd.id).status if app_by_jd.get(jd.id) else None, "match_score": match_by_jd.get(jd.id)}
        for jd in jds
    ]


@router.get("/opportunities/{jd_id}", response_model=OpportunityOut)
async def get_opportunity(jd_id: int, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    jd = (await db.execute(select(JD).where(JD.id == jd_id, JD.is_published.is_(True), JD.status == "published"))).scalar_one_or_none()
    if not jd:
        raise HTTPException(404, "Opportunity not found")
    application = (await db.execute(select(Application).where(Application.jd_id == jd_id, Application.engineer_id == current_user.id))).scalar_one_or_none()
    match = (await db.execute(select(Match).where(Match.jd_id == jd_id, Match.engineer_id == current_user.id))).scalar_one_or_none()
    return {**jd.__dict__, "application_status": application.status if application else None, "match_score": match.jd_match_score if match else None}


@router.post("/opportunities/{jd_id}/apply", response_model=ApplicationOut, status_code=201)
async def apply_to_opportunity(jd_id: int, payload: ApplicationCreate, db: AsyncSession = Depends(get_db), current_user=Depends(require_role("engineer"))):
    jd = (await db.execute(select(JD).where(JD.id == jd_id, JD.is_published.is_(True), JD.status == "published"))).scalar_one_or_none()
    if not jd:
        raise HTTPException(404, "Opportunity not found")
    existing = (await db.execute(select(Application).where(Application.jd_id == jd_id, Application.engineer_id == current_user.id))).scalar_one_or_none()
    if existing:
        raise HTTPException(409, "Already applied")
    resume = (await db.execute(select(Resume).where(Resume.engineer_id == current_user.id, Resume.is_active.is_(True)).order_by(Resume.uploaded_at.desc()))).scalar_one_or_none()
    match = (await db.execute(select(Match).where(Match.jd_id == jd_id, Match.engineer_id == current_user.id))).scalar_one_or_none()
    application = Application(jd_id=jd_id, engineer_id=current_user.id, resume_id=resume.id if resume else None, cover_note=payload.cover_note, match_score_snapshot=match.jd_match_score if match else None)
    db.add(application)
    await db.flush()
    return application


@router.get("/engineers/me/applications", response_model=List[ApplicationDetail])
async def my_applications(db: AsyncSession = Depends(get_db), current_user=Depends(require_role("engineer"))):
    rows = (await db.execute(select(Application, JD).join(JD, Application.jd_id == JD.id).where(Application.engineer_id == current_user.id).order_by(Application.applied_at.desc()))).all()
    return [{**application.__dict__, "client_name": jd.client_name, "raw_text": jd.raw_text, "capability_blueprint": jd.capability_blueprint, "engineer_name": current_user.name} for application, jd in rows]


@router.get("/engineers/me/applications/{application_id}", response_model=ApplicationDetail)
async def my_application(application_id: int, db: AsyncSession = Depends(get_db), current_user=Depends(require_role("engineer"))):
    row = (await db.execute(select(Application, JD).join(JD, Application.jd_id == JD.id).where(Application.id == application_id, Application.engineer_id == current_user.id))).first()
    if not row:
        raise HTTPException(404, "Application not found")
    application, jd = row
    return {**application.__dict__, "client_name": jd.client_name, "raw_text": jd.raw_text, "capability_blueprint": jd.capability_blueprint, "engineer_name": current_user.name}


@router.get("/admin/jds/{jd_id}/applications", response_model=List[ApplicationDetail])
async def jd_applications(jd_id: int, db: AsyncSession = Depends(get_db), _=Depends(require_role("admin", "leadership"))):
    rows = (await db.execute(select(Application, JD, Engineer).join(JD, Application.jd_id == JD.id).join(Engineer, Application.engineer_id == Engineer.id).where(Application.jd_id == jd_id).order_by(Application.applied_at.desc()))).all()
    return [{**application.__dict__, "client_name": jd.client_name, "raw_text": jd.raw_text, "capability_blueprint": jd.capability_blueprint, "engineer_name": engineer.name} for application, jd, engineer in rows]


@router.get("/admin/applications", response_model=List[ApplicationDetail])
async def all_applications(db: AsyncSession = Depends(get_db), _=Depends(require_role("admin", "leadership"))):
    rows = (await db.execute(select(Application, JD, Engineer).join(JD, Application.jd_id == JD.id).join(Engineer, Application.engineer_id == Engineer.id).order_by(Application.applied_at.desc()))).all()
    return [{**application.__dict__, "client_name": jd.client_name, "raw_text": jd.raw_text, "capability_blueprint": jd.capability_blueprint, "engineer_name": engineer.name} for application, jd, engineer in rows]


@router.patch("/admin/applications/{application_id}", response_model=ApplicationOut)
async def update_application(application_id: int, payload: ApplicationStatusUpdate, db: AsyncSession = Depends(get_db), current_user=Depends(require_role("admin", "leadership"))):
    allowed = {"applied", "under_review", "shortlisted", "assessment_pending", "assessment_completed", "selected", "rejected", "withdrawn"}
    if payload.status not in allowed:
        raise HTTPException(422, "Invalid application status")
    application = (await db.execute(select(Application).where(Application.id == application_id))).scalar_one_or_none()
    if not application:
        raise HTTPException(404, "Application not found")
    application.status = payload.status
    application.admin_notes = payload.admin_notes
    application.reviewed_by = current_user.id
    application.reviewed_at = datetime.now(timezone.utc)
    await db.flush()
    return application


@router.post("/admin/applications/{application_id}/assessment", status_code=201)
async def request_assessment(application_id: int, db: AsyncSession = Depends(get_db), _=Depends(require_role("admin", "leadership"))):
    application = (await db.execute(select(Application).where(Application.id == application_id))).scalar_one_or_none()
    if not application:
        raise HTTPException(404, "Application not found")
    existing = (await db.execute(select(Assessment).where(Assessment.application_id == application_id))).scalar_one_or_none()
    if existing:
        return {"assessment_id": existing.id, "status": existing.status}
    assessment = Assessment(engineer_id=application.engineer_id, jd_id=application.jd_id, application_id=application.id, status="pending")
    application.status = "assessment_pending"
    db.add(assessment)
    await db.flush()
    return {"assessment_id": assessment.id, "status": assessment.status}
