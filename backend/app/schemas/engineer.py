from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


class SkillOut(BaseModel):
    id: int
    name: str
    category: Optional[str] = None
    model_config = {"from_attributes": True}


class EngineerSkillOut(BaseModel):
    skill_id: int
    skill: SkillOut
    claimed_score: float
    confidence_score: float
    source: str
    last_updated: datetime
    model_config = {"from_attributes": True}


class EvidenceOut(BaseModel):
    id: int
    skill_id: int
    type: str
    description: Optional[str] = None
    date: Optional[datetime] = None
    model_config = {"from_attributes": True}


class CertificationOut(BaseModel):
    id: int
    name: str
    issuer: Optional[str] = None
    date: Optional[datetime] = None
    expiry: Optional[datetime] = None
    model_config = {"from_attributes": True}


class EngineerOut(BaseModel):
    id: int
    name: str
    email: str
    role: str
    seniority: Optional[str] = None
    bio: Optional[str] = None
    created_at: datetime
    model_config = {"from_attributes": True}


class EngineerPassport(EngineerOut):
    skills: List[EngineerSkillOut] = []
    evidence: List[EvidenceOut] = []
    certifications: List[CertificationOut] = []


class EngineerCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    seniority: Optional[str] = None
    bio: Optional[str] = None


class EngineerUpdate(BaseModel):
    name: Optional[str] = None
    seniority: Optional[str] = None
    bio: Optional[str] = None


class EngineerProfileUpdate(BaseModel):
    name: Optional[str] = None
    seniority: Optional[str] = None
    bio: Optional[str] = None
