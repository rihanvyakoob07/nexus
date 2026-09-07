from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.db import Base


class SkillGap(Base):
    __tablename__ = "skill_gaps"

    id = Column(Integer, primary_key=True, index=True)
    engineer_id = Column(Integer, ForeignKey("engineers.id"), nullable=True)
    jd_id = Column(Integer, ForeignKey("jds.id"), nullable=True)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    severity = Column(String, default="medium")  # critical | high | medium | low
    current_score = Column(Float, default=0.0)
    target_score = Column(Float, default=8.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    engineer = relationship("Engineer", back_populates="skill_gaps")
    jd = relationship("JD", back_populates="skill_gaps")
    skill = relationship("Skill", back_populates="skill_gaps")


class LearningPath(Base):
    __tablename__ = "learning_paths"

    id = Column(Integer, primary_key=True, index=True)
    engineer_id = Column(Integer, ForeignKey("engineers.id"), nullable=False)
    plan = Column(JSON, nullable=True)  # week-by-week plan JSON
    status = Column(String, default="active")  # active | completed | paused
    projected_readiness_date = Column(DateTime, nullable=True)
    projected_readiness_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    engineer = relationship("Engineer", back_populates="learning_paths")


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    jd_id = Column(Integer, ForeignKey("jds.id"), nullable=False)
    composition = Column(JSON, nullable=True)  # list of {engineer_id, role, rationale}
    team_capability_score = Column(Float, nullable=True)
    risk_level = Column(String, default="medium")  # low | medium | high
    engagement_capability_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    jd = relationship("JD", back_populates="teams")
    deployments = relationship("Deployment", back_populates="team")
