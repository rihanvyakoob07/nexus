from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.db import Base


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    jd_id = Column(Integer, ForeignKey("jds.id"), nullable=False, index=True)
    engineer_id = Column(Integer, ForeignKey("engineers.id"), nullable=False, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=True)
    status = Column(String, default="applied", nullable=False)
    cover_note = Column(Text, nullable=True)
    match_score_snapshot = Column(Float, nullable=True)
    applied_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(Integer, ForeignKey("engineers.id"), nullable=True)
    admin_notes = Column(Text, nullable=True)

    jd = relationship("JD", back_populates="applications")
    engineer = relationship("Engineer", foreign_keys=[engineer_id], back_populates="applications")
    resume = relationship("Resume")
    reviewer = relationship("Engineer", foreign_keys=[reviewed_by])
    assessments = relationship("Assessment", back_populates="application")