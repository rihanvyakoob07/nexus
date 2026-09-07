"""Routes tasks to the appropriate model and estimates cost."""
from app.core.config import get_settings

settings = get_settings()

# Cost per 1K tokens (USD) — approximate as of mid-2025
_COSTS = {
    "gpt-4o": {"input": 0.005, "output": 0.015},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "gpt-4.1": {"input": 0.002, "output": 0.008},
    "text-embedding-3-large": {"input": 0.00013, "output": 0.0},
}

TRIAGE_TASKS = {"extract_skills", "classify_priority", "summarize"}
REASONING_TASKS = {"blueprint", "arena_question", "arena_evaluate", "match_explain", "gap_analyze", "team_compose", "learning_plan"}


def pick_model(task: str) -> str:
    if task in TRIAGE_TASKS:
        return settings.openai_model_triage
    return settings.openai_model_reasoning


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    rates = _COSTS.get(model, {"input": 0.005, "output": 0.015})
    return (input_tokens / 1000 * rates["input"]) + (output_tokens / 1000 * rates["output"])
