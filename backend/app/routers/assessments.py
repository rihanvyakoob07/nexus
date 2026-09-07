from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone
from app.core.db import get_db
from app.core.security import get_current_user, require_role
from app.models.assessment import Assessment, AssessmentTurn, AssessmentScore
from app.models.engineer import Engineer, EngineerSkill, Skill
from app.models.jd import JD
from app.models.application import Application
from app.schemas.assessment import AssessmentCreate, AssessmentOut, AssessmentTurnIn, AssessmentResult, NextQuestion, AssessmentScoreOut
from app.agents import arena_agent
from app.services.capability_graph import has_recent_proven_evidence

router = APIRouter(prefix="/assessments", tags=["assessments"])

MAX_TURNS = 5


@router.get("/{assessment_id}", response_model=AssessmentOut)
async def get_assessment(assessment_id: int, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    result = await db.execute(
        select(Assessment)
        .options(selectinload(Assessment.turns))
        .where(Assessment.id == assessment_id)
    )
    assessment = result.scalar_one_or_none()
    if not assessment:
        raise HTTPException(404, "Assessment not found")
    return assessment


@router.post("/", response_model=AssessmentOut, status_code=201)
async def start_assessment(payload: AssessmentCreate, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    engineer_id = current_user.id if current_user.role == "engineer" else payload.engineer_id
    if not engineer_id:
        raise HTTPException(422, "engineer_id is required for admin assessment requests")
    application = None
    if payload.application_id:
        application = (await db.execute(select(Application).where(Application.id == payload.application_id))).scalar_one_or_none()
        if not application or application.jd_id != payload.jd_id or application.engineer_id != engineer_id:
            raise HTTPException(422, "Application does not match the engineer and JD")
    # Check if engineer has recent proof
    jd_res = await db.execute(select(JD).where(JD.id == payload.jd_id))
    jd = jd_res.scalar_one_or_none()
    if not jd:
        raise HTTPException(404, "JD not found")

    assessment = Assessment(
        engineer_id=engineer_id,
        jd_id=payload.jd_id,
        application_id=payload.application_id,
        status="pending" if current_user.role != "engineer" else "in_progress",
        started_at=datetime.now(timezone.utc) if current_user.role == "engineer" else None,
    )
    db.add(assessment)
    await db.flush()

    if current_user.role != "engineer":
        await db.flush()
        return assessment

    # Generate first question for an engineer starting their own assessment.
    from app.services.capability_graph import get_all_engineers_skill_map
    skill_map = await get_all_engineers_skill_map(db)
    eng_res = await db.execute(select(Engineer).where(Engineer.id == payload.engineer_id))
    eng = eng_res.scalar_one_or_none()
    profile = {"id": eng.id, "name": eng.name, "seniority": eng.seniority, "skills": skill_map.get(eng.id, [])}

    blueprint = jd.capability_blueprint or {}
    q_result = await arena_agent.generate_first_question(blueprint, profile, db)

    turn = AssessmentTurn(
        assessment_id=assessment.id,
        turn_index=0,
        question=q_result.get("question", ""),
    )
    db.add(turn)
    await db.flush()
    return assessment


@router.post("/{assessment_id}/start", response_model=AssessmentOut)
async def begin_pending_assessment(assessment_id: int, db: AsyncSession = Depends(get_db), current_user=Depends(require_role("engineer"))):
    assessment = (await db.execute(select(Assessment).where(Assessment.id == assessment_id))).scalar_one_or_none()
    if not assessment:
        raise HTTPException(404, "Assessment not found")
    if assessment.engineer_id != current_user.id:
        raise HTTPException(403, "Assessment belongs to another engineer")
    if assessment.status != "pending":
        return assessment
    jd = (await db.execute(select(JD).where(JD.id == assessment.jd_id))).scalar_one_or_none()
    from app.services.capability_graph import get_all_engineers_skill_map
    skill_map = await get_all_engineers_skill_map(db)
    eng = (await db.execute(select(Engineer).where(Engineer.id == current_user.id))).scalar_one()
    q_result = await arena_agent.generate_first_question(jd.capability_blueprint or {}, {"id": eng.id, "name": eng.name, "seniority": eng.seniority, "skills": skill_map.get(eng.id, [])}, db)
    assessment.status = "in_progress"
    assessment.started_at = datetime.now(timezone.utc)
    db.add(AssessmentTurn(assessment_id=assessment.id, turn_index=0, question=q_result.get("question", "")))
    await db.flush()
    refreshed = await db.execute(
        select(Assessment)
        .options(selectinload(Assessment.turns))
        .where(Assessment.id == assessment.id)
    )
    return refreshed.scalar_one()


@router.post("/{assessment_id}/turn", response_model=NextQuestion)
async def submit_turn(assessment_id: int, payload: AssessmentTurnIn, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    a_res = await db.execute(select(Assessment).where(Assessment.id == assessment_id))
    assessment = a_res.scalar_one_or_none()
    if not assessment:
        raise HTTPException(404, "Assessment not found")
    current_user = _
    if current_user.role == "engineer" and assessment.engineer_id != current_user.id:
        raise HTTPException(403, "Assessment belongs to another engineer")
    if assessment.status != "in_progress":
        raise HTTPException(400, "Assessment not in progress")

    turns_res = await db.execute(
        select(AssessmentTurn)
        .where(AssessmentTurn.assessment_id == assessment_id)
        .order_by(AssessmentTurn.turn_index)
    )
    turns = turns_res.scalars().all()
    current_turn = turns[-1]

    # Save answer
    current_turn.answer = payload.answer

    jd_res = await db.execute(select(JD).where(JD.id == assessment.jd_id))
    jd = jd_res.scalar_one_or_none()
    blueprint = jd.capability_blueprint if jd else {}

    # Evaluate answer
    evaluation = await arena_agent.evaluate_answer(current_turn.question, payload.answer, blueprint, db)
    current_turn.ai_evaluation = evaluation
    await db.flush()

    turn_count = len(turns)
    is_final = turn_count >= MAX_TURNS

    if is_final:
        # Finalize assessment
        all_turns = [{"question": t.question, "answer": t.answer, "evaluation": t.ai_evaluation} for t in turns]
        final = await arena_agent.finalize_assessment(all_turns, blueprint, db)

        for skill_name, score in final.get("skill_scores", {}).items():
            sk_res = await db.execute(select(Skill).where(Skill.name == skill_name))
            sk = sk_res.scalar_one_or_none()
            if sk:
                as_score = AssessmentScore(assessment_id=assessment_id, skill_id=sk.id, score=score, confidence=0.8)
                db.add(as_score)

                # Update engineer skill record
                es_res = await db.execute(
                    select(EngineerSkill).where(
                        EngineerSkill.engineer_id == assessment.engineer_id,
                        EngineerSkill.skill_id == sk.id,
                    )
                )
                es = es_res.scalar_one_or_none()
                if es:
                    es.source = "demonstrated" if score >= 6 else es.source
                    es.claimed_score = max(es.claimed_score, score)

        assessment.status = "completed"
        assessment.completed_at = datetime.now(timezone.utc)
        assessment.overall_score = final.get("overall_score")
        assessment.readiness_score = final.get("overall_score")
        assessment.summary = final.get("summary")
        if assessment.application_id:
            application = (await db.execute(select(Application).where(Application.id == assessment.application_id))).scalar_one_or_none()
            if application:
                application.status = "assessment_completed"
        await db.flush()

        return NextQuestion(assessment_id=assessment_id, turn_index=turn_count, question="Assessment complete. See /result for your scores.", is_final=True)

    # Generate follow-up
    history = [{"q": t.question, "a": t.answer} for t in turns]
    followup = await arena_agent.generate_followup(evaluation, history, blueprint, db)
    next_turn = AssessmentTurn(
        assessment_id=assessment_id,
        turn_index=turn_count,
        question=followup.get("question", ""),
    )
    db.add(next_turn)
    await db.flush()

    return NextQuestion(assessment_id=assessment_id, turn_index=turn_count, question=next_turn.question, is_final=False)


@router.get("/{assessment_id}/result", response_model=AssessmentResult)
async def get_result(assessment_id: int, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    a_res = await db.execute(select(Assessment).where(Assessment.id == assessment_id))
    assessment = a_res.scalar_one_or_none()
    if not assessment:
        raise HTTPException(404, "Assessment not found")
    if _.role == "engineer" and assessment.engineer_id != _.id:
        raise HTTPException(403, "Assessment belongs to another engineer")

    scores_res = await db.execute(
        select(AssessmentScore, Skill).join(Skill).where(AssessmentScore.assessment_id == assessment_id)
    )
    scores = scores_res.all()
    scores_out = [AssessmentScoreOut(skill_id=sk.id, skill_name=sk.name, score=s.score, confidence=s.confidence) for s, sk in scores]
    overall = sum(s.score for s, _ in scores) / max(len(scores), 1)
    level = "highly_ready" if overall >= 8 else "ready" if overall >= 6 else "developing" if overall >= 4 else "not_ready"

    return AssessmentResult(
        assessment_id=assessment_id,
        status=assessment.status,
        scores=scores_out,
        overall_score=round(overall, 2),
        readiness_level=level,
        summary=f"Assessment {assessment.status}. Overall score: {overall:.1f}/10.",
    )
