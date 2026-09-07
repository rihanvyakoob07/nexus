import io
import re
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pypdf import PdfReader
from docx import Document
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.resume_agent import run as parse_resume
from app.core.db import get_db
from app.core.security import get_current_user, require_role
from app.models.engineer import EngineerSkill, Evidence, Skill
from app.models.resume import Resume
from app.schemas.resume import ATSResult, ResumeOut
from app.services.ats_scoring import score_resume

router = APIRouter(prefix="/engineers/me/resume", tags=["resumes"])
MAX_BYTES = 10 * 1024 * 1024


def extract_text(filename: str, content: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        reader = PdfReader(io.BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    if suffix == ".docx":
        document = Document(io.BytesIO(content))
        return "\n".join(paragraph.text for paragraph in document.paragraphs)
    raise HTTPException(415, "Only PDF and DOCX resumes are supported")


@router.post("", response_model=ResumeOut, status_code=201)
async def upload_resume(file: UploadFile = File(...), db: AsyncSession = Depends(get_db), current_user=Depends(require_role("engineer"))):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".pdf", ".docx"}:
        raise HTTPException(415, "Only PDF and DOCX resumes are supported")
    content = await file.read()
    if not content:
        raise HTTPException(422, "Resume file is empty")
    if len(content) > MAX_BYTES:
        raise HTTPException(413, "Resume exceeds the 10 MB size limit")
    try:
        raw_text = extract_text(file.filename or "resume", content).strip()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(422, "Resume extraction failed") from exc
    if not raw_text:
        raise HTTPException(422, "Resume contains no extractable text")

    parsed = await parse_resume(raw_text, db)
    ats = score_resume(parsed, raw_text)
    await db.execute(update(Resume).where(Resume.engineer_id == current_user.id).values(is_active=False))
    resume = Resume(
        engineer_id=current_user.id,
        filename=Path(file.filename or "resume").name,
        file_path=None,
        raw_text=raw_text,
        parsed_data=parsed,
        ats_score=ats["ats_score"],
        ats_breakdown={**ats, "raw_text_length": len(raw_text)},
        status="processed",
        is_active=True,
    )
    db.add(resume)
    await db.flush()

    for skill_data in parsed.get("skills", []):
        name = skill_data.get("name", "").strip()
        if not name:
            continue
        skill = (await db.execute(select(Skill).where(Skill.name.ilike(name)))).scalar_one_or_none()
        if not skill:
            skill = Skill(name=name, category="Resume detected")
            db.add(skill)
            await db.flush()
        engineer_skill = (await db.execute(select(EngineerSkill).where(EngineerSkill.engineer_id == current_user.id, EngineerSkill.skill_id == skill.id))).scalar_one_or_none()
        score = float(skill_data.get("score", 0))
        if engineer_skill:
            engineer_skill.claimed_score = max(engineer_skill.claimed_score or 0, score)
            if engineer_skill.source not in {"proven", "demonstrated"}:
                engineer_skill.source = "claimed"
        else:
            db.add(EngineerSkill(engineer_id=current_user.id, skill_id=skill.id, claimed_score=score, confidence_score=score * 0.5, source="claimed"))
        db.add(Evidence(engineer_id=current_user.id, skill_id=skill.id, type="resume", description=skill_data.get("evidence", "Detected in uploaded resume"), ref_id=resume.id))
    return resume


@router.get("", response_model=ResumeOut)
async def get_resume(db: AsyncSession = Depends(get_db), current_user=Depends(require_role("engineer"))):
    resume = (await db.execute(select(Resume).where(Resume.engineer_id == current_user.id, Resume.is_active.is_(True)).order_by(Resume.uploaded_at.desc()))).scalar_one_or_none()
    if not resume:
        raise HTTPException(404, "No active resume found")
    return resume


@router.get("/ats", response_model=ATSResult)
async def get_resume_ats(db: AsyncSession = Depends(get_db), current_user=Depends(require_role("engineer"))):
    resume = (await db.execute(select(Resume).where(Resume.engineer_id == current_user.id, Resume.is_active.is_(True)).order_by(Resume.uploaded_at.desc()))).scalar_one_or_none()
    if not resume:
        raise HTTPException(404, "No active resume found")
    analysis = resume.ats_breakdown or {}
    return {"resume_id": resume.id, "ats_score": resume.ats_score or 0, "breakdown": analysis.get("breakdown", {}), "strengths": analysis.get("strengths", []), "weaknesses": analysis.get("weaknesses", []), "recommendations": analysis.get("recommendations", [])}


@router.delete("/{resume_id}", status_code=204)
async def archive_resume(resume_id: int, db: AsyncSession = Depends(get_db), current_user=Depends(require_role("engineer"))):
    resume = (await db.execute(select(Resume).where(Resume.id == resume_id, Resume.engineer_id == current_user.id))).scalar_one_or_none()
    if not resume:
        raise HTTPException(404, "Resume not found")
    resume.is_active = False
    return None
