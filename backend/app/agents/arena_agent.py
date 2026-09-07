"""ArenaAgent — conducts a multi-turn adaptive technical assessment."""
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.base import chat_completion, chat_text, parse_json
from app.services.cost_router import pick_model
from app.services.observability import log_agent_call

_QUESTION_SYSTEM = """You are an expert technical interviewer conducting an adaptive assessment.
Given the JD blueprint and conversation history, generate the next scenario-based question.
Target the weakest sub-dimension from the candidate's last answer.
Questions should be open-ended, scenario-driven, and test architecture/scalability/security depth.

Return JSON: {"question": "...", "target_skill": "...", "target_dimension": "architecture|scalability|security|reliability|implementation"}"""

_EVAL_SYSTEM = """You are an expert technical evaluator. Evaluate this answer across sub-dimensions.
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
  "weakest_dimension": "dimension name",
  "feedback": "brief evaluator note",
  "skill_scores": {"skill_name": score}
}"""

_FINAL_SYSTEM = """Synthesize the complete assessment into final skill scores.
Return JSON:
{
  "skill_scores": {"skill_name": 0-10},
  "overall_score": 0-10,
  "readiness_level": "not_ready|developing|ready|highly_ready",
  "summary": "2-3 sentence assessment summary",
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
    return parse_json(raw)


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
    model = pick_model("arena_evaluate")
    messages = [
        {"role": "system", "content": _FINAL_SYSTEM},
        {"role": "user", "content": f"All assessment turns: {turns}\nJD Blueprint: {blueprint}"},
    ]
    async with log_agent_call(db, "ArenaAgent", model, "finalize") as tracker:
        raw, inp, out = await chat_completion(messages, model)
        tracker["input_tokens"] = inp
        tracker["output_tokens"] = out
    return parse_json(raw)
