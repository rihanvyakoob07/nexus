"""OutcomeRecalibration — compares predicted vs actual and logs discrepancies."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.outcome import Deployment, Outcome, AgentCall
from app.models.jd import Match
from datetime import datetime, timezone


async def run(deployment_id: int, db: AsyncSession) -> dict:
    dep_res = await db.execute(select(Deployment).where(Deployment.id == deployment_id))
    deployment = dep_res.scalar_one_or_none()
    if not deployment or not deployment.outcome:
        return {"status": "no_outcome"}

    outcome = deployment.outcome
    predicted = deployment.predicted_readiness_score or 0.0
    actual = outcome.client_feedback_score or 0.0
    discrepancy = abs(predicted - actual)
    direction = "over_predicted" if predicted > actual else "under_predicted"

    report = {
        "deployment_id": deployment_id,
        "engineer_id": deployment.engineer_id,
        "jd_id": deployment.jd_id,
        "predicted_readiness": predicted,
        "actual_client_feedback": actual,
        "discrepancy": round(discrepancy, 2),
        "direction": direction,
        "delivery_success": outcome.delivery_success,
        "issues": outcome.issues_reported,
        "recommendation": (
            "Increase weighting of production experience in confidence scoring"
            if direction == "over_predicted" and discrepancy > 2
            else "Scoring is well calibrated" if discrepancy < 1
            else "Monitor for pattern before adjusting weights"
        ),
        "logged_at": datetime.now(timezone.utc).isoformat(),
    }
    return report
