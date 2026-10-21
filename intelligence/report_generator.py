"""Export intelligence findings into a compact CSV report."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


def export_insights(results: dict[str, Any], output_path: str = "reports/intelligence_insights.csv") -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for item in results.get("insights", []):
        rows.append({
            "Category": item.get("category", ""),
            "Title": item.get("title", ""),
            "Evidence": str(item.get("evidence", {})),
            "Suggested Action": item.get("action", ""),
        })
    pd.DataFrame(rows, columns=["Category", "Title", "Evidence", "Suggested Action"]).to_csv(output, index=False)
    return output
