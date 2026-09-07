from sqlalchemy import Column, Integer, String, Text, JSON, DateTime
from datetime import datetime, timezone
from app.core.db import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    client = Column(String, nullable=True)
    skills_used = Column(JSON, default=list)  # list of skill ids
    outcome_summary = Column(Text, nullable=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Certification(Base):
    __tablename__ = "certifications"

    id = Column(Integer, primary_key=True, index=True)
    engineer_id = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    issuer = Column(String, nullable=True)
    date = Column(DateTime, nullable=True)
    expiry = Column(DateTime, nullable=True)

    from sqlalchemy.orm import relationship
    from sqlalchemy import ForeignKey
    engineer_id = Column(Integer, ForeignKey("engineers.id"), nullable=False)
    engineer = relationship("Engineer", back_populates="certifications")
