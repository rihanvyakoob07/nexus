from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.db import Base


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True)
    engineer_id = Column(Integer, ForeignKey("engineers.id"), nullable=False)
    jd_id = Column(Integer, ForeignKey("jds.id"), nullable=False)
    status = Column(String, default="pending")  # pending | in_progress | completed
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=True)
    overall_score = Column(Float, nullable=True)
    readiness_score = Column(Float, nullable=True)
    summary = Column(Text, nullable=True)

    engineer = relationship("Engineer", back_populates="assessments")
    jd = relationship("JD", back_populates="assessments")
    turns = relationship("AssessmentTurn", back_populates="assessment", cascade="all, delete-orphan", order_by="AssessmentTurn.turn_index")
    scores = relationship("AssessmentScore", back_populates="assessment", cascade="all, delete-orphan")
    application = relationship("Application", back_populates="assessments")


class AssessmentTurn(Base):
    __tablename__ = "assessment_turns"

    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=False)
    turn_index = Column(Integer, nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=True)
    ai_evaluation = Column(JSON, nullable=True)

    assessment = relationship("Assessment", back_populates="turns")


class AssessmentScore(Base):
    __tablename__ = "assessment_scores"

    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    score = Column(Float, default=0.0)
    confidence = Column(Float, default=0.0)

    assessment = relationship("Assessment", back_populates="scores")
    skill = relationship("Skill", back_populates="assessment_scores")
