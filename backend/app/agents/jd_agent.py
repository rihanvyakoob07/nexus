"""JDAgent — extracts a structured capability blueprint from raw JD text."""
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.base import chat_completion, parse_json
from app.services.cost_router import pick_model
from app.services.observability import log_agent_call

_SYSTEM = """You are an expert AI capability analyst. Given a job description, produce a JSON capability blueprint.

Output JSON with this exact structure:
{
  "summary": "One-sentence role summary",
  "categories": {
    "technical": [{"skill": "skill name", "weight": 0.0-1.0, "priority": "critical|high|medium|nice_to_have", "rationale": "why"}],
    "architecture": [...],
    "engineering": [...],
    "delivery": [...]
  },
  "hidden_requirements": ["inferred skill or trait not explicitly stated"],
  "seniority_signal": "junior|mid|senior|principal",
  "team_fit_notes": "what kind of team culture/dynamic this role implies"
}

Be thorough. Extract ALL technical skills, frameworks, methodologies. Infer hidden requirements from context clues."""


async def run(jd_text: str, db: AsyncSession) -> dict:
    model = pick_model("blueprint")
    messages = [
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": f"Job Description:\n\n{jd_text}"},
    ]
    async with log_agent_call(db, "JDAgent", model, "jd_extraction") as tracker:
        raw, inp, out = await chat_completion(messages, model)
        tracker["input_tokens"] = inp
        tracker["output_tokens"] = out
    return parse_json(raw)
