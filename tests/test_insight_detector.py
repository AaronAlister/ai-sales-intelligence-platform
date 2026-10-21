
import pandas as pd

from intelligence.insight_detector import InsightDetector


def test_product_concentration() -> None:
    products = pd.DataFrame(
        {
            "item_name": ["Product A", "Product B", "Product C"],
            "net_revenue_contribution": [600, 300, 100],
        }
    )

    insights = InsightDetector.detect_product_concentration(products)

    assert len(insights) == 1
    assert insights[0].category
    assert "Product A" in insights[0].summary
    assert insights[0].evidence
    assert 0 <= insights[0].confidence <= 1


def test_customer_concentration() -> None:
    customers = pd.DataFrame(
        {
            "customer": [f"Customer {i}" for i in range(1, 13)],
            "Revenue": list(range(1, 13)),
        }
    )

    insights = InsightDetector.detect_customer_concentration(customers)

    assert len(insights) == 1
    assert insights[0].category
    assert insights[0].evidence
    assert 0 <= insights[0].confidence <= 1


def test_empty_product_data() -> None:
    products = pd.DataFrame(
        columns=["item_name", "net_revenue_contribution"]
    )

    insights = InsightDetector.detect_product_concentration(products)

    assert insights == []


def test_empty_customer_data() -> None:
    customers = pd.DataFrame(columns=["customer", "Revenue"])

    insights = InsightDetector.detect_customer_concentration(customers)

    assert insights == []


def test_missing_product_columns() -> None:
    products = pd.DataFrame({"item_name": ["Product A"]})

    insights = InsightDetector.detect_product_concentration(products)

    assert insights == []


def test_missing_customer_columns() -> None:
    customers = pd.DataFrame({"customer": ["Customer A"]})

    insights = InsightDetector.detect_customer_concentration(customers)

    assert insights == []