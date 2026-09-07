from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.db import Base


class Deployment(Base):
    __tablename__ = "deployments"

    id = Column(Integer, primary_key=True, index=True)
    engineer_id = Column(Integer, ForeignKey("engineers.id"), nullable=False)
    jd_id = Column(Integer, ForeignKey("jds.id"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    predicted_readiness_score = Column(Float, nullable=True)

    engineer = relationship("Engineer", back_populates="deployments")
    jd = relationship("JD", back_populates="deployments")
    team = relationship("Team", back_populates="deployments")
    outcome = relationship("Outcome", back_populates="deployment", uselist=False)


class Outcome(Base):
    __tablename__ = "outcomes"

    id = Column(Integer, primary_key=True, index=True)
    deployment_id = Column(Integer, ForeignKey("deployments.id"), nullable=False, unique=True)
    client_feedback_score = Column(Float, nullable=True)  # 0-10
    delivery_success = Column(Boolean, default=True)
    issues_reported = Column(JSON, default=list)
    recorded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    deployment = relationship("Deployment", back_populates="outcome")


class AgentCall(Base):
    __tablename__ = "agent_calls"

    id = Column(Integer, primary_key=True, index=True)
    agent_name = Column(String, nullable=False)
    model_used = Column(String, nullable=False)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    latency_ms = Column(Float, default=0.0)
    cost_estimate = Column(Float, default=0.0)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    context_ref = Column(String, nullable=True)  # e.g. "jd_id=5"
