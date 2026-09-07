import re
from typing import Any, Dict

from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import chat_completion, parse_json
from app.schemas.resume import ParsedResume
from app.services.cost_router import pick_model
from app.services.observability import log_agent_call

_SYSTEM = """Extract structured resume information as JSON matching this schema: name, email, summary, seniority, years_experience, skills (name, score 0-10, confidence 0-1, evidence), projects, certifications, technologies, client_experience, education. Scores must represent resume evidence only, never proven production capability. Return JSON only."""


def _fallback(text: str) -> ParsedResume:
    email = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text)
    known = ["Python", "FastAPI", "RAG Systems", "LangChain", "Azure AI Services", "MLOps", "Docker & Kubernetes", "Vector Databases", "React / Next.js", "OpenAI API", "TypeScript / Node.js"]
    skills = [
        {"name": skill, "score": 6.0, "confidence": 0.5, "evidence": "Detected in resume text"}
        for skill in known if skill.lower() in text.lower()
    ]
    return ParsedResume(email=email.group(0) if email else None, summary=text[:500], skills=skills, technologies=[item["name"] for item in skills])


async def run(resume_text: str, db: AsyncSession) -> dict:
    model = pick_model("resume_extraction")
    messages = [{"role": "system", "content": _SYSTEM}, {"role": "user", "content": resume_text[:50000]}]
    try:
        async with log_agent_call(db, "ResumeAgent", model, "resume_extraction") as tracker:
            raw, inp, out = await chat_completion(messages, model)
            tracker["input_tokens"] = inp
            tracker["output_tokens"] = out
        parsed = ParsedResume.model_validate(parse_json(raw))
    except (Exception, ValidationError):
        parsed = _fallback(resume_text)
    return parsed.model_dump()
