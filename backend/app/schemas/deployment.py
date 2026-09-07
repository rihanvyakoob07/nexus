from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class DeploymentOut(BaseModel):
    id: int
    engineer_id: int
    jd_id: int
    team_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    predicted_readiness_score: Optional[float] = None
    outcome: Optional[dict] = None

    model_config = {"from_attributes": True}


class DeploymentCreate(BaseModel):
    engineer_id: int
    jd_id: int
    team_id: Optional[int] = None
    start_date: Optional[datetime] = None
    predicted_readiness_score: Optional[float] = None


class OutcomeCreate(BaseModel):
    client_feedback_score: float
    delivery_success: bool = True
    issues_reported: List[str] = []


class LearningPathOut(BaseModel):
    learning_path_id: int
    plan: dict
    status: str
    projected_readiness_date: Optional[datetime] = None
    projected_readiness_score: Optional[float] = None
    created_at: datetime
