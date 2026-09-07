from sqlalchemy import Boolean, Column, Integer, String, Text, JSON, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.db import Base


class JD(Base):
    __tablename__ = "jds"

    id = Column(Integer, primary_key=True, index=True)
    client_name = Column(String, nullable=False)
    raw_text = Column(Text, nullable=False)
    capability_blueprint = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    status = Column(String, default="draft", nullable=False)
    posted_by = Column(Integer, ForeignKey("engineers.id"), nullable=True)
    is_published = Column(Boolean, default=False, nullable=False)
    location = Column(String, nullable=True)
    employment_type = Column(String, nullable=True)

    capabilities = relationship("JDCapability", back_populates="jd", cascade="all, delete-orphan")
    matches = relationship("Match", back_populates="jd", cascade="all, delete-orphan")
    assessments = relationship("Assessment", back_populates="jd", cascade="all, delete-orphan")
    teams = relationship("Team", back_populates="jd", cascade="all, delete-orphan")
    deployments = relationship("Deployment", back_populates="jd", cascade="all, delete-orphan")
    skill_gaps = relationship("SkillGap", back_populates="jd", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="jd", cascade="all, delete-orphan")


class JDCapability(Base):
    __tablename__ = "jd_capabilities"

    id = Column(Integer, primary_key=True, index=True)
    jd_id = Column(Integer, ForeignKey("jds.id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    weight = Column(Float, default=1.0)
    priority = Column(String, default="medium")  # critical | high | medium | nice_to_have

    jd = relationship("JD", back_populates="capabilities")
    skill = relationship("Skill", back_populates="jd_capabilities")


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    jd_id = Column(Integer, ForeignKey("jds.id"), nullable=False)
    engineer_id = Column(Integer, ForeignKey("engineers.id"), nullable=False)
    jd_match_score = Column(Float, default=0.0)
    breakdown = Column(JSON, nullable=True)  # detailed score breakdown
    explanation = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    jd = relationship("JD", back_populates="matches")
    engineer = relationship("Engineer", back_populates="matches")
