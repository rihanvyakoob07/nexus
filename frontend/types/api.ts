export type Role = "leadership" | "admin" | "engineer";

export type Skill = { id: number; name: string; category?: string | null };
export type EngineerSkill = { skill_id: number; skill: Skill; claimed_score: number; confidence_score: number; source: string; last_updated: string };
export type Evidence = { id: number; skill_id: number; type: string; description?: string | null; date?: string | null };
export type Certification = { id: number; name: string; issuer?: string | null; date?: string | null; expiry?: string | null };
export type Engineer = { id: number; name: string; email: string; role: Role; seniority?: string | null; bio?: string | null; created_at: string };
export type EngineerPassport = Engineer & { skills: EngineerSkill[]; evidence: Evidence[]; certifications: Certification[] };

export type CapabilityCoverage = { skill_name: string; category: string; coverage_pct: number; avg_confidence: number; engineer_count: number };
export type GapAlert = { skill_name: string; severity: string; affected_jds: number; engineer_gap_count: number };
export type DemandRadarItem = { skill_name: string; demand_count: number; avg_priority_weight: number };
export type LeadershipDashboard = { capability_coverage: CapabilityCoverage[]; gap_alerts: GapAlert[]; demand_radar: DemandRadarItem[]; total_engineers: number; total_jds: number; deployment_velocity: number; agent_cost_last_30d: number };
export type AdminDashboard = { open_jds: number; recent_matches: Array<{ engineer: string; jd: string; score: number }>; pending_assessments: number; teams_composed: number };
export type EngineerDashboard = { engineer_id: number; readiness_score: number; evidence_confidence: number; assessment_score?: number | null; critical_gaps: number; overall_capability_score: number; matched_opportunities: Array<{ jd_id: number; client: string; match_score: number; explanation?: string | null }>; active_gaps: number; learning_path_status?: string | null; projected_readiness_date?: string | null };
export type ObservabilityRow = { agent_name: string; model_used: string; input_tokens: number; output_tokens: number; latency_ms: number; cost_estimate: number; timestamp: string };
export type ObservabilityDashboard = { rows: ObservabilityRow[]; total_cost: number; total_calls: number; avg_latency_ms: number };

export type JD = { id: number; client_name: string; raw_text: string; capability_blueprint?: Record<string, unknown> | null; created_at: string; updated_at?: string | null; status?: string; posted_by?: number | null; is_published?: boolean; location?: string | null; employment_type?: string | null };
export type Match = { engineer_id: number; engineer_name: string; jd_match_score: number; breakdown?: Record<string, unknown> | null; explanation?: string | null };
export type JDMatches = { jd_id: number; client_name: string; candidates: Match[] };
export type SkillGap = { skill_id: number; skill_name: string; severity: string; current_score: number; target_score: number };

export type AssessmentTurn = { turn_index: number; question: string; answer?: string | null; ai_evaluation?: Record<string, unknown> | null };
export type Assessment = { id: number; engineer_id: number; jd_id: number; status: string; started_at?: string | null; completed_at?: string | null; turns: AssessmentTurn[] };
export type AssessmentScore = { skill_id: number; skill_name: string; score: number; confidence: number };
export type AssessmentResult = { assessment_id: number; status: string; scores: AssessmentScore[]; overall_score: number; readiness_level: string; summary: string };
export type NextQuestion = { assessment_id: number; turn_index: number; question: string; is_final: boolean };

export type LearningPath = { learning_path_id: number; plan: Record<string, unknown>; projected_readiness_date?: string | null; projected_readiness_score?: number | null };
export type TeamMember = { engineer_id: number; engineer_name: string; role: string; rationale: string; capability_score: number };
export type TeamResult = { team_id?: number; jd_id: number; composition: TeamMember[]; team_capability_score: number; engagement_capability_score: number; risk_level: string; swap_explanations?: string[] };
export type WhatIfResult = { jd_id: number; current_coverage_pct: number; gap_skills: Array<Record<string, unknown>>; projected_coverage_pct: number; upskilling_recommendation: string; readiness_date?: string | null };
export type Deployment = { id: number; engineer_id: number; jd_id: number; team_id?: number | null; start_date?: string | null; end_date?: string | null; predicted_readiness_score?: number | null; outcome?: Outcome | null };
export type Outcome = { id: number; deployment_id: number; client_feedback_score?: number | null; delivery_success: boolean; issues_reported: string[]; recorded_at: string };
export type Resume = { id: number; engineer_id: number; filename: string; parsed_data?: Record<string, unknown> | null; ats_score?: number | null; ats_breakdown?: Record<string, unknown> | null; status: string; is_active: boolean; uploaded_at: string; updated_at: string };
export type ATSResult = { resume_id: number; ats_score: number; breakdown: Record<string, number>; strengths: string[]; weaknesses: string[]; recommendations: string[] };
export type Opportunity = JD & { status: string; location?: string | null; employment_type?: string | null; application_status?: string | null; match_score?: number | null };
export type Application = { id: number; jd_id: number; engineer_id: number; resume_id?: number | null; status: string; cover_note?: string | null; match_score_snapshot?: number | null; applied_at: string; updated_at: string; reviewed_at?: string | null; admin_notes?: string | null; client_name?: string; raw_text?: string; capability_blueprint?: Record<string, unknown> | null; engineer_name?: string };
export type AdminAssessment = { id: number; engineer_id: number; engineer_name: string; jd_id: number; client_name: string; application_id?: number | null; status: string; started_at?: string | null; completed_at?: string | null; overall_score?: number | null; readiness_score?: number | null; summary?: string | null };
export type AdminTeam = { id: number; jd_id: number; client_name: string; composition: Array<Record<string, unknown>>; team_capability_score?: number | null; engagement_capability_score?: number | null; risk_level: string; created_at: string };
export type LeadershipAnalytics = { assessment_count: number; completed_assessments: number; assessment_completion_rate: number; average_readiness: number; deployment_count: number };
export type DemandResponse = { demand_radar: DemandRadarItem[]; opportunities: Array<{ id: number; client_name: string; status: string; capability_blueprint?: Record<string, unknown> | null }> };
