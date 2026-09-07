from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.db import get_db
from app.core.security import require_role, get_current_user
from app.models.engineer import Engineer, EngineerSkill, Skill
from app.models.jd import JD, Match
from app.models.assessment import Assessment
from app.models.gap_learning import SkillGap, Team, LearningPath
from app.models.outcome import AgentCall, Deployment
from app.schemas.dashboard import (
    LeadershipDashboard, AdminDashboard, EngineerDashboard,
    ObservabilityDashboard, ObservabilityRow, CapabilityCoverageItem, GapAlert, DemandRadarItem
)
from app.services.capability_graph import get_capability_coverage

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/leadership", response_model=LeadershipDashboard)
async def leadership_dashboard(db: AsyncSession = Depends(get_db), _=Depends(require_role("leadership", "admin"))):
    coverage_rows = await get_capability_coverage(db)
    total_eng = (await db.execute(select(func.count(Engineer.id)))).scalar() or 0
    total_jds = (await db.execute(select(func.count(JD.id)))).scalar() or 0

    from datetime import datetime, timedelta, timezone
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    dep_count = (await db.execute(select(func.count(Deployment.id)).where(Deployment.start_date >= cutoff))).scalar() or 0
    velocity = round(dep_count, 2)

    cost_res = await db.execute(select(func.sum(AgentCall.cost_estimate)).where(AgentCall.timestamp >= cutoff))
    total_cost = cost_res.scalar() or 0.0

    coverage = [
        CapabilityCoverageItem(
            skill_name=r.name,
            category=r.category or "General",
            coverage_pct=min(100.0, r.engineer_count / max(total_eng, 1) * 100),
            avg_confidence=round(r.avg_confidence or 0, 2),
            engineer_count=r.engineer_count,
        )
        for r in coverage_rows
    ]

    gap_res = await db.execute(
        select(Skill.name, SkillGap.severity, func.count(SkillGap.id).label("cnt"))
        .join(Skill, SkillGap.skill_id == Skill.id)
        .group_by(Skill.id, SkillGap.severity)
        .order_by(func.count(SkillGap.id).desc())
        .limit(10)
    )
    gap_alerts = [GapAlert(skill_name=r.name, severity=r.severity, affected_jds=0, engineer_gap_count=r.cnt) for r in gap_res.all()]

    # Current demand, not a forecast: published JD capability requirements.
    from app.models.jd import JDCapability
    demand_res = await db.execute(
        select(Skill.name, func.count(JDCapability.id).label("cnt"), func.avg(JDCapability.weight).label("avg_w"))
        .join(Skill, JDCapability.skill_id == Skill.id)
        .join(JD, JDCapability.jd_id == JD.id)
        .where(JD.is_published.is_(True))
        .group_by(Skill.id)
        .order_by(func.count(JDCapability.id).desc())
        .limit(15)
    )
    demand = [DemandRadarItem(skill_name=r.name, demand_count=r.cnt, avg_priority_weight=round(r.avg_w or 0, 2)) for r in demand_res.all()]

    return LeadershipDashboard(
        capability_coverage=coverage,
        gap_alerts=gap_alerts,
        demand_radar=demand,
        total_engineers=total_eng,
        total_jds=total_jds,
        deployment_velocity=velocity,
        agent_cost_last_30d=round(total_cost, 4),
    )


@router.get("/admin", response_model=AdminDashboard)
async def admin_dashboard(db: AsyncSession = Depends(get_db), _=Depends(require_role("admin", "leadership"))):
    open_jds = (await db.execute(select(func.count(JD.id)))).scalar() or 0
    pending_assessments = (await db.execute(select(func.count(Assessment.id)).where(Assessment.status == "in_progress"))).scalar() or 0
    teams_composed = (await db.execute(select(func.count(Team.id)))).scalar() or 0

    recent_matches_res = await db.execute(
        select(Match, Engineer, JD)
        .join(Engineer, Match.engineer_id == Engineer.id)
        .join(JD, Match.jd_id == JD.id)
        .order_by(Match.created_at.desc())
        .limit(10)
    )
    recent = [{"engineer": eng.name, "jd": jd.client_name, "score": m.jd_match_score} for m, eng, jd in recent_matches_res.all()]
    return AdminDashboard(open_jds=open_jds, recent_matches=recent, pending_assessments=pending_assessments, teams_composed=teams_composed)


@router.get("/engineer", response_model=EngineerDashboard)
async def engineer_dashboard(db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    skills_res = await db.execute(
        select(func.avg(EngineerSkill.confidence_score)).where(EngineerSkill.engineer_id == current_user.id)
    )
    evidence_confidence = round(float(skills_res.scalar() or 0.0), 2)

    latest_assessment = (await db.execute(
        select(Assessment)
        .where(Assessment.engineer_id == current_user.id, Assessment.status == "completed")
        .order_by(Assessment.completed_at.desc())
        .limit(1)
    )).scalar_one_or_none()
    assessment_score = round(float(latest_assessment.readiness_score if latest_assessment and latest_assessment.readiness_score is not None else 0.0), 2) or None

    # Readiness is a transparent composite, not an unexplained capability claim.
    # If no assessment exists, do not invent one: readiness equals evidence confidence.
    readiness_score = evidence_confidence if assessment_score is None else round(evidence_confidence * 0.7 + assessment_score * 0.3, 2)

    gaps_count = (await db.execute(select(func.count(SkillGap.id)).where(SkillGap.engineer_id == current_user.id))).scalar() or 0
    critical_gaps = (await db.execute(
        select(func.count(SkillGap.id)).where(SkillGap.engineer_id == current_user.id, SkillGap.severity.in_(["critical", "high"]))
    )).scalar() or 0

    matches_res = await db.execute(
        select(Match, JD)
        .join(JD, Match.jd_id == JD.id)
        .where(Match.engineer_id == current_user.id)
        .order_by(Match.jd_match_score.desc())
        .limit(5)
    )
    opportunities = [{"jd_id": jd.id, "client": jd.client_name, "match_score": m.jd_match_score, "explanation": m.explanation} for m, jd in matches_res.all()]

    lp_res = await db.execute(select(LearningPath).where(LearningPath.engineer_id == current_user.id).order_by(LearningPath.created_at.desc()).limit(1))
    lp = lp_res.scalar_one_or_none()

    return EngineerDashboard(
        engineer_id=current_user.id,
        readiness_score=readiness_score,
        evidence_confidence=evidence_confidence,
        assessment_score=assessment_score,
        critical_gaps=critical_gaps,
        overall_capability_score=evidence_confidence,
        matched_opportunities=opportunities,
        active_gaps=gaps_count,
        learning_path_status=lp.status if lp else None,
        projected_readiness_date=lp.projected_readiness_date.isoformat() if lp and lp.projected_readiness_date else None,
    )


@router.get("/observability", response_model=ObservabilityDashboard)
async def observability(db: AsyncSession = Depends(get_db), _=Depends(require_role("leadership", "admin"))):
    res = await db.execute(select(AgentCall).order_by(AgentCall.timestamp.desc()).limit(200))
    rows = res.scalars().all()
    total_cost = sum(r.cost_estimate for r in rows)
    avg_latency = sum(r.latency_ms for r in rows) / max(len(rows), 1)
    return ObservabilityDashboard(
        rows=[ObservabilityRow(agent_name=r.agent_name, model_used=r.model_used, input_tokens=r.input_tokens, output_tokens=r.output_tokens, latency_ms=round(r.latency_ms, 1), cost_estimate=round(r.cost_estimate, 6), timestamp=r.timestamp.isoformat()) for r in rows],
        total_cost=round(total_cost, 4), total_calls=len(rows), avg_latency_ms=round(avg_latency, 1),
    )


@router.get("/capabilities")
async def capabilities(db: AsyncSession = Depends(get_db), _=Depends(require_role("leadership", "admin"))):
    rows = await get_capability_coverage(db)
    return [{"skill_name": row.name, "category": row.category or "General", "engineer_count": row.engineer_count, "avg_confidence": round(row.avg_confidence or 0, 2)} for row in rows]


@router.get("/demand")
async def demand(db: AsyncSession = Depends(get_db), _=Depends(require_role("leadership", "admin"))):
    dashboard = await leadership_dashboard(db, _)
    jds = (await db.execute(select(JD).where(JD.is_published.is_(True)).order_by(JD.created_at.desc()))).scalars().all()
    return {"demand_radar": dashboard.demand_radar, "opportunities": [{"id": jd.id, "client_name": jd.client_name, "status": jd.status, "capability_blueprint": jd.capability_blueprint} for jd in jds]}


@router.get("/analytics")
async def analytics(db: AsyncSession = Depends(get_db), _=Depends(require_role("leadership", "admin"))):
    total_assessments = (await db.execute(select(func.count(Assessment.id)))).scalar() or 0
    completed_assessments = (await db.execute(select(func.count(Assessment.id)).where(Assessment.status == "completed"))).scalar() or 0
    avg_readiness = (await db.execute(select(func.avg(Assessment.readiness_score)).where(Assessment.readiness_score.is_not(None)))).scalar() or 0
    deployments = (await db.execute(select(func.count(Deployment.id)))).scalar() or 0
    return {"assessment_count": total_assessments, "completed_assessments": completed_assessments, "assessment_completion_rate": round(completed_assessments / max(total_assessments, 1) * 100, 1), "average_readiness": round(avg_readiness, 2), "deployment_count": deployments}


@router.get("/admin/assessments")
async def admin_assessments(db: AsyncSession = Depends(get_db), _=Depends(require_role("admin", "leadership"))):
    rows = (await db.execute(select(Assessment, Engineer, JD).join(Engineer, Assessment.engineer_id == Engineer.id).join(JD, Assessment.jd_id == JD.id).order_by(Assessment.started_at.desc()))).all()
    return [{"id": assessment.id, "engineer_id": assessment.engineer_id, "engineer_name": engineer.name, "jd_id": assessment.jd_id, "client_name": jd.client_name, "application_id": assessment.application_id, "status": assessment.status, "started_at": assessment.started_at, "completed_at": assessment.completed_at, "overall_score": assessment.overall_score, "readiness_score": assessment.readiness_score, "summary": assessment.summary} for assessment, engineer, jd in rows]


@router.get("/admin/teams")
async def admin_teams(db: AsyncSession = Depends(get_db), _=Depends(require_role("admin", "leadership"))):
    rows = (await db.execute(select(Team, JD).join(JD, Team.jd_id == JD.id).order_by(Team.created_at.desc()))).all()
    return [{"id": team.id, "jd_id": team.jd_id, "client_name": jd.client_name, "composition": team.composition or [], "team_capability_score": team.team_capability_score, "engagement_capability_score": team.engagement_capability_score, "risk_level": team.risk_level, "created_at": team.created_at} for team, jd in rows]
