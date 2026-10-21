
from typing import Any

import pandas as pd

from intelligence.schemas import Insight


class InsightDetector:
    """Detect evidence-backed patterns in sales data."""

    @staticmethod
    def detect_product_concentration(
        products: pd.DataFrame,
    ) -> list[Insight]:
        if products.empty:
            return []

        required = {"item_name", "net_revenue_contribution"}
        if not required.issubset(products.columns):
            return []

        ranked = products.sort_values(
            "net_revenue_contribution",
            ascending=False,
        )

        top = ranked.iloc[0]
        share = float(top["net_revenue_contribution"])

        return [
            Insight(
                title="Leading product contribution",
                category="product",
                severity="info",
                summary=(
                    f"{top['item_name']} contributes "
                    f"{share:.2f}% of net product revenue."
                ),
                evidence=[
                    {
                        "metric": "Net revenue contribution",
                        "value": share,
                        "unit": "%",
                        "product": str(top["item_name"]),
                    }
                ],
                recommendation=(
                    "Review this product's historical performance "
                    "and contribution before making inventory "
                    "or sales decisions."
                ),
                confidence=1.0,
                dashboard="products",
            )
        ]

    @staticmethod
    def detect_customer_concentration(
        customers: pd.DataFrame,
    ) -> list[Insight]:
        if customers.empty:
            return []

        required = {"customer", "Revenue"}
        if not required.issubset(customers.columns):
            return []

        revenue = pd.to_numeric(
            customers["Revenue"],
            errors="coerce",
        ).fillna(0)

        total = float(revenue.sum())

        if total <= 0:
            return []

        top_customers = customers.loc[
            revenue.nlargest(min(10, len(revenue))).index
        ]

        top_revenue = float(
            pd.to_numeric(
                top_customers["Revenue"],
                errors="coerce",
            ).fillna(0).sum()
        )

        share = top_revenue / total * 100

        return [
            Insight(
                title="Top customer revenue share",
                category="customer",
                severity="info",
                summary=(
                    f"The top {len(top_customers)} customers "
                    f"account for {share:.2f}% of customer revenue."
                ),
                evidence=[
                    {
                        "metric": "Top customer revenue share",
                        "value": round(share, 2),
                        "unit": "%",
                        "customers_count": len(top_customers),
                    }
                ],
                recommendation=(
                    "Review these customers' purchase histories "
                    "and assess how changes in their activity "
                    "could affect revenue."
                ),
                confidence=1.0,
                dashboard="customers",
            )
        ]