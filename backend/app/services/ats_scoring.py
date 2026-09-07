from typing import Any, Dict


def score_resume(parsed: Dict[str, Any], raw_text: str) -> Dict[str, Any]:
    text = raw_text.lower()
    skills = parsed.get("skills") or []
    projects = parsed.get("projects") or []
    certifications = parsed.get("certifications") or []
    technologies = parsed.get("technologies") or []
    dimensions = {
        "skill_coverage": min(100, 35 + len(skills) * 6),
        "experience_relevance": min(100, 35 + (20 if parsed.get("years_experience") else 0) + len(parsed.get("client_experience") or []) * 10),
        "project_evidence": min(100, 35 + len(projects) * 15),
        "technology_alignment": min(100, 35 + len(technologies) * 7),
        "seniority_alignment": 80 if parsed.get("seniority") else 45,
        "certifications": min(100, 35 + len(certifications) * 20),
        "resume_completeness": min(100, 25 + sum(bool(parsed.get(field)) for field in ("name", "email", "summary", "skills", "projects", "education")) * 12),
    }
    if "production" in text or "client" in text or "deployed" in text:
        dimensions["experience_relevance"] = min(100, dimensions["experience_relevance"] + 10)
    score = round(sum(dimensions.values()) / len(dimensions), 1)
    strengths = [name.replace("_", " ").title() for name, value in dimensions.items() if value >= 75]
    weaknesses = [name.replace("_", " ").title() for name, value in dimensions.items() if value < 60]
    recommendations = [f"Add measurable evidence for {item.lower()}." for item in weaknesses]
    if not recommendations:
        recommendations.append("Keep project outcomes and technology versions current.")
    return {"ats_score": score, "breakdown": dimensions, "strengths": strengths, "weaknesses": weaknesses, "recommendations": recommendations}
