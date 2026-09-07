from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class AssessmentCreate(BaseModel):
    jd_id: int
    engineer_id: Optional[int] = None
    application_id: Optional[int] = None


class AssessmentTurnIn(BaseModel):
    answer: str


class AssessmentTurnOut(BaseModel):
    turn_index: int
    question: str
    answer: Optional[str] = None
    ai_evaluation: Optional[Dict[str, Any]] = None
    model_config = {"from_attributes": True}


class AssessmentScoreOut(BaseModel):
    skill_id: int
    skill_name: str
    score: float
    confidence: float
    model_config = {"from_attributes": True}


class AssessmentOut(BaseModel):
    id: int
    engineer_id: int
    jd_id: int
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    turns: List[AssessmentTurnOut] = []
    model_config = {"from_attributes": True}


class AssessmentResult(BaseModel):
    assessment_id: int
    status: str
    scores: List[AssessmentScoreOut]
    overall_score: float
    readiness_level: str  # not_ready | developing | ready | highly_ready
    summary: str


class NextQuestion(BaseModel):
    assessment_id: int
    turn_index: int
    question: str
    is_final: bool = False
