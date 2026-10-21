
from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class Insight:
    title: str
    category: str
    severity: str
    summary: str
    evidence: list[dict[str, Any]]
    recommendation: str
    confidence: float
    dashboard: str = "overview"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)