"""LearningAgent — generates a personalised week-by-week upskilling plan."""
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.base import chat_completion, parse_json
from app.services.cost_router import pick_model
from app.services.observability import log_agent_call

_SYSTEM = """You are an expert AI learning path designer. Given an engineer's gaps, design a week-by-week upskilling plan.

Return JSON:
{
  "weeks": [
    {
      "week": int,
      "focus_skill": "skill name",
      "activities": ["specific learning activity"],
      "milestone": "what they should be able to do by end of week",
      "resources": ["specific course/resource names"],
      "projected_score_gain": 0-10
    }
  ],
  "capstone_project": {
    "title": "...",
    "description": "...",
    "skills_demonstrated": ["..."],
    "duration_weeks": int
  },
  "projected_readiness_date_weeks": int,
  "projected_final_score": 0-10,
  "success_criteria": "how to verify readiness"
}"""


async def run(gaps: list, engineer_profile: dict, db: AsyncSession) -> dict:
    model = pick_model("learning_plan")
    messages = [
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": f"Engineer: {engineer_profile}\nGaps to address: {gaps}"},
    ]
    async with log_agent_call(db, "LearningAgent", model, f"eng_{engineer_profile.get('id')}") as tracker:
        raw, inp, out = await chat_completion(messages, model)
        tracker["input_tokens"] = inp
        tracker["output_tokens"] = out
    return parse_json(raw)
