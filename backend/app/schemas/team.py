from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class TeamComposeRequest(BaseModel):
    jd_id: int
    size: int = 6
    natural_language_request: Optional[str] = None


class TeamMemberOut(BaseModel):
    engineer_id: int
    engineer_name: str
    role: str
    rationale: str
    capability_score: float


class TeamOut(BaseModel):
    id: int
    jd_id: int
    composition: List[TeamMemberOut]
    team_capability_score: float
    engagement_capability_score: float
    risk_level: str
    swap_explanations: List[str] = []


class WhatIfJDRequest(BaseModel):
    jd_id: int
    team_size: int = 6
    upskilling_weeks: int = 8


class WhatIfPortfolioRequest(BaseModel):
    jd_ids: List[int]
    team_size_per_jd: int = 6
    upskilling_weeks: int = 8


class WhatIfResult(BaseModel):
    jd_id: int
    current_coverage_pct: float
    gap_skills: List[Dict[str, Any]]
    projected_coverage_pct: float
    upskilling_recommendation: str
    readiness_date: Optional[str] = None


class LearningPathCreate(BaseModel):
    engineer_id: int
    jd_id: Optional[int] = None


class GapOut(BaseModel):
    skill_id: int
    skill_name: str
    severity: str
    current_score: float
    target_score: float
