from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ApplicationCreate(BaseModel):
    cover_note: Optional[str] = None


class ApplicationOut(BaseModel):
    id: int
    jd_id: int
    engineer_id: int
    resume_id: Optional[int] = None
    status: str
    cover_note: Optional[str] = None
    match_score_snapshot: Optional[float] = None
    applied_at: datetime
    updated_at: datetime
    reviewed_at: Optional[datetime] = None
    admin_notes: Optional[str] = None
    model_config = {"from_attributes": True}


class ApplicationDetail(ApplicationOut):
    client_name: str
    raw_text: str
    capability_blueprint: Optional[Dict[str, Any]] = None
    engineer_name: Optional[str] = None


class ApplicationStatusUpdate(BaseModel):
    status: str
    admin_notes: Optional[str] = None


class OpportunityOut(BaseModel):
    id: int
    client_name: str
    raw_text: str
    capability_blueprint: Optional[Dict[str, Any]] = None
    status: str
    location: Optional[str] = None
    employment_type: Optional[str] = None
    created_at: datetime
    application_status: Optional[str] = None
    match_score: Optional[float] = None
