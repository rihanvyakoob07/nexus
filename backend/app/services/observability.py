"""Logs every OpenAI call to the agent_calls table."""
import time
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.outcome import AgentCall
from app.services.cost_router import estimate_cost


@asynccontextmanager
async def log_agent_call(db: AsyncSession, agent_name: str, model: str, context_ref: str = ""):
    """Usage: async with log_agent_call(db, 'JDAgent', 'gpt-4o') as tracker: ..."""
    start = time.time()
    tracker = {"input_tokens": 0, "output_tokens": 0}
    try:
        yield tracker
    finally:
        latency = (time.time() - start) * 1000
        cost = estimate_cost(model, tracker["input_tokens"], tracker["output_tokens"])
        call = AgentCall(
            agent_name=agent_name,
            model_used=model,
            input_tokens=tracker["input_tokens"],
            output_tokens=tracker["output_tokens"],
            latency_ms=latency,
            cost_estimate=cost,
            context_ref=context_ref,
        )
        db.add(call)
        await db.flush()
