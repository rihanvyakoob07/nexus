"""TeamComposerAgent — selects an optimal roster from ranked candidates."""
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.base import chat_completion, parse_json
from app.services.cost_router import pick_model
from app.services.observability import log_agent_call

_SYSTEM = """You are an AI team composition expert. Given a JD blueprint and ranked candidates, compose an optimal team.

Rules:
- Avoid skill overlap redundancy: don't pick two engineers with identical top skills if alternatives cover other needed skills
- Maximise team-level coverage of critical JD skills
- Explain any swap decisions clearly ("Candidate F replaces Candidate B because team otherwise lacks MLOps coverage")

Return JSON:
{
  "members": [
    {
      "engineer_id": int,
      "role": "role title for this engagement",
      "rationale": "why this person was selected",
      "key_contribution": "primary skill/value they bring",
      "capability_score": 0-10
    }
  ],
  "swap_explanations": ["explanation of any non-obvious picks or swaps"],
  "team_capability_score": 0-10,
  "coverage_analysis": {"skill_name": "covered|partial|gap"},
  "risk_level": "low|medium|high",
  "risk_factors": ["list any coverage gaps or single-points-of-failure"]
}"""


async def run(blueprint: dict, candidates: list, size: int, db: AsyncSession) -> dict:
    model = pick_model("team_compose")
    messages = [
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": f"JD Blueprint: {blueprint}\nCandidates (ranked): {candidates}\nRequired team size: {size}"},
    ]
    async with log_agent_call(db, "TeamComposerAgent", model, "team_composition") as tracker:
        raw, inp, out = await chat_completion(messages, model)
        tracker["input_tokens"] = inp
        tracker["output_tokens"] = out
    return parse_json(raw)
