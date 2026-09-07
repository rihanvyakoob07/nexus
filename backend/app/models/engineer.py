from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.db import Base


class Engineer(Base):
    __tablename__ = "engineers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="engineer")  # leadership | admin | engineer
    seniority = Column(String, nullable=True)  # junior | mid | senior | principal
    bio = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    skills = relationship("EngineerSkill", back_populates="engineer", cascade="all, delete-orphan")
    evidence = relationship("Evidence", back_populates="engineer", cascade="all, delete-orphan")
    certifications = relationship("Certification", back_populates="engineer", cascade="all, delete-orphan")
    assessments = relationship("Assessment", back_populates="engineer", cascade="all, delete-orphan")
    matches = relationship("Match", back_populates="engineer", cascade="all, delete-orphan")
    skill_gaps = relationship("SkillGap", back_populates="engineer", cascade="all, delete-orphan")
    learning_paths = relationship("LearningPath", back_populates="engineer", cascade="all, delete-orphan")
    deployments = relationship("Deployment", back_populates="engineer", cascade="all, delete-orphan")
    resumes = relationship("Resume", back_populates="engineer", cascade="all, delete-orphan")
    applications = relationship("Application", foreign_keys="Application.engineer_id", back_populates="engineer", cascade="all, delete-orphan")


class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    category = Column(String, nullable=True)  # e.g. RAG, Agentic AI, MLOps

    engineer_skills = relationship("EngineerSkill", back_populates="skill")
    jd_capabilities = relationship("JDCapability", back_populates="skill")
    evidence = relationship("Evidence", back_populates="skill")
    assessment_scores = relationship("AssessmentScore", back_populates="skill")
    skill_gaps = relationship("SkillGap", back_populates="skill")


class EngineerSkill(Base):
    __tablename__ = "engineer_skills"

    id = Column(Integer, primary_key=True, index=True)
    engineer_id = Column(Integer, ForeignKey("engineers.id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    claimed_score = Column(Float, default=0.0)  # 0-10
    confidence_score = Column(Float, default=0.0)  # computed, cached
    source = Column(String, default="claimed")  # claimed | demonstrated | proven
    last_updated = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    engineer = relationship("Engineer", back_populates="skills")
    skill = relationship("Skill", back_populates="engineer_skills")


class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True)
    engineer_id = Column(Integer, ForeignKey("engineers.id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    type = Column(String, nullable=False)  # project | certification | assessment | client_delivery
    description = Column(Text, nullable=True)
    ref_id = Column(Integer, nullable=True)  # FK to project/cert/assessment id
    date = Column(DateTime, nullable=True)

    engineer = relationship("Engineer", back_populates="evidence")
    skill = relationship("Skill", back_populates="evidence")
