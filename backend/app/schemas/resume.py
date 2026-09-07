from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ResumeSkill(BaseModel):
    name: str
    score: float = Field(ge=0, le=10)
    confidence: float = Field(ge=0, le=1)
    evidence: str = "Resume claim"


class ParsedResume(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    summary: Optional[str] = None
    seniority: Optional[str] = None
    years_experience: Optional[float] = None
    skills: List[ResumeSkill] = []
    projects: List[Dict[str, Any]] = []
    certifications: List[Dict[str, Any]] = []
    technologies: List[str] = []
    client_experience: List[Dict[str, Any]] = []
    education: List[Dict[str, Any]] = []


class ResumeOut(BaseModel):
    id: int
    engineer_id: int
    filename: str
    parsed_data: Optional[Dict[str, Any]] = None
    ats_score: Optional[float] = None
    ats_breakdown: Optional[Dict[str, Any]] = None
    status: str
    is_active: bool
    uploaded_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class ATSResult(BaseModel):
    resume_id: int
    ats_score: float
    breakdown: Dict[str, float]
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]
