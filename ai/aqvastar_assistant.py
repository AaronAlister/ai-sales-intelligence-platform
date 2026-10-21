"""Data-grounded question answering for the AQVASTAR sales dashboard."""

from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd
from dotenv import load_dotenv


DB_PATH = Path("data/sales.db")
DEFAULT_MODEL = "gemini-2.5-flash"


def _fetch_dataframe(
    query: str,
    params: tuple[Any, ...] = (),
) -> pd.DataFrame:
    """Run a read-only analytical query against the local sales database."""
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Sales database was not found at {DB_PATH.as_posix()}."
        )

    connection = sqlite3.connect(
        f"file:{DB_PATH.as_posix()}?mode=ro",
        uri=True,
    )
    try:
        return pd.read_sql_query(query, connection, params=params)
    finally:
        connection.close()


def _monthly_summary() -> pd.DataFrame:
    """Return the two latest months available in the database."""
    return _fetch_dataframe(
        """
        SELECT
            strftime('%Y-%m', posting_date) AS month,
            ROUND(SUM(amount), 2) AS net_sales,
            ROUND(SUM(stock_qty), 2) AS net_quantity,
            COUNT(DISTINCT invoice) AS orders
        FROM sales
        WHERE posting_date IS NOT NULL
        GROUP BY strftime('%Y-%m', posting_date)
        ORDER BY month DESC
        LIMIT 2
        """
    ).sort_values("month")


def _collect_evidence(question: str) -> dict[str, Any]:
    """Calculate relevant evidence locally before sending summaries to Gemini."""
    lowered = question.casefold()
    monthly = _monthly_summary()

    snapshot_df = _fetch_dataframe(
        """
        SELECT
            ROUND(COALESCE(SUM(
                CASE WHEN amount > 0 THEN amount ELSE 0 END
            ), 0), 2) AS gross_sales,
            ROUND(COALESCE(SUM(
                CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END
            ), 0), 2) AS returns_value,
            ROUND(COALESCE(SUM(amount), 0), 2) AS net_sales,
            COUNT(DISTINCT invoice) AS orders,
            COUNT(DISTINCT item_code) AS products,
            COUNT(DISTINCT customer) AS customers
        FROM sales
        """
    )
    snapshot = snapshot_df.iloc[0].to_dict() if not snapshot_df.empty else {}

    evidence: dict[str, Any] = {
        "question": question,
        "analysis_type": "sales_overview",
        "snapshot": snapshot,
        "monthly_comparison": monthly.to_dict(orient="records"),
        "data_notes": [
            "Revenue is calculated from the amount column, including "
            "negative return values.",
            "The latest month in the dataset may be incomplete.",
            "These are descriptive comparisons and do not establish causation.",
        ],
    }
    display_evidence: dict[str, Any] = {}

    if any(
        term in lowered
        for term in ("product", "item", "best selling", "top seller")
    ):
        products = _fetch_dataframe(
            """
            SELECT
                item_name AS product,
                ROUND(SUM(amount), 2) AS net_revenue,
                ROUND(SUM(stock_qty), 2) AS net_quantity,
                COUNT(DISTINCT invoice) AS orders
            FROM sales
            WHERE item_name IS NOT NULL
              AND TRIM(item_name) != ''
            GROUP BY item_name
            ORDER BY net_revenue DESC
            LIMIT 10
            """
        )
        evidence["analysis_type"] = "top_products"
        evidence["top_products"] = products.to_dict(orient="records")
        display_evidence = {
            "title": "Top products by net revenue",
            "table": products,
        }

    elif any(
        term in lowered
        for term in (
            "customer",
            "client",
            "reduced their purchases",
            "reduced purchase",
            "declin",
        )
    ):
        if len(monthly) < 2:
            customers = pd.DataFrame()
            evidence["analysis_type"] = "customer_decline"
            evidence["customer_decline_summary"] = {
                "status": "insufficient_months",
                "message": (
                    "At least two months of sales data are needed "
                    "to compare customer purchases."
                ),
            }
        else:
            previous_month = str(monthly.iloc[-2]["month"])
            latest_month = str(monthly.iloc[-1]["month"])

            customers = _fetch_dataframe(
                """
                SELECT
                    customer,
                    ROUND(SUM(
                        CASE
                            WHEN strftime('%Y-%m', posting_date) = ?
                            THEN amount ELSE 0
                        END
                    ), 2) AS latest_month_sales,
                    ROUND(SUM(
                        CASE
                            WHEN strftime('%Y-%m', posting_date) = ?
                            THEN amount ELSE 0
                        END
                    ), 2) AS previous_month_sales
                FROM sales
                WHERE strftime('%Y-%m', posting_date) IN (?, ?)
                  AND customer IS NOT NULL
                  AND TRIM(customer) != ''
                GROUP BY customer
                HAVING previous_month_sales > latest_month_sales
                ORDER BY (
                    previous_month_sales - latest_month_sales
                ) DESC
                LIMIT 10
                """,
                (
                    latest_month,
                    previous_month,
                    latest_month,
                    previous_month,
                ),
            )

            if not customers.empty:
                customers["revenue_change"] = (
                    customers["latest_month_sales"]
                    - customers["previous_month_sales"]
                ).round(2)

                customers["change_percent"] = customers.apply(
                    lambda row: round(
                        row["revenue_change"]
                        / abs(row["previous_month_sales"])
                        * 100,
                        2,
                    )
                    if row["previous_month_sales"]
                    else None,
                    axis=1,
                )

            evidence["analysis_type"] = "customer_decline"
            evidence["customer_decline_summary"] = {
                "comparison_months": [
                    previous_month,
                    latest_month,
                ],
                "customers_with_lower_sales_in_top_10": int(
                    len(customers)
                ),
                "top_decline_amounts": (
                    [
                        round(float(value), 2)
                        for value in customers["revenue_change"].tolist()
                    ]
                    if not customers.empty
                    else []
                ),
                "note": (
                    "Customer names are deliberately excluded "
                    "from the prompt sent to Gemini."
                ),
            }

        display_evidence = {
            "title": "Customers with lower sales in the latest month",
            "table": customers,
        }

    elif any(
        term in lowered
        for term in (
            "discount",
            "pricing",
            "price realization",
            "price",
        )
    ):
        pricing = _fetch_dataframe(
            """
            SELECT
                ROUND(AVG(discount_percent), 2)
                    AS average_discount_percent,
                COUNT(*) AS valid_rows,
                ROUND(AVG(stock_qty), 2)
                    AS average_quantity_per_row,
                ROUND(AVG(amount), 2)
                    AS average_amount_per_row
            FROM sales
            WHERE discount_percent BETWEEN 0 AND 100
              AND stock_qty > 0
              AND amount > 0
            """
        )

        correlation_data = _fetch_dataframe(
            """
            SELECT discount_percent, stock_qty, amount
            FROM sales
            WHERE discount_percent BETWEEN 0 AND 100
              AND stock_qty > 0
              AND amount > 0
            """
        )

        correlation = None
        if len(correlation_data) >= 2:
            calculated = correlation_data["discount_percent"].corr(
                correlation_data["stock_qty"]
            )
            if pd.notna(calculated):
                correlation = round(float(calculated), 4)

        bands = _fetch_dataframe(
            """
            SELECT
                CASE
                    WHEN discount_percent < 10 THEN '0-9.99%'
                    WHEN discount_percent < 20 THEN '10-19.99%'
                    WHEN discount_percent < 30 THEN '20-29.99%'
                    WHEN discount_percent < 40 THEN '30-39.99%'
                    ELSE '40-100%'
                END AS discount_band,
                COUNT(*) AS rows,
                ROUND(SUM(amount), 2) AS net_revenue,
                ROUND(SUM(stock_qty), 2) AS net_quantity
            FROM sales
            WHERE discount_percent BETWEEN 0 AND 100
              AND amount > 0
              AND stock_qty > 0
            GROUP BY discount_band
            ORDER BY MIN(discount_percent)
            """
        )

        evidence["analysis_type"] = "discount_analysis"
        evidence["discount_summary"] = {
            **(
                pricing.iloc[0].to_dict()
                if not pricing.empty
                else {}
            ),
            "discount_quantity_correlation": correlation,
            "interpretation_note": (
                "Correlation is descriptive and does not show "
                "that discounts cause quantity changes."
            ),
        }
        evidence["discount_bands"] = bands.to_dict(orient="records")
        display_evidence = {
            "title": "Sales by discount band",
            "table": bands,
        }

    elif any(
        term in lowered
        for term in ("forecast", "predict", "next month", "future")
    ):
        evidence["data_notes"].append(
            "This first version reports historical evidence only; "
            "it does not generate a forecast."
        )

    return {
        "prompt_evidence": evidence,
        "display_evidence": display_evidence,
    }


def _json_safe(value: Any) -> Any:
    """Convert pandas/numpy values and missing values to JSON-safe types."""
    if isinstance(value, dict):
        return {
            str(key): _json_safe(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [_json_safe(item) for item in value]

    if value is None:
        return None

    if hasattr(value, "item"):
        value = value.item()

    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    return value


def _build_prompt(
    question: str,
    evidence: dict[str, Any],
) -> str:
    """Build a prompt that restricts Gemini to verified evidence."""
    safe_evidence = _json_safe(evidence)

    return f"""You are AQVASTAR, a sales intelligence assistant for business users.

Answer the user's question using only the verified data in the JSON evidence below.

Rules:
- Do not invent numbers, entities, time periods, or explanations.
- Distinguish observations from possible explanations.
- Do not claim causation from correlation.
- If the data is insufficient, say so clearly and state what additional data is needed.
- Compare the actual months shown in the evidence.
- Mention if the latest month may be incomplete.
- Use concise, professional language and short headings or bullets when useful.
- Mention key figures that directly support the answer.
- Do not reveal or infer customer identities.
- Customer names are not included in the evidence sent to you.
- End with one practical next step to investigate, if supported by the data.
- All monetary amounts must be displayed in Indian Rupees (₹).
- Format monetary amounts using the Indian numbering system,
  such as ₹7,04,82,714.06.
- Never display monetary amounts without a currency symbol.
- Use ₹ for currency and INR when the symbol cannot be displayed.
- Do not convert, round, or change the underlying monetary values
  unless the user explicitly requests it.
- Do not apply currency formatting to quantities, order counts,
  percentages, or other non-monetary metrics.

User question:
{question}

Verified analytical evidence (JSON):
{json.dumps(safe_evidence, ensure_ascii=False, default=str, allow_nan=False)}
"""


def answer_question(question: str) -> dict[str, Any]:
    """Answer a question using local analytics and Gemini for explanation."""
    clean_question = question.strip()
    if not clean_question:
        raise ValueError("Enter a question before asking AQVASTAR.")

    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is missing. Add it to the .env file "
            "in the project root."
        )

    collected = _collect_evidence(clean_question)

    try:
        from google import genai
    except ImportError as exc:
        raise RuntimeError(
            "The Gemini SDK is not installed. Run: "
            "pip install google-genai python-dotenv"
        ) from exc

    client = genai.Client(api_key=api_key)
    model = os.getenv("GEMINI_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL

    response = None
    last_error = None

    models_to_try = list(dict.fromkeys([
        model,
        "gemini-3.5-flash",
        "gemini-3.1-flash-lite",
    ]))

    for candidate_model in models_to_try:
        print(
            f"[AQVASTAR] Calling Gemini model: "
            f"{candidate_model!r}",
            flush=True,
        )

        try:
            response = client.models.generate_content(
                model=candidate_model,
                contents=_build_prompt(
                    clean_question,
                    collected["prompt_evidence"],
                ),
            )

            print(
                f"[AQVASTAR] Successfully used "
                f"{candidate_model!r}",
                flush=True,
            )
            break

        except Exception as exc:
            last_error = exc

            print(
                f"[AQVASTAR] {candidate_model!r} failed: "
                f"{type(exc).__name__}: {exc}",
                flush=True,
            )

            error_message = str(exc).upper()

            # Switch models only for temporary unavailability.
            if "503" not in error_message and "UNAVAILABLE" not in error_message:
                raise

    if response is None:
        raise RuntimeError(
            "AQVASTAR could not reach any configured Gemini "
            "model because of service unavailability. "
            "Please try again later."
        ) from last_error

    answer = (response.text or "").strip()
    if not answer:
        raise RuntimeError(
            "Gemini returned an empty response. Please try again."
        )

    return {
        "question": clean_question,
        "answer": answer,
        "analysis_type": collected["prompt_evidence"].get(
            "analysis_type",
            "sales_overview",
        ),
        "display_evidence": collected["display_evidence"],
        "data_notes": collected["prompt_evidence"].get(
            "data_notes",
            [],
        ),
    }