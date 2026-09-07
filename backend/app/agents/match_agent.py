"""MatchAgent — deterministic capability matching with LLM explanations."""
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.base import chat_completion, parse_json
from app.services.cost_router import pick_model
from app.services.observability import log_agent_call
import json


_SYSTEM = """You are an AI talent matching explanation engine. The candidate scores have already been calculated deterministically from the JD requirements and the engineer's complete skill profile. Do NOT change the scores.

For each candidate return:
{
  "engineer_id": int,
  "strengths": ["strong matching areas"],
  "gaps": ["missing or weak areas"],
  "explanation": "2-3 sentence plain-English rationale grounded only in the supplied data"
}

Return JSON: {"rankings": [...]}"""


def _flatten_requirements(blueprint: dict) -> list[dict]:
    requirements = []
    for category in (blueprint or {}).get("categories", {}).values():
        if isinstance(category, list):
            requirements.extend(item for item in category if isinstance(item, dict) and item.get("skill"))
    return requirements


def _deterministic_score(engineer: dict, requirements: list[dict]) -> dict:
    """Score the complete skill inventory; LLM is deliberately excluded from scoring."""
    skills = {
        str(s.get("skill_name", "")).strip().lower(): s
        for s in engineer.get("skills", [])
        if s.get("skill_name")
    }

    weighted_total = 0.0
    weighted_match = 0.0
    matched = []
    gaps = []

    for req in requirements:
        name = str(req["skill"]).strip()
        weight = float(req.get("weight", 0.5) or 0.5)
        priority = str(req.get("priority", "medium")).lower()
        # Critical requirements receive additional weight while preserving the
        # original blueprint weight as the primary signal.
        priority_multiplier = {"critical": 1.5, "high": 1.25, "medium": 1.0, "low": 0.75}.get(priority, 1.0)
        effective_weight = weight * priority_multiplier
        weighted_total += effective_weight

        skill = skills.get(name.lower())
        confidence = float(skill.get("confidence_score", 0) or 0) if skill else 0.0
        contribution = min(confidence / 10.0, 1.0) * effective_weight
        weighted_match += contribution

        if confidence >= 6:
            matched.append(name)
        else:
            gaps.append(name)

    technical = (weighted_match / weighted_total * 10.0) if weighted_total else 0.0
    # With no historical assessment/experience signal, keep those dimensions
    # neutral rather than inventing evidence. The overall score is therefore
    # anchored to the measurable capability match.
    overall = technical

    return {
        "engineer_id": engineer.get("id"),
        "overall_score": round(overall, 2),
        "breakdown": {
            "technical_skills": round(technical, 2),
            "relevant_experience": 0.0,
            "architecture_ability": 0.0,
            "prior_assessment_results": 0.0,
        },
        "_matched": matched,
        "_gaps": gaps,
    }


async def run(blueprint: dict, engineers: list, db: AsyncSession) -> list:
    """Score every engineer using the complete skill inventory, then use the LLM only for explanations."""
    requirements = _flatten_requirements(blueprint)
    if not requirements:
        return []

    scored = [_deterministic_score(engineer, requirements) for engineer in engineers]
    scored.sort(key=lambda item: item["overall_score"], reverse=True)

    # Explain only the strongest candidates to control token cost. Scores are
    # retained exactly as calculated above.
    candidates_for_explanation = [
        {
            "id": item["engineer_id"],
            "score": item["overall_score"],
            "breakdown": item["breakdown"],
            "matched": item["_matched"],
            "gaps": item["_gaps"],
        }
        for item in scored[:15]
    ]

    model = pick_model("match_explain")
    messages = [
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": f"Blueprint requirements:\n{json.dumps(requirements, separators=(',', ':'))}\n\nCandidates:\n{json.dumps(candidates_for_explanation, separators=(',', ':'))}"},
    ]

    explanations = {}
    async with log_agent_call(db, "MatchAgent", model, "explanation") as tracker:
        raw, inp, out = await chat_completion(messages, model)
        tracker["input_tokens"] = inp
        tracker["output_tokens"] = out
    try:
        explanation_result = parse_json(raw)
        explanations = {
            int(item["engineer_id"]): item
            for item in explanation_result.get("rankings", [])
            if item.get("engineer_id") is not None
        }
    except (ValueError, TypeError, KeyError):
        explanations = {}

    rankings = []
    for item in scored:
        explanation = explanations.get(item["engineer_id"], {})
        rankings.append({
            "engineer_id": item["engineer_id"],
            "overall_score": item["overall_score"],
            "breakdown": item["breakdown"],
            "strengths": explanation.get("strengths", item["_matched"]),
            "gaps": explanation.get("gaps", item["_gaps"]),
            "explanation": explanation.get(
                "explanation",
                f"Matched {len(item['_matched'])} of {len(requirements)} required capabilities at or above the confidence threshold."
            ),
        })
    return rankings
