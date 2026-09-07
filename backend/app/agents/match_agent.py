"""MatchAgent — scores engineers against a JD blueprint and ranks them."""
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.base import chat_completion, parse_json
from app.services.cost_router import pick_model
from app.services.observability import log_agent_call
import json


_SYSTEM = """You are an AI talent matching engine. Given a JD capability blueprint and a list of engineer profiles, score each engineer (0-10) across these dimensions:
- technical_skills (weighted match of required skills)
- relevant_experience (project history alignment)
- architecture_ability (design/system thinking signals)
- prior_assessment_results (Arena scores if present)

For each engineer output:
{
  "engineer_id": int,
  "overall_score": float,
  "breakdown": {
    "technical_skills": float,
    "relevant_experience": float,
    "architecture_ability": float,
    "prior_assessment_results": float
  },
  "strengths": ["list of strongest matching areas"],
  "gaps": ["list of missing or weak areas"],
  "explanation": "2-3 sentence plain-English rationale"
}

Return JSON: {"rankings": [...sorted by overall_score desc...]}"""


async def run(blueprint: dict, engineers: list, db: AsyncSession) -> list:
    """engineers: list of dicts with id, name, skills, evidence etc."""
    model = pick_model("match_explain")
    compact_engineers = [
        {
            "id": engineer.get("id"),
            "skills": [
                {
                    "skill_name": skill.get("skill_name"),
                    "confidence_score": skill.get("confidence_score"),
                    "source": skill.get("source"),
                }
                for skill in sorted(engineer.get("skills", []), key=lambda item: item.get("confidence_score", 0), reverse=True)[:3]
            ],
        }
        for engineer in engineers
    ]
    messages = [
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": f"Blueprint:\n{json.dumps(blueprint, separators=(',', ':'))}\n\nEngineers:\n{json.dumps(compact_engineers, separators=(',', ':'))}"},
    ]
    async with log_agent_call(db, "MatchAgent", model, "ranking") as tracker:
        raw, inp, out = await chat_completion(messages, model)
        tracker["input_tokens"] = inp
        tracker["output_tokens"] = out
    result = parse_json(raw)
    return result.get("rankings", [])
