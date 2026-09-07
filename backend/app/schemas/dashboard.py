from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class CapabilityCoverageItem(BaseModel):
    skill_name: str
    category: str
    coverage_pct: float
    avg_confidence: float
    engineer_count: int


class GapAlert(BaseModel):
    skill_name: str
    severity: str
    affected_jds: int
    engineer_gap_count: int


class DemandRadarItem(BaseModel):
    skill_name: str
    demand_count: int
    avg_priority_weight: float


class LeadershipDashboard(BaseModel):
    capability_coverage: List[CapabilityCoverageItem]
    gap_alerts: List[GapAlert]
    demand_radar: List[DemandRadarItem]
    total_engineers: int
    total_jds: int
    deployment_velocity: float
    agent_cost_last_30d: float


class AdminDashboard(BaseModel):
    open_jds: int
    recent_matches: List[Dict[str, Any]]
    pending_assessments: int
    teams_composed: int


class EngineerDashboard(BaseModel):
    engineer_id: int
    readiness_score: float
    evidence_confidence: float
    assessment_score: Optional[float] = None
    critical_gaps: int = 0
    overall_capability_score: float
    matched_opportunities: List[Dict[str, Any]]
    active_gaps: int
    learning_path_status: Optional[str] = None
    projected_readiness_date: Optional[str] = None


class ObservabilityRow(BaseModel):
    agent_name: str
    model_used: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    cost_estimate: float
    timestamp: str


class ObservabilityDashboard(BaseModel):
    rows: List[ObservabilityRow]
    total_cost: float
    total_calls: int
    avg_latency_ms: float
