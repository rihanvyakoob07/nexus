from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
from app.core.db import get_db
from app.core.security import require_role, get_current_user
from app.models.outcome import Deployment, Outcome
from app.agents.orchestrator import orchestrator
from app.schemas.deployment import DeploymentCreate, DeploymentOut, OutcomeCreate

router = APIRouter(prefix="/deployments", tags=["deployments"])


@router.get("/", response_model=List[DeploymentOut])
async def list_deployments(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role("admin", "leadership")),
):
    result = await db.execute(
        select(Deployment)
        .options(selectinload(Deployment.outcome))
        .order_by(Deployment.start_date.desc(), Deployment.id.desc())
    )
    deployments = result.scalars().all()
    return [
        {
            **deployment.__dict__,
            "outcome": (
                {
                    "id": deployment.outcome.id,
                    "deployment_id": deployment.outcome.deployment_id,
                    "client_feedback_score": deployment.outcome.client_feedback_score,
                    "delivery_success": deployment.outcome.delivery_success,
                    "issues_reported": deployment.outcome.issues_reported or [],
                    "recorded_at": deployment.outcome.recorded_at,
                }
                if deployment.outcome
                else None
            ),
        }
        for deployment in deployments
    ]


@router.get("/{deployment_id}", response_model=DeploymentOut)
async def get_deployment(
    deployment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(
        select(Deployment)
        .options(selectinload(Deployment.outcome))
        .where(Deployment.id == deployment_id)
    )
    deployment = result.scalar_one_or_none()
    if not deployment:
        raise HTTPException(404, "Deployment not found")
    if current_user.role == "engineer" and deployment.engineer_id != current_user.id:
        raise HTTPException(403, "Insufficient permissions")
    return {
        **deployment.__dict__,
        "outcome": deployment.outcome.__dict__ if deployment.outcome else None,
    }


@router.post("/", status_code=201)
async def create_deployment(payload: DeploymentCreate, db: AsyncSession = Depends(get_db), _=Depends(require_role("admin", "leadership"))):
    dep = Deployment(**payload.model_dump())
    db.add(dep)
    await db.flush()
    return {"deployment_id": dep.id}


@router.post("/{deployment_id}/outcome")
async def record_outcome(deployment_id: int, payload: OutcomeCreate, db: AsyncSession = Depends(get_db), _=Depends(require_role("admin", "leadership"))):
    dep_res = await db.execute(select(Deployment).where(Deployment.id == deployment_id))
    dep = dep_res.scalar_one_or_none()
    if not dep:
        raise HTTPException(404, "Deployment not found")

    outcome = Outcome(
        deployment_id=deployment_id,
        client_feedback_score=payload.client_feedback_score,
        delivery_success=payload.delivery_success,
        issues_reported=payload.issues_reported,
    )
    db.add(outcome)
    await db.flush()

    recalibration = await orchestrator.recalibrate_from_outcome(deployment_id, db)
    return {"outcome_id": outcome.id, "recalibration_report": recalibration}
