
from intelligence.intelligence_engine import IntelligenceEngine


def test_executive_insights_structure() -> None:
    result = IntelligenceEngine().get_executive_insights()

    assert result["status"] == "success"
    assert isinstance(result["kpis"], dict)
    assert isinstance(result["insights"], list)
    assert len(result["insights"]) <= 4

    for insight in result["insights"]:
        assert insight["title"]
        assert insight["summary"]
        assert isinstance(insight["evidence"], list)
        assert 0 <= insight["confidence"] <= 1