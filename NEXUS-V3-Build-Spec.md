# NEXUS V3 — End-to-End Build Specification
**AI Engineering Capability Intelligence Platform**
*Know what we can do. Prove what we can do. Predict what we'll need next.*

---

## 1. Tech Stack

| Layer | Choice |
|---|---|
| Frontend | Next.js 14 (App Router), TypeScript, TailwindCSS, shadcn/ui, Recharts |
| Backend | Python FastAPI, Pydantic v2, SQLAlchemy 2.0 (async) |
| Database | SQLite (local, file-based) — swappable to Postgres later via same SQLAlchemy models |
| AI | OpenAI API (GPT-4.1/4o-class for reasoning + assessment, `text-embedding-3-large` for retrieval) |
| Vector store | Local — `sqlite-vec` or `chromadb` (embedded, no external service) |
| Auth | JWT (FastAPI + `python-jose`), 3 roles: `leadership`, `admin`, `engineer` |
| Background jobs | FastAPI `BackgroundTasks` (V1) → upgrade path to Celery/Redis if needed later |
| Observability | Simple structured logging table (`agent_calls`) capturing latency, tokens, cost, model used |

---

## 2. System Architecture

```
                         Next.js Frontend
                    (Leadership / Admin / Engineer)
                                │
                          REST API (FastAPI)
                                │
                       ┌────────▼────────┐
                       │  AI ORCHESTRATOR │
                       └────────┬────────┘
        ┌──────────┬───────────┼───────────┬──────────┬─────────┐
        ▼          ▼           ▼           ▼          ▼         ▼
   JD Agent   Match Agent  Arena Agent  Gap Agent  Learning  Team
   (extract)  (rank)       (assess)     (diff)     Agent     Composer
        └──────────┴───────────┼───────────┴──────────┴─────────┘
                                ▼
                        Capability Graph
                (Engineers ↔ Skills ↔ Projects ↔ JDs ↔ Evidence)
                                │
                   ┌────────────┼────────────┐
                   ▼            ▼            ▼
              SQLite DB   Vector Store   Outcome Log
                                │
                         Recalibration Loop
                       (feeds back into Match/Arena scoring)
```

The **Orchestrator** is a single FastAPI service function/class that owns the request lifecycle end-to-end (e.g. "process new JD" or "assess engineer for opportunity X"), decides which of the 6 agents to call, in what order, and whether an agent call can be skipped (e.g. skip Arena if valid, recent, proven evidence already exists). All agents are plain Python classes with a single `.run(input) -> output` interface, callable independently for testing but always invoked *through* the orchestrator in production flows.

---

## 3. Database Schema (SQLite via SQLAlchemy)

**Core entities**
- `engineers` (id, name, email, role, seniority, created_at)
- `skills` (id, name, category) — e.g. RAG, Agentic AI, MLOps, Azure AI
- `engineer_skills` (engineer_id, skill_id, claimed_score, source: claimed/demonstrated/proven, last_updated)
- `evidence` (id, engineer_id, skill_id, type: project/certification/assessment/client_delivery, description, ref_id, date)
- `projects` (id, name, client, skills_used[], outcome_summary)
- `certifications` (id, engineer_id, name, issuer, date, expiry)

**JD & matching**
- `jds` (id, client_name, raw_text, capability_blueprint JSON, created_at)
- `jd_capabilities` (jd_id, skill_id, weight, priority: critical/high/medium/nice_to_have)
- `matches` (jd_id, engineer_id, jd_match_score, breakdown JSON, created_at)

**Assessment (Arena)**
- `assessments` (id, engineer_id, jd_id, status, started_at, completed_at)
- `assessment_turns` (assessment_id, turn_index, question, answer, ai_evaluation JSON)
- `assessment_scores` (assessment_id, skill_id, score, confidence)

**Gap, learning, teams**
- `skill_gaps` (engineer_id or jd_id context, skill_id, severity, target_score)
- `learning_paths` (id, engineer_id, plan JSON, status, projected_readiness_date)
- `teams` (id, jd_id, composition JSON, team_capability_score, risk_level)

**Outcomes — the ground truth loop**
- `deployments` (id, engineer_id, jd_id, team_id, start_date, end_date)
- `outcomes` (deployment_id, client_feedback_score, delivery_success: bool, issues_reported JSON, recorded_at)

**Observability**
- `agent_calls` (id, agent_name, model_used, input_tokens, output_tokens, latency_ms, cost_estimate, timestamp)

**Capability Confidence (derived, computed not stored raw)**
`confidence = f(skill_score, evidence_strength, recency, production_experience)` — computed in a service function, cached in `engineer_skills.confidence_score`.

---

## 4. Backend Plan (FastAPI)

### 4.1 Folder structure
```
backend/
  app/
    main.py
    core/
      config.py
      security.py           # JWT auth
      db.py                 # SQLAlchemy session
    models/                 # SQLAlchemy models (per table above)
    schemas/                # Pydantic request/response models
    agents/
      orchestrator.py
      jd_agent.py
      match_agent.py
      arena_agent.py
      gap_agent.py
      learning_agent.py
      team_composer_agent.py
      outcome_recalibration.py
    services/
      capability_graph.py   # graph queries over relational data
      confidence_scoring.py
      embeddings.py         # OpenAI embeddings + local vector store
      cost_router.py        # picks model per task type
    routers/
      jds.py
      engineers.py
      assessments.py
      teams.py
      dashboard.py
      whatif.py
      auth.py
    tests/
  requirements.txt
```

### 4.2 Key endpoints (V1→V3 scope, build in this order)

**MVP**
- `POST /jds` — upload JD → runs JD Agent → returns capability blueprint
- `GET /jds/{id}/matches` — runs Match Agent → ranked candidates with explainability
- `GET /engineers/{id}` — capability passport view
- `POST /auth/login`

**V2**
- `POST /assessments` — start an Arena session for engineer + JD
- `POST /assessments/{id}/turn` — submit answer, get next adaptive question
- `GET /assessments/{id}/result` — final skill breakdown + readiness score
- `GET /engineers/{id}/gaps` — Skill Gap Agent output
- `POST /learning-paths` — generate upskilling plan

**V3**
- `POST /teams/compose` — Team Composer Agent, natural-language input ("build me a 6-person team for X")
- `POST /whatif/jd` — single-JD capacity simulation
- `POST /whatif/portfolio` — multi-JD, CU-wide capacity planning
- `POST /deployments/{id}/outcome` — record client feedback/delivery outcome
- `GET /dashboard/leadership` / `/admin` / `/engineer` — aggregated views per role

### 4.3 Orchestrator logic (pseudocode)
```python
class Orchestrator:
    async def process_jd(self, jd_text: str):
        blueprint = await jd_agent.run(jd_text)
        candidates = await match_agent.run(blueprint)
        for c in candidates[:10]:
            if not evidence_service.has_recent_proof(c, blueprint):
                await arena_agent.queue(c, blueprint)   # only assess if needed
        gaps = gap_agent.run(candidates, blueprint)
        return {"blueprint": blueprint, "candidates": candidates, "gaps": gaps}

    async def compose_team(self, jd_id, size):
        candidates = await self.process_jd_cached(jd_id)
        team = await team_composer_agent.run(candidates, size)
        return team

    async def recalibrate(self, outcome):
        await outcome_recalibration.run(outcome)  # adjusts scoring weights
```

### 4.4 Cost-aware model routing
- Simple extraction / triage → `gpt-4o-mini`
- Capability blueprint reasoning, adaptive Arena questioning, evaluation → `gpt-4.1` / `gpt-4o`
- Embeddings for retrieval/graph similarity → `text-embedding-3-large`
- Log every call's model + token + latency to `agent_calls` for the leadership observability panel.

---

## 5. Frontend Plan (Next.js)

### 5.1 Structure
```
frontend/
  app/
    (auth)/login/
    leadership/
      dashboard/page.tsx        # capability coverage, gaps, radar, what-if
      whatif/page.tsx
    admin/
      jds/page.tsx              # upload JD, view blueprint
      jds/[id]/matches/page.tsx # ranked candidates, explainability
      teams/compose/page.tsx    # team composer UI
    engineer/
      passport/page.tsx         # capability passport
      opportunities/page.tsx    # matched opportunities
      assessment/[id]/page.tsx  # Arena chat-style interface
      learning-path/page.tsx
    components/
      CapabilityBar.tsx
      EvidenceTrail.tsx
      ReadinessGauge.tsx
      SkillRadarChart.tsx
      TeamRoster.tsx
      ArenaChat.tsx
  lib/
    api.ts        # typed fetch wrapper to FastAPI
    auth.ts
```

### 5.2 Three dashboards (what each role sees)
- **Leadership**: capability coverage %, gap alerts, demand radar, what-if simulator, north-star metric (Capability-to-Deployment Velocity)
- **Admin**: JD upload → blueprint → ranked matches with evidence → team composer → readiness before proposing to client
- **Engineer**: capability passport, matched opportunities, Arena assessment flow, personalized learning path with projected readiness date

---

## 6. Feature List by Phase

**MVP (Weeks 1–4)**
JD upload + blueprint extraction · Capability Graph (basic relational, not yet vector-heavy) · Rank & explain matches · Capability Passport view · Auth + 3 roles

**V2 (Weeks 5–8)**
Arena adaptive assessment (multi-turn, adversarial follow-ups) · Skill Gap Agent · Personalized Learning Path generator · Capability Confidence scoring (score × evidence × recency × production exposure)

**V3 (Weeks 9–12)**
Team Composer (NL input → optimized roster, explainable swaps) · What-If simulation (single JD + portfolio-level) · Future Demand Radar (trend across JDs) · Outcome capture + recalibration loop · Observability dashboard (cost/latency/model routing) · Engagement Capability Score (team/engagement-level, not individual, for anything client-facing)

---

## 7. The Master End-to-End Build Prompt

Copy everything in the box below into Claude Code (or another agentic coding tool) as the initial project prompt. It's written to be handed to an AI coding agent directly.

```
Build a full-stack application called NEXUS — an AI Engineering Capability
Intelligence Platform. Tech stack: Next.js 14 (App Router, TypeScript,
TailwindCSS, shadcn/ui) frontend; Python FastAPI backend (async SQLAlchemy 2.0,
Pydantic v2); SQLite as the local database; OpenAI API (gpt-4o / gpt-4o-mini)
for all AI reasoning; text-embedding-3-large + a local embedded vector store
(chromadb) for retrieval; JWT auth with three roles: leadership, admin, engineer.

CORE CONCEPT
NEXUS maps engineers' proven capabilities against client job requirements,
assesses readiness through adaptive AI interviews, identifies skill gaps,
generates upskilling plans, composes optimal teams, and recalibrates all
scoring based on real project outcomes. Optimize for "fastest path to a
successful client deployment," not just highest match score.

BUILD ORDER — please work in this sequence and confirm each phase works
before moving to the next:

PHASE 1 — Backend foundation
- Set up FastAPI project structure per this layout: app/core, app/models,
  app/schemas, app/agents, app/services, app/routers.
- SQLAlchemy models for: engineers, skills, engineer_skills, evidence,
  projects, certifications, jds, jd_capabilities, matches, assessments,
  assessment_turns, assessment_scores, skill_gaps, learning_paths, teams,
  deployments, outcomes, agent_calls.
- JWT auth (register/login) with 3 roles.
- Seed script generating ~30 synthetic engineers with realistic AI
  engineering skills, projects, and evidence, plus ~10 synthetic client JDs.

PHASE 2 — Core AI agents (each as a standalone class with a .run() method)
- JDAgent: takes raw JD text, calls OpenAI to produce a structured capability
  blueprint (technical/architecture/engineering/delivery categories, each
  skill weighted and prioritized critical/high/medium/nice-to-have),
  including inferred hidden requirements not explicitly stated in the JD.
- MatchAgent: given a blueprint, scores all engineers on weighted dimensions
  (technical skills, relevant experience, project similarity, prior
  assessment results, architecture ability) and returns ranked candidates
  with a natural-language explanation of why each was ranked, and what's
  missing.
- ArenaAgent: conducts a multi-turn adaptive technical assessment. Starts
  with a scenario question tied to the JD's top skills, evaluates the
  answer across sub-dimensions (architecture, scalability, security, etc.),
  and generates an adversarial follow-up question targeting the weakest
  sub-dimension. Repeat for 4-6 turns, then output a final skill score
  breakdown.
- GapAgent: diffs an engineer's (or a group's) proven capabilities against
  a JD blueprint or portfolio of JDs, returns severity-ranked gaps.
- LearningAgent: given gaps, generates a week-by-week upskilling plan with
  a capstone project and a projected readiness date/score.
- TeamComposerAgent: given a JD and team size, selects an optimal roster
  from ranked candidates, actively avoiding skill overlap redundancy and
  explaining any swap decisions in plain language (e.g. "Candidate F
  replaces Candidate B because the team otherwise lacks MLOps coverage").
- Orchestrator: a class that owns full workflows (process_jd, compose_team,
  run_whatif, recalibrate_from_outcome) and decides which agents to invoke,
  in what order, and whether an agent call can be skipped because valid
  recent evidence already exists. All agent calls, tokens, and latency
  should be logged to the agent_calls table for observability.

PHASE 3 — Capability scoring logic
- Implement a confidence_scoring service that computes Capability Confidence
  as a function of skill score, evidence strength (how many/what type of
  evidence sources), recency (assessments/evidence decay after ~6 months),
  and production experience (client-delivered vs. simulated).
- Distinguish claimed vs demonstrated vs proven for every skill.
- Implement Readiness as three separate scores per engineer per opportunity:
  JD Match, Technical Capability (from Arena), Client Readiness (composite).
  For anything team/client-facing, aggregate into an "Engagement Capability
  Score" at the team level rather than exposing individual scores externally.

PHASE 4 — What-if simulation
- Single-JD: given required capabilities and size, compute current coverage,
  gaps, and projected coverage after N weeks of upskilling.
- Portfolio-level: accept multiple simultaneous JDs, compute combined
  capacity demand, flag capability clashes across JDs, recommend an
  upskilling vs. hiring mix, and project readiness dates per JD.

PHASE 5 — Outcome recalibration loop
- Add an endpoint to record post-deployment outcomes (client feedback score,
  delivery success boolean, issues reported).
- Implement a recalibration routine that compares predicted readiness scores
  against actual outcomes and adjusts scoring weights (start simple: a
  logged discrepancy report leadership can review; can evolve to automatic
  weight tuning later).

PHASE 6 — Frontend (Next.js)
- Build three role-based dashboards:
  1. Leadership: capability coverage %, skill gap alerts, future demand
     radar (trending skills across recent JDs), what-if simulator (both
     single-JD and portfolio), and the north-star metric
     "Capability-to-Deployment Velocity."
  2. Admin: JD upload → capability blueprint view → ranked candidate list
     with expandable evidence/explainability → team composer UI (natural
     language input box) → readiness summary before proposing to a client.
  3. Engineer: capability passport (skill bars + evidence: projects,
     certifications, assessments, client deployments) → matched
     opportunities list with match/readiness scores → Arena assessment
     as a chat-style adaptive interface → personalized learning path with
     projected readiness trajectory.
- Use shadcn/ui components, Recharts for skill radar/coverage charts, and a
  typed API client (lib/api.ts) against the FastAPI backend.

PHASE 7 — Observability panel (leadership-only)
- Simple table/chart view of agent_calls: which agent, which model, token
  usage, latency, and estimated cost per call, so the cost-aware model
  routing story is demonstrable live.

NON-FUNCTIONAL REQUIREMENTS THROUGHOUT
- Every AI-generated score must ship with a human-readable evidence trail
  (never a bare number).
- Admin/leadership can always override any AI recommendation; log overrides
  with a reason field for future learning-agent training data.
- Route simple extraction/triage tasks to gpt-4o-mini and complex
  reasoning/evaluation tasks to gpt-4o, logging the choice each time.
- Keep all AI prompts and parsing logic isolated inside the agents/ folder
  so models/prompts can be swapped without touching routers or frontend.

Start with Phase 1. Confirm the schema and seed data look right before
writing any agent logic.
```

---

**Suggested next step:** run Phase 1 in Claude Code against a fresh repo, verify the seed data and schema, then proceed phase by phase rather than generating the whole app in one shot — this keeps each agent testable in isolation before wiring it into the orchestrator.
