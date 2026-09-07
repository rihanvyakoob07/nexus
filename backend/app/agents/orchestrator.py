"""Orchestrator — owns full workflows and decides agent invocation order."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.engineer import Engineer, EngineerSkill, Skill
from app.models.jd import JD, JDCapability, Match
from app.models.assessment import Assessment
from app.models.gap_learning import SkillGap, LearningPath, Team
from app.models.outcome import Deployment
from app.services.capability_graph import (
    get_all_engineers_skill_map,
    get_jd_skill_requirements,
    has_recent_proven_evidence,
)
from app.services.confidence_scoring import compute_engagement_capability_score
from app.agents import jd_agent, match_agent, arena_agent, gap_agent, learning_agent, team_composer_agent, outcome_recalibration
from datetime import datetime, timezone
import json


class Orchestrator:

    async def process_jd(self, jd_text: str, client_name: str, db: AsyncSession) -> dict:
        """Full JD processing: extract blueprint → match → flag assessments → identify gaps."""
        # 1. Extract blueprint
        blueprint = await jd_agent.run(jd_text, db)

        # 2. Persist JD
        jd = JD(client_name=client_name, raw_text=jd_text, capability_blueprint=blueprint)
        db.add(jd)
        await db.flush()

        # 3. Resolve/upsert skills from blueprint
        skill_ids = await self._ensure_skills(blueprint, db)

        # 4. Persist JD capabilities
        all_skills_flat = self._flatten_blueprint_skills(blueprint)
        for skill_entry in all_skills_flat:
            skill_id = skill_ids.get(skill_entry["skill"])
            if skill_id:
                cap = JDCapability(
                    jd_id=jd.id,
                    skill_id=skill_id,
                    weight=skill_entry.get("weight", 0.5),
                    priority=skill_entry.get("priority", "medium"),
                )
                db.add(cap)
        await db.flush()

        # 5. Get engineer skill map and run match agent
        skill_map = await get_all_engineers_skill_map(db)
        eng_res = await db.execute(select(Engineer))
        engineers = eng_res.scalars().all()
        engineer_profiles = self._build_profiles(engineers, skill_map)

        rankings = await match_agent.run(blueprint, engineer_profiles, db)

        # 6. Persist matches and queue Arena where needed
        critical_skill_ids = [sid for name, sid in skill_ids.items()
                               if any(s.get("priority") == "critical" and s.get("skill") == name
                                      for s in all_skills_flat)]
        for rank in rankings[:15]:
            eng_id = rank.get("engineer_id")
            m = Match(
                jd_id=jd.id,
                engineer_id=eng_id,
                jd_match_score=rank.get("overall_score", 0.0),
                breakdown=rank.get("breakdown"),
                explanation=rank.get("explanation"),
            )
            db.add(m)

        # 7. Compute gaps for top candidates
        gaps_summary = []
        for rank in rankings[:5]:
            eng_profile = next((e for e in engineer_profiles if e["id"] == rank.get("engineer_id")), None)
            if eng_profile:
                gap_result = await gap_agent.run(eng_profile, blueprint, db)
                gaps_summary.append({"engineer_id": rank["engineer_id"], "gaps": gap_result})

        await db.flush()
        return {
            "jd_id": jd.id,
            "blueprint": blueprint,
            "candidates": rankings[:10],
            "gaps_summary": gaps_summary,
        }

    async def compose_team(self, jd_id: int, size: int, db: AsyncSession) -> dict:
        jd_res = await db.execute(select(JD).where(JD.id == jd_id))
        jd = jd_res.scalar_one_or_none()
        if not jd:
            return {"error": "JD not found"}

        blueprint = jd.capability_blueprint or {}
        matches_res = await db.execute(
            select(Match).where(Match.jd_id == jd_id).order_by(Match.jd_match_score.desc())
        )
        matches = matches_res.scalars().all()

        skill_map = await get_all_engineers_skill_map(db)
        eng_res = await db.execute(select(Engineer))
        engineers = eng_res.scalars().all()
        profiles = self._build_profiles(engineers, skill_map)

        ranked_candidates = []
        for m in matches:
            prof = next((p for p in profiles if p["id"] == m.engineer_id), None)
            if prof:
                ranked_candidates.append({**prof, "match_score": m.jd_match_score, "explanation": m.explanation})

        composition = await team_composer_agent.run(blueprint, ranked_candidates, size, db)

        member_scores = [m.get("capability_score", 0) for m in composition.get("members", [])]
        ecs = compute_engagement_capability_score(member_scores)

        team = Team(
            jd_id=jd_id,
            composition=composition.get("members", []),
            team_capability_score=composition.get("team_capability_score", 0),
            engagement_capability_score=ecs,
            risk_level=composition.get("risk_level", "medium"),
        )
        db.add(team)
        await db.flush()

        return {**composition, "team_id": team.id, "engagement_capability_score": ecs}

    async def run_whatif(self, jd_id: int, team_size: int, upskilling_weeks: int, db: AsyncSession) -> dict:
        jd_res = await db.execute(select(JD).where(JD.id == jd_id))
        jd = jd_res.scalar_one_or_none()
        if not jd:
            return {"error": "JD not found"}

        reqs = await get_jd_skill_requirements(db, jd_id)
        skill_map = await get_all_engineers_skill_map(db)
        all_skills = [s for skills in skill_map.values() for s in skills]

        coverage_hits = 0
        total_weight = sum(r["weight"] for r in reqs)
        covered_weight = 0.0
        gap_skills = []

        for req in reqs:
            matching = [s for s in all_skills if s["skill_id"] == req["skill_id"] and s["confidence_score"] >= 6]
            if matching:
                covered_weight += req["weight"]
            else:
                gap_skills.append({
                    "skill_name": req["skill_name"],
                    "priority": req["priority"],
                    "upskilling_weeks": 4 if req["priority"] == "critical" else 2,
                })

        current_pct = (covered_weight / total_weight * 100) if total_weight else 0
        addressable_in_window = [g for g in gap_skills if g["upskilling_weeks"] <= upskilling_weeks]
        projected_pct = min(100, current_pct + len(addressable_in_window) / max(len(reqs), 1) * 100)

        return {
            "jd_id": jd_id,
            "current_coverage_pct": round(current_pct, 1),
            "gap_skills": gap_skills,
            "projected_coverage_pct": round(projected_pct, 1),
            "upskilling_recommendation": (
                "Hire" if len(gap_skills) > len(reqs) * 0.5 else "Upskill existing engineers"
            ),
        }

    async def recalibrate_from_outcome(self, deployment_id: int, db: AsyncSession) -> dict:
        return await outcome_recalibration.run(deployment_id, db)

    def _flatten_blueprint_skills(self, blueprint: dict) -> list:
        skills = []
        for category in blueprint.get("categories", {}).values():
            skills.extend(category)
        return skills

    async def _ensure_skills(self, blueprint: dict, db: AsyncSession) -> dict:
        """Upsert skills from blueprint, return {name: id} map."""
        from sqlalchemy.dialects.sqlite import insert as sqlite_insert
        skill_map = {}
        for s in self._flatten_blueprint_skills(blueprint):
            name = s.get("skill", "")
            if not name:
                continue
            res = await db.execute(select(Skill).where(Skill.name == name))
            skill = res.scalar_one_or_none()
            if not skill:
                skill = Skill(name=name, category=None)
                db.add(skill)
                await db.flush()
            skill_map[name] = skill.id
        return skill_map

    def _build_profiles(self, engineers: list, skill_map: dict) -> list:
        profiles = []
        for eng in engineers:
            skills = skill_map.get(eng.id, [])
            profiles.append({
                "id": eng.id,
                "name": eng.name,
                "seniority": eng.seniority,
                "role": eng.role,
                "skills": skills,
            })
        return profiles


orchestrator = Orchestrator()
