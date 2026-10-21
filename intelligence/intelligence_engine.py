
from typing import Any

from engines.customer_engine import CustomerEngine
from engines.kpi_engine import KPIEngine
from engines.product_engine import ProductEngine
from intelligence.insight_detector import InsightDetector


class IntelligenceEngine:
    """Coordinate existing engines and generate business insights."""

    def get_executive_insights(self) -> dict[str, Any]:
        kpi_engine = KPIEngine()
        product_engine = ProductEngine()
        customer_engine = CustomerEngine()

        try:
            kpis = kpi_engine.dashboard_summary()

            insights = [
                *InsightDetector.detect_product_concentration(
                    product_engine.product_contribution
                ),
                *InsightDetector.detect_customer_concentration(
                    customer_engine.customer_summary()
                ),
            ]

            insights.sort(
                key=lambda insight: (
                    insight.severity != "critical",
                    insight.severity != "warning",
                    insight.title,
                )
            )

            return {
                "kpis": kpis,
                "insights": [
                    insight.to_dict()
                    for insight in insights[:4]
                ],
                "status": "success",
            }
        finally:
            kpi_engine.close()
            product_engine.close()