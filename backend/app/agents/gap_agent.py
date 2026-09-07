"""GapAgent — diffs engineer capabilities against JD blueprint."""
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.base import chat_completion, parse_json
from app.services.cost_router import pick_model
from app.services.observability import log_agent_call

_SYSTEM = """You are a capability gap analyst. Given an engineer's proven skills and a JD blueprint, identify gaps.

Return JSON:
{
  "gaps": [
    {
      "skill_name": "...",
      "severity": "critical|high|medium|low",
      "current_score": 0-10,
      "target_score": 0-10,
      "gap_explanation": "brief rationale",
      "upskilling_effort_weeks": int
    }
  ],
  "strengths": ["skills where engineer exceeds requirements"],
  "overall_gap_severity": "critical|high|medium|low",
  "readiness_summary": "plain English summary"
}"""


async def run(engineer_profile: dict, blueprint: dict, db: AsyncSession) -> dict:
    model = pick_model("gap_analyze")
    messages = [
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": f"Engineer: {engineer_profile}\n\nJD Blueprint: {blueprint}"},
    ]
    async with log_agent_call(db, "GapAgent", model, f"eng_{engineer_profile.get('id')}") as tracker:
        raw, inp, out = await chat_completion(messages, model)
        tracker["input_tokens"] = inp
        tracker["output_tokens"] = out
    return parse_json(raw)
