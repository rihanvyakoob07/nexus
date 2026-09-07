from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
from app.core.db import get_db
from app.core.security import get_current_user, require_self_or_role
from app.models.engineer import Engineer, EngineerSkill, Skill, Evidence
from app.models.gap_learning import SkillGap, LearningPath
from app.models.assessment import Assessment
from app.models.outcome import Deployment
from app.schemas.engineer import EngineerOut, EngineerPassport, EngineerSkillOut, EvidenceOut, CertificationOut, EngineerProfileUpdate
from app.schemas.team import GapOut, LearningPathCreate
from app.schemas.assessment import AssessmentOut
from app.services.confidence_scoring import compute_confidence
from app.agents import learning_agent

router = APIRouter(prefix="/engineers", tags=["engineers"])


@router.patch("/me", response_model=EngineerOut)
async def update_my_profile(payload: EngineerProfileUpdate, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(current_user, field, value)
    await db.flush()
    return current_user


@router.get("/", response_model=List[EngineerOut])
async def list_engineers(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    result = await db.execute(select(Engineer))
    return result.scalars().all()


@router.get("/{engineer_id}", response_model=EngineerPassport)
async def get_engineer(engineer_id: int, db: AsyncSession = Depends(get_db), _=Depends(require_self_or_role("admin", "leadership"))):
    res = await db.execute(select(Engineer).where(Engineer.id == engineer_id))
    eng = res.scalar_one_or_none()
    if not eng:
        raise HTTPException(404, "Engineer not found")

    skills_res = await db.execute(
        select(EngineerSkill, Skill)
        .join(Skill, EngineerSkill.skill_id == Skill.id)
        .where(EngineerSkill.engineer_id == engineer_id)
    )
    skills_data = skills_res.all()

    evidence_res = await db.execute(select(Evidence).where(Evidence.engineer_id == engineer_id))
    evidence_list = evidence_res.scalars().all()

    from app.models.project import Certification
    cert_res = await db.execute(select(Certification).where(Certification.engineer_id == engineer_id))
    certs = cert_res.scalars().all()

    skills_out = []
    for es, sk in skills_data:
        ev_for_skill = [e for e in evidence_list if e.skill_id == es.skill_id]
        confidence = compute_confidence(es.claimed_score, es.source, ev_for_skill)
        skills_out.append(EngineerSkillOut(
            skill_id=sk.id,
            skill=sk,
            claimed_score=es.claimed_score,
            confidence_score=confidence,
            source=es.source,
            last_updated=es.last_updated,
        ))

    return {**eng.__dict__, "skills": skills_out, "evidence": evidence_list, "certifications": certs}


@router.get("/{engineer_id}/gaps", response_model=List[GapOut])
async def get_gaps(engineer_id: int, jd_id: int = None, db: AsyncSession = Depends(get_db), _=Depends(require_self_or_role("admin", "leadership"))):
    query = select(SkillGap, Skill).join(Skill, SkillGap.skill_id == Skill.id).where(SkillGap.engineer_id == engineer_id)
    if jd_id:
        query = query.where(SkillGap.jd_id == jd_id)
    res = await db.execute(query)
    return [GapOut(skill_id=sk.id, skill_name=sk.name, severity=sg.severity, current_score=sg.current_score, target_score=sg.target_score) for sg, sk in res.all()]


@router.get("/{engineer_id}/assessments", response_model=List[AssessmentOut])
async def get_assessments(engineer_id: int, db: AsyncSession = Depends(get_db), _=Depends(require_self_or_role("admin", "leadership"))):
    res = await db.execute(
        select(Assessment).options(selectinload(Assessment.turns)).where(Assessment.engineer_id == engineer_id)
    )
    return res.scalars().all()


@router.get("/{engineer_id}/deployments")
async def get_deployments(engineer_id: int, db: AsyncSession = Depends(get_db), _=Depends(require_self_or_role("admin", "leadership"))):
    res = await db.execute(
        select(Deployment).where(Deployment.engineer_id == engineer_id).order_by(Deployment.start_date.desc(), Deployment.id.desc())
    )
    return [
        {
            "id": deployment.id,
            "engineer_id": deployment.engineer_id,
            "jd_id": deployment.jd_id,
            "team_id": deployment.team_id,
            "start_date": deployment.start_date,
            "end_date": deployment.end_date,
            "predicted_readiness_score": deployment.predicted_readiness_score,
        }
        for deployment in res.scalars().all()
    ]


@router.post("/{engineer_id}/learning-path")
async def generate_learning_path(engineer_id: int, payload: LearningPathCreate, db: AsyncSession = Depends(get_db), _=Depends(require_self_or_role("admin", "leadership"))):
    from app.models.jd import JD
    from app.services.capability_graph import get_all_engineers_skill_map

    res = await db.execute(select(Engineer).where(Engineer.id == engineer_id))
    eng = res.scalar_one_or_none()
    if not eng:
        raise HTTPException(404, "Engineer not found")

    skill_map = await get_all_engineers_skill_map(db)
    profile = {"id": eng.id, "name": eng.name, "seniority": eng.seniority, "skills": skill_map.get(eng.id, [])}

    gap_query = select(SkillGap, Skill).join(Skill).where(SkillGap.engineer_id == engineer_id)
    if payload.jd_id:
        gap_query = gap_query.where(SkillGap.jd_id == payload.jd_id)
    gap_res = await db.execute(gap_query)
    gaps = [{"skill": sk.name, "current_score": sg.current_score, "target_score": sg.target_score, "severity": sg.severity} for sg, sk in gap_res.all()]

    if not gaps:
        raise HTTPException(400, "No gaps found to generate a learning path for")

    plan = await learning_agent.run(gaps, profile, db)

    from datetime import datetime, timezone, timedelta
    weeks = plan.get("projected_readiness_date_weeks", 8)
    readiness_date = datetime.now(timezone.utc) + timedelta(weeks=weeks)

    lp = LearningPath(
        engineer_id=engineer_id,
        plan=plan,
        projected_readiness_date=readiness_date,
        projected_readiness_score=plan.get("projected_final_score"),
    )
    db.add(lp)
    await db.flush()
    return {"learning_path_id": lp.id, "plan": plan}


@router.get("/{engineer_id}/learning-path")
async def get_learning_path(engineer_id: int, db: AsyncSession = Depends(get_db), _=Depends(require_self_or_role("admin", "leadership"))):
    result = await db.execute(
        select(LearningPath).where(LearningPath.engineer_id == engineer_id).order_by(LearningPath.created_at.desc()).limit(1)
    )
    learning_path = result.scalar_one_or_none()
    if not learning_path:
        raise HTTPException(404, "Learning path not found")
    return {
        "learning_path_id": learning_path.id,
        "plan": learning_path.plan or {},
        "status": learning_path.status,
        "projected_readiness_date": learning_path.projected_readiness_date,
        "projected_readiness_score": learning_path.projected_readiness_score,
        "created_at": learning_path.created_at,
    }
