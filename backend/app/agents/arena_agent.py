"""ArenaAgent — conducts a multi-turn adaptive technical assessment."""
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.base import chat_completion, parse_json
from app.services.cost_router import pick_model
from app.services.observability import log_agent_call

_QUESTION_SYSTEM = """You are an expert technical interviewer conducting an adaptive assessment.
Given the JD blueprint and conversation history, generate the next scenario-based question.
Target the weakest sub-dimension from the candidate's last answer.
Questions should be open-ended, scenario-driven, and test architecture/scalability/security depth.

Return JSON: {"question": "...", "target_skill": "...", "target_dimension": "architecture|scalability|security|reliability|implementation"}"""

_EVAL_SYSTEM = """You are an expert technical evaluator. Evaluate this answer using the supplied rubric.
Score each dimension from 0-10 based only on observable evidence in the answer.
A score is not a statement of absolute ability; it is an assessment signal with confidence.
Return JSON:
{
  "scores": {
    "architecture": 0-10,
    "scalability": 0-10,
    "security": 0-10,
    "reliability": 0-10,
    "implementation": 0-10
  },
  "overall": 0-10,
  "confidence": 0-1,
  "weakest_dimension": "dimension name",
  "feedback": "brief evaluator note grounded in the answer",
  "evidence": ["specific observable evidence from the answer"],
  "skill_scores": {"skill_name": score}
}"""

_FINAL_SYSTEM = """Synthesize the complete assessment.
Do not invent a score. The final overall score will be calculated deterministically from the recorded turn evaluations.
Return JSON:
{
  "skill_scores": {"skill_name": 0-10},
  "readiness_level": "not_ready|developing|ready|highly_ready",
  "summary": "2-3 sentence assessment summary grounded in the turns",
  "strengths": ["..."],
  "development_areas": ["..."]
}"""

MAX_TURNS = 5


async def generate_first_question(blueprint: dict, engineer_profile: dict, db: AsyncSession) -> dict:
    model = pick_model("arena_question")
    messages = [
        {"role": "system", "content": _QUESTION_SYSTEM},
        {"role": "user", "content": f"JD Blueprint: {blueprint}\nEngineer Profile: {engineer_profile}\nGenerate the opening scenario question targeting the top critical skill."},
    ]
    async with log_agent_call(db, "ArenaAgent", model, "first_question") as tracker:
        raw, inp, out = await chat_completion(messages, model)
        tracker["input_tokens"] = inp
        tracker["output_tokens"] = out
    return parse_json(raw)


async def evaluate_answer(question: str, answer: str, blueprint: dict, db: AsyncSession) -> dict:
    model = pick_model("arena_evaluate")
    messages = [
        {"role": "system", "content": _EVAL_SYSTEM},
        {"role": "user", "content": f"Question: {question}\nAnswer: {answer}\nJD Context: {blueprint}"},
    ]
    async with log_agent_call(db, "ArenaAgent", model, "evaluate_answer") as tracker:
        raw, inp, out = await chat_completion(messages, model)
        tracker["input_tokens"] = inp
        tracker["output_tokens"] = out
    result = parse_json(raw)
    result["confidence"] = max(0.0, min(1.0, float(result.get("confidence", 0.5))))
    result["evidence"] = [str(item) for item in result.get("evidence", [])][:5]
    return result


async def generate_followup(evaluation: dict, history: list, blueprint: dict, db: AsyncSession) -> dict:
    model = pick_model("arena_question")
    messages = [
        {"role": "system", "content": _QUESTION_SYSTEM},
        {"role": "user", "content": f"Last evaluation: {evaluation}\nHistory: {history}\nBlueprint: {blueprint}\nGenerate adversarial follow-up targeting weakest_dimension: {evaluation.get('weakest_dimension')}."},
    ]
    async with log_agent_call(db, "ArenaAgent", model, "followup_question") as tracker:
        raw, inp, out = await chat_completion(messages, model)
        tracker["input_tokens"] = inp
        tracker["output_tokens"] = out
    return parse_json(raw)


async def finalize_assessment(turns: list, blueprint: dict, db: AsyncSession) -> dict:
    # Aggregate recorded rubric scores instead of trusting an LLM-generated final score.
    dimension_names = ("architecture", "scalability", "security", "reliability", "implementation")
    evaluations = [t.get("ai_evaluation") or {} for t in turns if t.get("ai_evaluation")]
    dimension_scores = []
    confidences = []
    for evaluation in evaluations:
        scores = evaluation.get("scores") or {}
        values = [float(scores[name]) for name in dimension_names if isinstance(scores.get(name), (int, float))]
        if values:
            dimension_scores.append(sum(values) / len(values))
            confidences.append(max(0.0, min(1.0, float(evaluation.get("confidence", 0.5)))))

    deterministic_overall = round(sum(dimension_scores) / len(dimension_scores), 2) if dimension_scores else 0.0
    assessment_confidence = round(sum(confidences) / len(confidences), 2) if confidences else 0.0

    model = pick_model("arena_evaluate")
    messages = [
        {"role": "system", "content": _FINAL_SYSTEM},
        {"role": "user", "content": f"All assessment turns: {turns}\nJD Blueprint: {blueprint}\nDeterministic overall score: {deterministic_overall}\nAssessment confidence: {assessment_confidence}"},
    ]
    async with log_agent_call(db, "ArenaAgent", model, "finalize") as tracker:
        raw, inp, out = await chat_completion(messages, model)
        tracker["input_tokens"] = inp
        tracker["output_tokens"] = out
    result = parse_json(raw)
    result["overall_score"] = deterministic_overall
    result["confidence"] = assessment_confidence
    result["evidence_count"] = sum(len((t.get("ai_evaluation") or {}).get("evidence", [])) for t in turns)
    return result
