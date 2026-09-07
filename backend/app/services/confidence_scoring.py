"""
Computes Capability Confidence = f(skill_score, evidence_strength, recency, production_experience).
Higher is better (0–10 scale).
"""
from datetime import datetime, timezone
from typing import List


_SOURCE_WEIGHTS = {"claimed": 0.4, "demonstrated": 0.7, "proven": 1.0}
_EVIDENCE_WEIGHTS = {
    "client_delivery": 1.0,
    "assessment": 0.7,
    "project": 0.6,
    "certification": 0.5,
}
_DECAY_MONTHS = 6  # evidence older than this decays linearly


def _recency_factor(date: datetime | None) -> float:
    if date is None:
        return 0.5
    now = datetime.now(timezone.utc)
    if date.tzinfo is None:
        date = date.replace(tzinfo=timezone.utc)
    months_old = (now - date).days / 30
    if months_old <= _DECAY_MONTHS:
        return 1.0
    return max(0.3, 1.0 - (months_old - _DECAY_MONTHS) / (_DECAY_MONTHS * 2))


def _evidence_strength(evidence_list: list) -> float:
    """Returns 0–1 from list of Evidence ORM objects."""
    if not evidence_list:
        return 0.0
    score = 0.0
    for ev in evidence_list:
        weight = _EVIDENCE_WEIGHTS.get(ev.type, 0.4)
        recency = _recency_factor(ev.date)
        score += weight * recency
    return min(1.0, score / max(1, len(evidence_list)) * 2)


def compute_confidence(
    claimed_score: float,
    source: str,
    evidence_list: list,
) -> float:
    source_w = _SOURCE_WEIGHTS.get(source, 0.4)
    ev_strength = _evidence_strength(evidence_list)
    # Weighted blend: base score × source credibility × evidence strength
    raw = (claimed_score / 10.0) * source_w * (0.5 + 0.5 * ev_strength)
    return round(raw * 10, 2)  # back to 0–10 scale


def compute_readiness(jd_match: float, technical_score: float, confidence_avg: float) -> dict:
    """Returns three readiness scores and a composite."""
    client_readiness = (jd_match * 0.4 + technical_score * 0.4 + confidence_avg * 0.2)
    level = (
        "highly_ready" if client_readiness >= 8
        else "ready" if client_readiness >= 6
        else "developing" if client_readiness >= 4
        else "not_ready"
    )
    return {
        "jd_match": round(jd_match, 2),
        "technical_capability": round(technical_score, 2),
        "client_readiness": round(client_readiness, 2),
        "readiness_level": level,
    }


def compute_engagement_capability_score(member_scores: List[float]) -> float:
    """Team-level aggregate — geometric mean to penalise weak links."""
    import math
    if not member_scores:
        return 0.0
    product = math.prod(max(s, 0.1) for s in member_scores)
    return round(product ** (1 / len(member_scores)), 2)
