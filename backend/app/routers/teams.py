from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.db import get_db
from app.core.security import require_role
from app.schemas.team import TeamComposeRequest, WhatIfJDRequest, WhatIfPortfolioRequest
from app.agents.orchestrator import orchestrator

router = APIRouter(prefix="/teams", tags=["teams"])


@router.post("/compose")
async def compose_team(
    payload: TeamComposeRequest,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role("admin", "leadership")),
):
    return await orchestrator.compose_team(payload.jd_id, payload.size, db)


@router.post("/whatif/jd")
async def whatif_jd(
    payload: WhatIfJDRequest,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role("admin", "leadership")),
):
    return await orchestrator.run_whatif(payload.jd_id, payload.team_size, payload.upskilling_weeks, db)


@router.post("/whatif/portfolio")
async def whatif_portfolio(
    payload: WhatIfPortfolioRequest,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role("admin", "leadership")),
):
    results = []
    for jd_id in payload.jd_ids:
        r = await orchestrator.run_whatif(jd_id, payload.team_size_per_jd, payload.upskilling_weeks, db)
        results.append(r)

    # Flag clashes: skills needed by multiple JDs with low coverage
    from collections import Counter
    skill_demand: Counter = Counter()
    for r in results:
        for g in r.get("gap_skills", []):
            skill_demand[g["skill_name"]] += 1

    clashes = [{"skill_name": sk, "jd_count": cnt} for sk, cnt in skill_demand.items() if cnt > 1]
    return {"per_jd": results, "cross_jd_clashes": clashes}
