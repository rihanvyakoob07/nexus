from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class JDCreate(BaseModel):
    client_name: str
    raw_text: str
    location: Optional[str] = None
    employment_type: Optional[str] = None


class JDCapabilityOut(BaseModel):
    skill_id: int
    skill_name: str
    weight: float
    priority: str
    model_config = {"from_attributes": True}


class JDOut(BaseModel):
    id: int
    client_name: str
    raw_text: str
    capability_blueprint: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    status: str = "draft"
    posted_by: Optional[int] = None
    is_published: bool = False
    location: Optional[str] = None
    employment_type: Optional[str] = None
    model_config = {"from_attributes": True}


class MatchOut(BaseModel):
    engineer_id: int
    engineer_name: str
    jd_match_score: float
    breakdown: Optional[Dict[str, Any]] = None
    explanation: Optional[str] = None
    model_config = {"from_attributes": True}


class JDMatchesOut(BaseModel):
    jd_id: int
    client_name: str
    candidates: List[MatchOut]
