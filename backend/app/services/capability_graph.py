"""Graph-style queries over the relational capability data."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.engineer import Engineer, EngineerSkill, Skill, Evidence
from app.models.jd import JD, JDCapability, Match
from app.models.assessment import Assessment, AssessmentScore
from app.models.outcome import Deployment, Outcome


async def get_engineer_with_skills(db: AsyncSession, engineer_id: int):
    result = await db.execute(
        select(Engineer).where(Engineer.id == engineer_id)
    )
    eng = result.scalar_one_or_none()
    if eng is None:
        return None
    # Load skills with evidence
    skills_res = await db.execute(
        select(EngineerSkill).where(EngineerSkill.engineer_id == engineer_id)
    )
    eng._skills_loaded = skills_res.scalars().all()
    return eng


async def get_jd_with_capabilities(db: AsyncSession, jd_id: int):
    result = await db.execute(select(JD).where(JD.id == jd_id))
    return result.scalar_one_or_none()


async def get_all_engineers_skill_map(db: AsyncSession) -> dict:
    """Returns {engineer_id: [{skill_id, name, confidence_score, source}]}."""
    result = await db.execute(
        select(EngineerSkill, Skill)
        .join(Skill, EngineerSkill.skill_id == Skill.id)
    )
    rows = result.all()
    skill_map: dict[int, list] = {}
    for es, sk in rows:
        skill_map.setdefault(es.engineer_id, []).append({
            "skill_id": sk.id,
            "skill_name": sk.name,
            "category": sk.category,
            "claimed_score": es.claimed_score,
            "confidence_score": es.confidence_score,
            "source": es.source,
        })
    return skill_map


async def get_jd_skill_requirements(db: AsyncSession, jd_id: int) -> list:
    result = await db.execute(
        select(JDCapability, Skill)
        .join(Skill, JDCapability.skill_id == Skill.id)
        .where(JDCapability.jd_id == jd_id)
    )
    return [
        {
            "skill_id": sk.id,
            "skill_name": sk.name,
            "weight": jdc.weight,
            "priority": jdc.priority,
        }
        for jdc, sk in result.all()
    ]


async def has_recent_proven_evidence(db: AsyncSession, engineer_id: int, skill_ids: list) -> bool:
    """True if engineer has completed assessments for all critical skills in the last 90 days."""
    from datetime import datetime, timedelta, timezone
    cutoff = datetime.now(timezone.utc) - timedelta(days=90)
    result = await db.execute(
        select(Assessment)
        .where(
            Assessment.engineer_id == engineer_id,
            Assessment.status == "completed",
            Assessment.completed_at >= cutoff,
        )
    )
    assessments = result.scalars().all()
    if not assessments:
        return False
    scored_skills = set()
    for a in assessments:
        scores_res = await db.execute(
            select(AssessmentScore).where(
                AssessmentScore.assessment_id == a.id,
                AssessmentScore.score >= 6.0,
            )
        )
        for s in scores_res.scalars().all():
            scored_skills.add(s.skill_id)
    return all(sid in scored_skills for sid in skill_ids)


async def get_capability_coverage(db: AsyncSession) -> list:
    result = await db.execute(
        select(
            Skill.name,
            Skill.category,
            func.count(EngineerSkill.engineer_id).label("engineer_count"),
            func.avg(EngineerSkill.confidence_score).label("avg_confidence"),
        )
        .join(EngineerSkill, Skill.id == EngineerSkill.skill_id)
        .group_by(Skill.id)
    )
    return result.all()
