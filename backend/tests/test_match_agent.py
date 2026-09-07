from app.agents.match_agent import _deterministic_score, _flatten_requirements


def test_match_uses_all_engineer_skills_not_top_three():
    blueprint = {
        "categories": {
            "core": [
                {"skill": "Python", "weight": 0.5, "priority": "high"},
                {"skill": "MLOps", "weight": 1.0, "priority": "critical"},
            ]
        }
    }
    engineer = {
        "id": 7,
        "skills": [
            {"skill_name": "Python", "confidence_score": 9, "source": "proven"},
            {"skill_name": "FastAPI", "confidence_score": 9, "source": "proven"},
            {"skill_name": "React", "confidence_score": 9, "source": "proven"},
            {"skill_name": "MLOps", "confidence_score": 8, "source": "demonstrated"},
        ],
    }

    result = _deterministic_score(engineer, _flatten_requirements(blueprint))

    assert result["overall_score"] > 0
    assert "MLOps" in result["_matched"]
    assert result["_gaps"] == []


def test_critical_requirements_are_weighted_more_heavily():
    requirements = [
        {"skill": "Python", "weight": 1.0, "priority": "medium"},
        {"skill": "Security", "weight": 1.0, "priority": "critical"},
    ]
    engineer = {
        "id": 1,
        "skills": [
            {"skill_name": "Python", "confidence_score": 10},
            {"skill_name": "Security", "confidence_score": 0},
        ],
    }

    result = _deterministic_score(engineer, requirements)

    assert result["overall_score"] < 5
    assert "Security" in result["_gaps"]
