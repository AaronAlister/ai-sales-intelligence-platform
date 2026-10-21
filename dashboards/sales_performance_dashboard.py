"""
AQVASTAR Sales Intelligence Platform.

Sales Performance dashboard rendered from the Home page.

This module is dashboard orchestration only. Existing analytics engines
remain responsible for business logic; this file composes their outputs
into the executive Sales Performance view.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from collections.abc import Callable
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from dashboards.components.navigation import (
    render_brand,
    render_navigation,
)
from dashboards.components.theme import (
    AQUA,
    DEEP_OCEAN,
    OCEAN,
    apply_theme,
)
from engines.regional_engine import RegionalEngine
from engines.forecast_engine import TimeSeriesEngine


# ============================================================
# DESIGN SYSTEM
# ============================================================

BACKGROUND = "#F3F8FA"
WHITE = "#FFFFFF"
TEXT = "#102631"
MUTED = "#617982"
BORDER = "#D9E8EC"

DEEP_OCEAN = "#063D4A"
OCEAN = "#075D6D"
AQUA = "#11AFC1"
AQUA_LIGHT = "#CDEFF2"
AQUA_SOFT = "#E8F7F9"

AXIS_LIGHT = "#D8F5F7"
GRID_DARK = "rgba(216,245,247,0.55)"

SHADOW = "0 12px 32px rgba(5, 57, 70, 0.08)"


# ============================================================
# FORMATTING
# ============================================================

def format_currency(value: float) -> str:
    """Format Indian currency using compact business notation."""

    numeric_value = float(value)
    absolute_value = abs(numeric_value)
    sign = "-" if numeric_value < 0 else ""

    if absolute_value >= 1_000_000_000:
        return f"{sign}₹{absolute_value / 1_000_000_000:.2f}B"

    if absolute_value >= 1_000_000:
        return f"{sign}₹{absolute_value / 1_000_000:.2f}M"

    if absolute_value >= 1_000:
        return f"{sign}₹{absolute_value / 1_000:.2f}K"

    return f"{sign}₹{absolute_value:,.0f}"


def format_number(value: float) -> str:
    """Format counts and quantities."""

    numeric_value = float(value)

    if numeric_value.is_integer():
        return f"{int(numeric_value):,}"

    return f"{numeric_value:,.1f}"


def safe_float(
    value: object,
    default: float = 0.0,
) -> float:
    """Convert a value to float safely."""

    try:
        numeric_value = float(value)  # type: ignore[arg-type]

        if pd.isna(numeric_value):
            return default

        return numeric_value

    except (TypeError, ValueError):
        return default


# ============================================================
# DATA
# ============================================================

def _get_sales_dataframe(
    db_path: str = "data/sales.db",
) -> pd.DataFrame:
    """Load the sales fact data required by the dashboard."""

    database_path = Path(db_path)

    if not database_path.exists():
        return pd.DataFrame()

    query = """
        SELECT
            invoice,
            item_name,
            item_group,
            customer,
            place_of_supply,
            posting_date,
            stock_qty,
            amount,
            transaction_type
        FROM sales
    """

    try:
        with sqlite3.connect(database_path) as connection:
            dataframe = pd.read_sql_query(
                query,
                connection,
            )
    except sqlite3.Error:
        return pd.DataFrame()

    if dataframe.empty:
        return dataframe

    dataframe["posting_date"] = pd.to_datetime(
        dataframe["posting_date"],
        errors="coerce",
    )

    for column in ("stock_qty", "amount"):
        dataframe[column] = pd.to_numeric(
            dataframe[column],
            errors="coerce",
        ).fillna(0.0)

    dataframe["transaction_type"] = (
        dataframe["transaction_type"]
        .astype("string")
        .str.strip()
        .str.title()
    )

    dataframe["item_group"] = (
        dataframe["item_group"]
        .astype("string")
        .str.strip()
    )

    dataframe["place_of_supply"] = (
        dataframe["place_of_supply"]
        .astype("string")
        .str.strip()
    )

    return dataframe


def _sales_only(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Return valid Sale transactions only."""

    if dataframe.empty:
        return dataframe.copy()

    return dataframe[
        dataframe["transaction_type"].eq("Sale")
    ].dropna(
        subset=["posting_date"],
    ).copy()


# ============================================================
# CSS
# ============================================================

def inject_sales_css() -> None:
    """Inject the Sales Performance visual system."""

    st.markdown(
        f"""
        <style>

        /* ==================================================
           APP
        ================================================== */

        .stApp {{
            background:
                radial-gradient(
                    circle at 100% 0%,
                    rgba(22, 174, 192, 0.045),
                    transparent 24%
                ),
                {BACKGROUND};

            color: {TEXT};
        }}

        [data-testid="stMainBlockContainer"] {{
            max-width: 1380px;
            padding-top: 0.55rem;
            padding-bottom: 2.5rem;
        }}

        [data-testid="stHeader"] {{
            background: transparent;
        }}

        div[data-testid="column"] {{
            min-width: 0;
        }}


        /* ==================================================
           FIXED BACK TO HOME
        ================================================== */

        .sales-floating-home {{
            position: fixed;
            left: 28px;
            bottom: 28px;
            z-index: 999999;

            display: inline-flex;
            align-items: center;
            gap: 10px;

            min-height: 50px;
            padding: 0 18px 0 10px;

            border: 1px solid #CFE3E7;
            border-radius: 16px;

            background: rgba(255, 255, 255, 0.98);
            color: #164B59 !important;

            box-shadow:
                0 12px 32px rgba(4, 62, 76, 0.18);

            text-decoration: none !important;

            font-size: 0.72rem;
            font-weight: 800;
            letter-spacing: 0.055em;

            transition:
                transform 160ms ease,
                box-shadow 160ms ease,
                border-color 160ms ease;

            backdrop-filter: blur(10px);
        }}

        .sales-floating-home:hover {{
            transform: translateY(-3px);

            border-color: {AQUA};

            box-shadow:
                0 16px 36px rgba(4, 62, 76, 0.22);

            color: #087C8A !important;
        }}

        .sales-floating-home-icon {{
            display: flex;
            align-items: center;
            justify-content: center;

            width: 32px;
            height: 32px;

            border-radius: 10px;

            background: {DEEP_OCEAN};
            color: #FFFFFF;

            font-size: 0.95rem;
            font-weight: 800;
            line-height: 1;
        }}

        .sales-floating-home-text {{
            white-space: nowrap;
        }}


        /* ==================================================
           HERO
        ================================================== */

        .sales-hero {{
            position: relative;
            overflow: hidden;

            min-height: 176px;

            padding: 2rem 2.25rem;
            margin: 0.35rem 0 0.85rem;

            border-radius: 20px;

            background:
                radial-gradient(
                    circle at 83% 30%,
                    rgba(50, 202, 215, 0.50),
                    transparent 28%
                ),
                linear-gradient(
                    115deg,
                    {DEEP_OCEAN} 0%,
                    {OCEAN} 58%,
                    #1597A6 100%
                );

            box-shadow:
                0 14px 34px rgba(5, 60, 74, 0.14);
        }}

        .sales-hero-content {{
            position: relative;
            z-index: 3;
            max-width: 760px;
        }}

        .sales-hero-eyebrow {{
            color: #3BD0D8;

            font-size: 0.60rem;
            font-weight: 800;

            letter-spacing: 0.18em;
            text-transform: uppercase;

            margin-bottom: 0.58rem;
        }}

        .sales-hero-title {{
            color: #FFFFFF;

            font-size: clamp(
                1.85rem,
                3.1vw,
                3rem
            );

            line-height: 1.02;
            font-weight: 800;

            letter-spacing: -0.045em;

            margin-bottom: 0.62rem;
        }}

        .sales-hero-description {{
            max-width: 620px;

            color: rgba(
                255,
                255,
                255,
                0.76
            );

            font-size: 0.76rem;
            line-height: 1.45;
        }}

        .sales-hero-asof {{
            position: absolute;

            right: 2.25rem;
            top: 2rem;

            z-index: 4;

            color: rgba(
                255,
                255,
                255,
                0.62
            );

            font-size: 0.65rem;
            line-height: 1.4;

            text-align: right;
        }}

        .sales-hero-asof strong {{
            display: block;

            color: #FFFFFF;

            font-size: 0.75rem;

            margin-top: 0.15rem;
        }}

        .sales-hero-ring {{
            position: absolute;

            border:
                1px solid
                rgba(255,255,255,0.13);

            border-radius: 50%;

            pointer-events: none;
        }}


        /* ==================================================
           SECTION CONTAINERS
        ================================================== */

        .st-key-sales_revenue_section,
        .st-key-sales_breakdown_section,
        .st-key-sales_insights_section {{
            position: relative;
            overflow: hidden;

            border-radius: 20px;

            margin-top: 1.05rem;
            margin-bottom: 1.45rem;

            padding: 1.25rem 1.35rem 2.05rem;
        }}

        .st-key-sales_revenue_section,
        .st-key-sales_insights_section {{
            background:
                linear-gradient(
                    145deg,
                    #064652 0%,
                    #0B6C79 100%
                );

            box-shadow:
                0 16px 38px
                rgba(5, 57, 70, 0.13);
        }}

        .st-key-sales_breakdown_section {{
            background:
                linear-gradient(
                    145deg,
                    #F7FCFD 0%,
                    #EAF7F9 100%
                );

            border: 1px solid #D8EAEE;

            box-shadow:
                0 12px 32px
                rgba(5, 57, 70, 0.07);
        }}


        /* ==================================================
           SECTION HEADING
        ================================================== */

        .sales-section-heading {{
            display: flex;
            align-items: flex-start;

            gap: 16px;

            margin-bottom: 1.15rem;
        }}

        .sales-section-icon {{
            display: flex;

            align-items: center;
            justify-content: center;

            flex: 0 0 auto;

            width: 52px;
            height: 52px;

            border-radius: 15px;

            background: #11AFC1;
            color: #FFFFFF;

            font-size: 1.1rem;
            font-weight: 800;

            box-shadow:
                0 8px 18px
                rgba(17, 175, 193, 0.22);
        }}

        .sales-section-eyebrow {{
            color: #0794A5;

            font-size: 0.60rem;
            font-weight: 800;

            letter-spacing: 0.18em;
            text-transform: uppercase;

            margin-bottom: 0.28rem;
        }}

        .sales-section-title {{
            color: {TEXT};

            font-size: 1.32rem;
            font-weight: 800;

            letter-spacing: -0.035em;

            line-height: 1.1;
        }}

        .sales-section-description {{
            color: {MUTED};

            font-size: 0.73rem;
            line-height: 1.45;

            margin-top: 0.32rem;
        }}

        .sales-section-heading.dark
        .sales-section-eyebrow {{
            color: #3BD0D8;
        }}

        .sales-section-heading.dark
        .sales-section-title {{
            color: #FFFFFF;
        }}

        .sales-section-heading.dark
        .sales-section-description {{
            color: rgba(
                255,
                255,
                255,
                0.70
            );
        }}


        /* ==================================================
           EXECUTIVE KPI
        ================================================== */

        .sales-executive-summary {{
            position: relative;
            overflow: hidden;
            margin: 0.85rem 0 1.15rem;
            padding: 0.15rem 0 0.05rem;
        }}

        .sales-executive-kicker {{
            color: #11899A;
            font-size: 0.64rem;
            font-weight: 800;
            letter-spacing: 0.16em;
            text-transform: uppercase;
            margin-bottom: 0.18rem;
        }}

        .sales-executive-title {{
            color: {TEXT};
            font-size: 1.32rem;
            line-height: 1.15;
            font-weight: 800;
            letter-spacing: -0.025em;
            margin-bottom: 0.18rem;
        }}

        .sales-executive-description {{
            color: {MUTED};
            font-size: 0.74rem;
            line-height: 1.4;
            margin-bottom: 0.68rem;
        }}

        .sales-kpi-strip {{
            display: grid;
            grid-template-columns: repeat(5, minmax(0, 1fr));
            gap: 0.65rem;
        }}

        .sales-kpi {{
            min-width: 0;
            padding: 0.78rem 0.82rem;
            border: 1px solid #D6E7EB;
            border-radius: 13px;
            background: #FFFFFF;
            box-shadow: 0 6px 18px rgba(7,63,76,0.045);
        }}

        .sales-kpi-label {{
            color: #198C9B;
            font-size: 0.57rem;
            font-weight: 800;
            letter-spacing: 0.10em;
            text-transform: uppercase;
        }}

        .sales-kpi-value {{
            color: {TEXT};
            font-size: 1.28rem;
            line-height: 1.05;
            font-weight: 800;
            letter-spacing: -0.025em;
            margin: 0.30rem 0 0.16rem;
        }}

        .sales-kpi-note {{
            color: {MUTED};
            font-size: 0.57rem;
            line-height: 1.3;
        }}

        /* ==================================================
           CHARTS
        ================================================== */

        .sales-chart-grid {{
            display: grid;

            grid-template-columns:
                1fr 1fr;

            gap: 18px;

            margin-bottom: 18px;
        }}

        .sales-chart-card {{
            min-width: 0;

            background: #FFFFFF;

            border:
                1px solid
                #E0EAED;

            border-radius: 18px;

            box-shadow:
                0 10px 28px
                rgba(5,57,70,0.06);

            overflow: hidden;
        }}

        .sales-chart-header {{
            display: flex;

            align-items: center;
            justify-content: space-between;

            min-height: 62px;

            padding:
                14px
                18px
                10px;

            border-bottom:
                1px solid
                #EDF2F3;
        }}

        .sales-chart-title {{
            color: {TEXT};

            font-size: 0.96rem;
            font-weight: 800;

            letter-spacing: -0.02em;
        }}

        .sales-chart-description {{
            color: #71878E;

            font-size: 0.67rem;

            margin-top: 3px;
        }}

        .sales-chart-badge {{
            padding:
                6px
                9px;

            border-radius: 8px;

            background: #E8F7F9;

            color: #087C8A;

            font-size: 0.61rem;
            font-weight: 800;
        }}


        /* ==================================================
           INSIGHTS
        ================================================== */

        .sales-insight {{
            display: flex;

            align-items: center;

            gap: 12px;

            min-height: 56px;

            margin:
                0
                0
                18px;

            padding:
                10px
                14px;

            border:
                1px solid
                #CFE7EB;

            border-radius: 14px;

            background:
                linear-gradient(
                    120deg,
                    #F5FBFC 0%,
                    #EAF7F9 100%
                );

            color: #52727B;

            font-size: 0.70rem;
            line-height: 1.45;
        }}

        .sales-insight-icon {{
            display: flex;

            align-items: center;
            justify-content: center;

            flex: 0 0 auto;

            width: 32px;
            height: 32px;

            border-radius: 50%;

            background: #11AFC1;

            color: #FFFFFF;

            font-size: 0.9rem;
            font-weight: 800;
        }}

        .sales-insight-label {{
            color: #087C8A;

            font-size: 0.61rem;
            font-weight: 800;

            letter-spacing: 0.13em;
            text-transform: uppercase;

            margin-bottom: 2px;
        }}

        .sales-insight-value {{
            color: #0A9AAA;
            font-weight: 800;
        }}


        /* ==================================================
           RESPONSIVE
        ================================================== */

        @media (max-width: 900px) {{

            .sales-kpi-strip {{
                grid-template-columns:
                    repeat(
                        2,
                        minmax(0, 1fr)
                    );
            }}

            .sales-kpi {{
                border: 1px solid #E1ECEF;
            }}

            .sales-chart-grid {{
                grid-template-columns: 1fr;
            }}
        }}

        @media (max-width: 650px) {{

            [data-testid="stMainBlockContainer"] {{
                padding-left: 0.65rem;
                padding-right: 0.65rem;
            }}

            .sales-hero {{
                min-height: 150px;
                padding: 1.4rem 1.2rem;
            }}

            .sales-hero-title {{
                font-size: 1.75rem;
            }}

            .sales-hero-description {{
                font-size: 0.74rem;
            }}

            .sales-floating-home {{
                left: 12px;
                bottom: 14px;
                min-height: 44px;
                padding-right: 13px;
            }}

            .sales-kpi-strip {{
                grid-template-columns: 1fr;
            }}
        }}

        </style>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# CHART HELPERS
# ============================================================

def _chart_layout(
    height: int = 285,
) -> dict[str, Any]:
    """Return shared Plotly styling."""

    return {
        "height": height,
        "margin": {
            "l": 48,
            "r": 22,
            "t": 16,
            "b": 42,
        },
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {
            "family": "Arial, sans-serif",
            "size": 10,
            "color": TEXT,
        },
        "showlegend": False,
    }


def _empty_figure(
    message: str,
    height: int = 285,
) -> go.Figure:
    """Create a readable empty chart."""

    figure = go.Figure()

    figure.add_annotation(
        text=message,
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        showarrow=False,
        font={
            "family": "Arial, sans-serif",
            "size": 11,
            "color": MUTED,
        },
    )

    layout = _chart_layout(height)

    figure.update_layout(
        **layout,
        xaxis={"visible": False},
        yaxis={"visible": False},
    )

    return figure


# ============================================================
# SECTION HEADING
# ============================================================

def render_section_heading(
    eyebrow: str,
    title: str,
    description: str,
    icon: str,
    dark: bool = False,
) -> None:
    """Render a dashboard section heading."""

    section_class = (
        " dark"
        if dark
        else ""
    )

    html = (
        f'<div class="sales-section-heading{section_class}">'
        f'<div class="sales-section-icon">{icon}</div>'
        '<div>'
        f'<div class="sales-section-eyebrow">'
        f'{eyebrow}'
        '</div>'
        f'<div class="sales-section-title">'
        f'{title}'
        '</div>'
        f'<div class="sales-section-description">'
        f'{description}'
        '</div>'
        '</div>'
        '</div>'
    )

    st.markdown(
        html,
        unsafe_allow_html=True,
    )


# ============================================================
# HERO + KPIs
# ============================================================

def render_header(
    latest_date: pd.Timestamp | None,
) -> None:
    """Render the Sales Performance hero."""

    date_text = (
        latest_date.strftime("%d %b %Y")
        if latest_date is not None
        else "No sales date available"
    )

    html = (
        '<section class="sales-hero">'

        '<div class="sales-hero-ring" '
        'style="'
        'width:330px;'
        'height:330px;'
        'right:-100px;'
        'bottom:-205px;'
        '"></div>'

        '<div class="sales-hero-ring" '
        'style="'
        'width:460px;'
        'height:460px;'
        'right:-165px;'
        'bottom:-285px;'
        'opacity:.62;'
        '"></div>'

        '<div class="sales-hero-ring" '
        'style="'
        'width:190px;'
        'height:190px;'
        'right:80px;'
        'top:-110px;'
        'opacity:.50;'
        '"></div>'

        '<div class="sales-hero-content">'

        '<div class="sales-hero-eyebrow">'
        'Sales Performance'
        '</div>'

        '<div class="sales-hero-title">'
        'Track revenue.<br>'
        'Understand what drives performance.'
        '</div>'

        '<div class="sales-hero-description">'
        'Monitor revenue, sales velocity, growth and the factors '
        'shaping business performance over time.'
        '</div>'

        '</div>'

        '<div class="sales-hero-asof">'
        'Data as of:'
        f'<strong>{date_text}</strong>'
        '</div>'

        '</section>'
    )

    st.markdown(
        html,
        unsafe_allow_html=True,
    )


def render_kpis(
    sales: pd.DataFrame,
) -> None:
    """Render the five executive Sales Performance KPIs."""

    total_revenue = safe_float(
        sales["amount"].sum()
    )

    total_orders = float(
        sales["invoice"].nunique()
    )

    average_order_value = (
        total_revenue / total_orders
        if total_orders > 0
        else 0.0
    )

    sales_velocity = 0.0

    if not sales.empty:
        first_date = sales["posting_date"].min()
        last_date = sales["posting_date"].max()

        if (
            not pd.isna(first_date)
            and not pd.isna(last_date)
        ):
            day_count = max(
                int(
                    (
                        last_date
                        - first_date
                    ).days
                ) + 1,
                1,
            )

            sales_velocity = (
                total_revenue
                / day_count
            )

    monthly = (
        sales.assign(
            month=sales["posting_date"]
            .dt.to_period("M")
        )
        .groupby(
            "month",
            as_index=False,
        )["amount"]
        .sum()
        .sort_values(
            by="month"
        )  # type: ignore[call-overload]
    )

    growth_rate = 0.0

    if len(monthly) >= 2:
        previous = safe_float(
            monthly.iloc[-2]["amount"]
        )

        current = safe_float(
            monthly.iloc[-1]["amount"]
        )

        if previous != 0:
            growth_rate = (
                (current - previous)
                / abs(previous)
                * 100.0
            )

    metrics = [
        (
            "TOTAL REVENUE",
            format_currency(
                total_revenue
            ),
            "Net recorded sales revenue",
        ),
        (
            "TOTAL ORDERS",
            format_number(
                total_orders
            ),
            "Distinct sales invoices",
        ),
        (
            "AVG ORDER VALUE",
            format_currency(
                average_order_value
            ),
            "Revenue per order",
        ),
        (
            "SALES VELOCITY",
            (
                f"{format_currency(sales_velocity)}"
                " / day"
            ),
            "Average revenue per active day",
        ),
        (
            "GROWTH RATE",
            f"{growth_rate:+.2f}%",
            "Latest month vs previous month",
        ),
    ]

    cards = "".join(
        (
            '<div class="sales-kpi">'
            f'<div class="sales-kpi-label">'
            f'{label}'
            '</div>'
            f'<div class="sales-kpi-value">'
            f'{value}'
            '</div>'
            f'<div class="sales-kpi-note">'
            f'{note}'
            '</div>'
            '</div>'
        )
        for label, value, note in metrics
    )

    html = (
        '<section class="sales-executive-summary">'

        '<div class="sales-executive-kicker">'
        'Revenue'
        '</div>'

        '<div class="sales-executive-title">'
        'Executive KPIs'
        '</div>'

        '<div class="sales-executive-description">'
        'A quick view of revenue scale, order value, '
        'sales velocity and growth.'
        '</div>'

        f'<div class="sales-kpi-strip">'
        f'{cards}'
        '</div>'

        '</section>'
    )

    st.markdown(
        html,
        unsafe_allow_html=True,
    )


# ============================================================
# REVENUE OVER TIME
# ============================================================

def render_revenue_over_time(
    timeseries_engine: TimeSeriesEngine,
    sales: pd.DataFrame,
) -> None:
    """Render daily revenue."""

    try:
        daily = (
            timeseries_engine
            .daily_sales()
        )
    except (
        KeyError,
        TypeError,
        ValueError,
    ):
        daily = pd.DataFrame()

    if daily.empty and not sales.empty:
        daily = (
            sales.assign(
                Date=sales["posting_date"]
                .dt.normalize()
            )
            .groupby(
                "Date",
                as_index=False,
            )["amount"]
            .sum()
            .rename(
                columns={
                    "amount": "Revenue"
                }
            )  # type: ignore[call-overload]
        )

    figure = _daily_revenue_figure(
        daily
    )

    st.markdown(
        '<article class="sales-chart-card">'
        '<div class="sales-chart-header">'
        '<div>'
        '<div class="sales-chart-title">'
        'Revenue Over Time'
        '</div>'
        '<div class="sales-chart-description">'
        'Daily revenue trend'
        '</div>'
        '</div>'
        '<div class="sales-chart-badge">'
        'Daily'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.plotly_chart(
        figure,
        use_container_width=True,
        config={
            "displayModeBar": False
        },
    )

    st.markdown(
        '</article>',
        unsafe_allow_html=True,
    )


def _daily_revenue_figure(
    daily: pd.DataFrame,
) -> go.Figure:
    """Build the daily revenue figure."""

    date_column = next(
        (
            column
            for column in (
                "Date",
                "date",
            )
            if column in daily.columns
        ),
        None,
    )

    revenue_column = next(
        (
            column
            for column in (
                "Revenue",
                "revenue",
            )
            if column in daily.columns
        ),
        None,
    )

    if (
        date_column is None
        or revenue_column is None
    ):
        return _empty_figure(
            "Daily revenue data is not available."
        )

    plot = daily.copy()

    plot[date_column] = pd.to_datetime(
        plot[date_column],
        errors="coerce",
    )

    plot[revenue_column] = pd.to_numeric(
        plot[revenue_column],
        errors="coerce",
    ).fillna(0.0)

    plot = plot.dropna(
        subset=[date_column],
    ).sort_values(
        by=date_column
    )  # type: ignore[call-overload]

    if plot.empty:
        return _empty_figure(
            "Daily revenue data is not available."
        )

    figure = go.Figure(
        go.Scatter(
            x=plot[date_column],
            y=plot[revenue_column],
            mode="lines",
            line={
                "color": AQUA,
                "width": 2.5,
            },
            fill="tozeroy",
            fillcolor=(
                "rgba(17,175,193,0.12)"
            ),
            hovertemplate=(
                "<b>%{x|%d %b %Y}</b><br>"
                "Revenue: ₹%{y:,.0f}"
                "<extra></extra>"
            ),
        )
    )

    figure.update_layout(
        **_chart_layout(300)
    )

    figure.update_xaxes(
        showgrid=False,
        tickfont={
            "family": "Arial, sans-serif",
            "size": 11,
            "color": AXIS_LIGHT,
        },
        tickformat="%b %d",
        nticks=7,
    )

    figure.update_yaxes(
        showgrid=True,
        gridcolor=GRID_DARK,
        gridwidth=1,
        zeroline=False,
        tickfont={
            "family": "Arial, sans-serif",
            "size": 11,
            "color": AXIS_LIGHT,
        },
        tickprefix="₹",
        tickformat="~s",
    )

    return figure


# ============================================================
# REVENUE BY TIME PERIOD
# ============================================================

def render_revenue_by_period(
    timeseries_engine: TimeSeriesEngine,
    sales: pd.DataFrame,
) -> None:
    """Render monthly revenue."""

    try:
        monthly = (
            timeseries_engine
            .monthly_sales()
        )
    except (
        KeyError,
        TypeError,
        ValueError,
    ):
        monthly = pd.DataFrame()

    if monthly.empty and not sales.empty:
        monthly = (
            sales.assign(
                Month=sales["posting_date"]
                .dt.to_period("M")
                .astype(str)
            )
            .groupby(
                "Month",
                as_index=False,
            )["amount"]
            .sum()
            .rename(
                columns={
                    "amount": "Revenue"
                }
            )  # type: ignore[call-overload]
        )

    figure = _monthly_revenue_figure(
        monthly
    )

    st.markdown(
        '<article class="sales-chart-card">'
        '<div class="sales-chart-header">'
        '<div>'
        '<div class="sales-chart-title">'
        'Revenue by Time Period'
        '</div>'
        '<div class="sales-chart-description">'
        'Compare performance across monthly periods'
        '</div>'
        '</div>'
        '<div class="sales-chart-badge">'
        'Monthly'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.plotly_chart(
        figure,
        use_container_width=True,
        config={
            "displayModeBar": False
        },
    )

    st.markdown(
        '</article>',
        unsafe_allow_html=True,
    )


def _monthly_revenue_figure(
    monthly: pd.DataFrame,
) -> go.Figure:
    """Build the monthly revenue figure."""

    if monthly.empty:
        return _empty_figure(
            "Monthly revenue data is not available."
        )

    period_column = next(
        (
            column
            for column in (
                "Month",
                "month",
            )
            if column in monthly.columns
        ),
        None,
    )

    revenue_column = next(
        (
            column
            for column in (
                "Revenue",
                "revenue",
            )
            if column in monthly.columns
        ),
        None,
    )

    if (
        period_column is None
        or revenue_column is None
    ):
        return _empty_figure(
            "Monthly revenue data is not available."
        )

    plot = monthly.copy()

    plot[revenue_column] = pd.to_numeric(
        plot[revenue_column],
        errors="coerce",
    ).fillna(0.0)

    plot = plot.tail(12)

    labels = [
        str(value)[:7]
        for value in plot[
            period_column
        ].tolist()
    ]

    values = [
        safe_float(value)
        for value in plot[
            revenue_column
        ].tolist()
    ]

    bar_colors = [
        (
            DEEP_OCEAN
            if index == len(values) - 1
            else AQUA_LIGHT
        )
        for index in range(
            len(values)
        )
    ]

    figure = go.Figure(
        go.Bar(
            x=labels,
            y=values,
            marker_color=bar_colors,
            text=[
                format_currency(value)
                for value in values
            ],
            textposition="outside",
            textfont={
                "family": "Arial, sans-serif",
                "size": 11,
                "color": "#FFFFFF",
            },
            cliponaxis=False,
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Revenue: ₹%{y:,.0f}"
                "<extra></extra>"
            ),
        )
    )

    chart_layout = _chart_layout(300)

    chart_layout["margin"] = {
        "l": 48,
        "r": 18,
        "t": 28,
        "b": 46,
    }

    figure.update_layout(
        **chart_layout
    )

    figure.update_xaxes(
        showgrid=False,
        tickfont={
            "family": "Arial, sans-serif",
            "size": 11,
            "color": AXIS_LIGHT,
        },
        ticks="outside",
        tickcolor="rgba(216,245,247,0.75)",
    )

    figure.update_yaxes(
        showgrid=True,
        gridcolor=GRID_DARK,
        gridwidth=1,
        zeroline=False,
        tickfont={
            "family": "Arial, sans-serif",
            "size": 11,
            "color": AXIS_LIGHT,
        },
        tickprefix="₹",
        tickformat="~s",
    )

    return figure


# ============================================================
# CATEGORY + REGION
# ============================================================

def render_category_and_region(
    sales: pd.DataFrame,
    regional_engine: RegionalEngine,
) -> None:
    """Render category contribution and regional revenue."""

    category_figure = _category_figure(
        sales
    )

    region_figure = _region_figure(
        regional_engine,
        sales,
    )

    st.markdown(
        '<div class="sales-chart-grid">',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<article class="sales-chart-card">'
        '<div class="sales-chart-header">'
        '<div>'
        '<div class="sales-chart-title">'
        'Revenue by Category'
        '</div>'
        '<div class="sales-chart-description">'
        'Top 10 categories by revenue contribution'
        '</div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.plotly_chart(
        category_figure,
        use_container_width=True,
        config={
            "displayModeBar": False
        },
    )

    st.markdown(
        '</article>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<article class="sales-chart-card">'
        '<div class="sales-chart-header">'
        '<div>'
        '<div class="sales-chart-title">'
        'Revenue by Region'
        '</div>'
        '<div class="sales-chart-description">'
        'Top performing regions'
        '</div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.plotly_chart(
        region_figure,
        use_container_width=True,
        config={
            "displayModeBar": False
        },
    )

    st.markdown(
        '</article>'
        '</div>',
        unsafe_allow_html=True,
    )


def _category_figure(
    sales: pd.DataFrame,
) -> go.Figure:
    """Build the clean Top-10 revenue-by-category donut."""

    if sales.empty:
        return _empty_figure(
            "Category revenue is not available.",
            390,
        )

    grouped = (
        sales.dropna(subset=["item_group"])
        .groupby("item_group", as_index=False)["amount"]
        .sum()
        .sort_values(
            by="amount",
            ascending=False,
        )  # type: ignore[call-overload]
        .head(10)
    )

    if grouped.empty:
        return _empty_figure(
            "Category revenue is not available.",
            390,
        )

    category_names = grouped["item_group"].astype(str).tolist()
    category_values = [
        safe_float(value)
        for value in grouped["amount"].tolist()
    ]

    top_10_revenue = sum(category_values)
    total_revenue = safe_float(sales["amount"].sum())
    top_10_share = (
        top_10_revenue / total_revenue * 100.0
        if total_revenue > 0
        else 0.0
    )

    legend_labels = [
        (
            f"{name}  •  "
            f"{value / total_revenue * 100:.1f}%"
        )
        if total_revenue > 0
        else name
        for name, value in zip(
            category_names,
            category_values,
        )
    ]

    figure = go.Figure(
        go.Pie(
            labels=legend_labels,
            customdata=category_names,
            values=category_values,
            hole=0.64,
            textinfo="none",
            sort=False,
            direction="clockwise",
            domain={
                "x": [0.28, 0.66],
                "y": [0.08, 0.94],
            },
            marker={
                "colors": [
                    DEEP_OCEAN,
                    AQUA,
                    "#35BFCB",
                    "#74D3D9",
                    "#8FDCE1",
                    "#B8E9ED",
                    "#CBECEF",
                    "#DDEFF1",
                    "#78B9E8",
                    "#4D9FDD",
                ],
                "line": {
                    "color": WHITE,
                    "width": 2,
                },
            },
            hovertemplate=(
                "<b>%{customdata}</b><br>"
                "Revenue: ₹%{value:,.0f}<br>"
                "Share: %{percent}"
                "<extra></extra>"
            ),
        )
    )

    figure.update_layout(
        height=390,
        margin={
            "l": 8,
            "r": 8,
            "t": 8,
            "b": 8,
        },
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={
            "family": "Arial, sans-serif",
            "size": 10,
            "color": TEXT,
        },
        showlegend=True,
        legend={
            "orientation": "v",
            "x": 0.72,
            "xanchor": "left",
            "y": 0.50,
            "yanchor": "middle",
            "font": {
                "family": "Arial, sans-serif",
                "size": 10,
                "color": TEXT,
            },
            "bgcolor": "rgba(255,255,255,0)",
            "borderwidth": 0,
            "itemsizing": "constant",
            "tracegroupgap": 2,
        },
        shapes=[
            {
                "type": "rect",
                "xref": "paper",
                "yref": "paper",
                "x0": 0.035,
                "x1": 0.285,
                "y0": 0.035,
                "y1": 0.300,
                "line": {
                    "color": "#D6E7EA",
                    "width": 1,
                },
                "fillcolor": "#FFFFFF",
                "layer": "below",
            },
        ],
        annotations=[
            {
                "text": "TOP 10 CATEGORY REVENUE",
                "x": 0.050,
                "y": 0.265,
                "xref": "paper",
                "yref": "paper",
                "xanchor": "left",
                "yanchor": "top",
                "showarrow": False,
                "font": {
                    "family": "Arial Black, Arial, sans-serif",
                    "size": 10,
                    "color": "#008FA3",
                },
            },
            {
                "text": format_currency(top_10_revenue),
                "x": 0.050,
                "y": 0.180,
                "xref": "paper",
                "yref": "paper",
                "xanchor": "left",
                "yanchor": "top",
                "showarrow": False,
                "font": {
                    "family": "Arial Black, Arial, sans-serif",
                    "size": 18,
                    "color": "#082F3A",
                },
            },
            {
                "text": f"{top_10_share:.1f}% of total revenue",
                "x": 0.050,
                "y": 0.095,
                "xref": "paper",
                "yref": "paper",
                "xanchor": "left",
                "yanchor": "top",
                "showarrow": False,
                "font": {
                    "family": "Arial, sans-serif",
                    "size": 9,
                    "color": "#617982",
                },
            },
        ],
    )

    return figure


# ============================================================
# REGION FIGURE
# ============================================================

def _region_figure(
    regional_engine: RegionalEngine,
    sales: pd.DataFrame,
) -> go.Figure:
    """Build the top-region revenue bars."""

    try:
        summary = (
            regional_engine
            .top_regions_by_revenue(5)
        )
    except (
        AttributeError,
        KeyError,
        TypeError,
        ValueError,
    ):
        summary = pd.DataFrame()

    if summary.empty and not sales.empty:
        summary = (
            sales.dropna(
                subset=["place_of_supply"]
            )
            .groupby(
                "place_of_supply",
                as_index=False,
            )["amount"]
            .sum()
            .rename(
                columns={
                    "place_of_supply": "Region",
                    "amount": "Revenue",
                }
            )  # type: ignore[call-overload]
            .sort_values(
                by="Revenue",
                ascending=False,
            )
            .head(5)
        )

    if summary.empty:
        return _empty_figure(
            "Regional revenue is not available.",
            330,
        )

    region_column = next(
        (
            column
            for column in (
                "Region",
                "region",
            )
            if column in summary.columns
        ),
        None,
    )

    revenue_column = next(
        (
            column
            for column in (
                "Revenue",
                "revenue",
            )
            if column in summary.columns
        ),
        None,
    )

    if (
        region_column is None
        or revenue_column is None
    ):
        return _empty_figure(
            "Regional revenue is not available.",
            330,
        )

    plot = summary.copy()

    plot[revenue_column] = pd.to_numeric(
        plot[revenue_column],
        errors="coerce",
    ).fillna(0.0)

    plot = plot.sort_values(
        by=revenue_column,
        ascending=True,
    )  # type: ignore[call-overload]

    values = [
        safe_float(value)
        for value in plot[
            revenue_column
        ].tolist()
    ]

    labels = [
        str(value)
        for value in plot[
            region_column
        ].tolist()
    ]

    figure = go.Figure(
        go.Bar(
            x=values,
            y=labels,
            orientation="h",
            marker_color=AQUA,
            text=[
                format_currency(value)
                for value in values
            ],
            textposition="outside",
            textfont={
                "family": "Arial, sans-serif",
                "size": 10,
                "color": TEXT,
            },
            cliponaxis=False,
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Revenue: ₹%{x:,.0f}"
                "<extra></extra>"
            ),
        )
    )

    figure.update_layout(
        height=330,
        margin={
            "l": 72,
            "r": 76,
            "t": 18,
            "b": 44,
        },
        paper_bgcolor=(
            "rgba(0,0,0,0)"
        ),
        plot_bgcolor=(
            "rgba(0,0,0,0)"
        ),
        font={
            "family": "Arial, sans-serif",
            "size": 10,
            "color": TEXT,
        },
        showlegend=False,
    )

    figure.update_xaxes(
        showgrid=True,
        gridcolor="#DCEBED",
        gridwidth=1,
        zeroline=False,
        tickfont={
            "family": "Arial, sans-serif",
            "size": 11,
            "color": TEXT,
        },
        tickprefix="₹",
        tickformat="~s",
        ticks="outside",
        tickcolor="#9FBBC2",
        title_font={
            "family": "Arial, sans-serif",
            "size": 11,
            "color": TEXT,
        },
    )

    figure.update_yaxes(
        showgrid=False,
        tickfont={
            "family": "Arial, sans-serif",
            "size": 11,
            "color": TEXT,
        },
        ticks="",
    )

    return figure


# ============================================================
# SALES INSIGHTS
# ============================================================

def render_sales_insights(
    sales: pd.DataFrame,
) -> None:
    """Render deterministic executive insights."""

    if sales.empty:
        message = (
            "No sales data is available to "
            "generate sales insights."
        )

    else:
        monthly = (
            sales.assign(
                month=sales["posting_date"]
                .dt.to_period("M")
            )
            .groupby(
                "month",
                as_index=False,
            )["amount"]
            .sum()
            .sort_values(
                by="month"
            )  # type: ignore[call-overload]
        )

        current_month_revenue = (
            safe_float(
                monthly.iloc[-1]["amount"]
            )
            if not monthly.empty
            else 0.0
        )

        previous_month_revenue = (
            safe_float(
                monthly.iloc[-2]["amount"]
            )
            if len(monthly) >= 2
            else 0.0
        )

        growth = (
            (
                current_month_revenue
                - previous_month_revenue
            )
            / abs(previous_month_revenue)
            * 100.0
            if previous_month_revenue != 0
            else 0.0
        )

        category = (
            sales.groupby(
                "item_group"
            )["amount"]
            .sum()
            .sort_values(
                ascending=False
            )  # type: ignore[call-overload]
        )

        region = (
            sales.groupby(
                "place_of_supply"
            )["amount"]
            .sum()
            .sort_values(
                ascending=False
            )  # type: ignore[call-overload]
        )

        top_category = (
            str(category.index[0])
            if not category.empty
            else "N/A"
        )

        top_region = (
            str(region.index[0])
            if not region.empty
            else "N/A"
        )

        message = (
            "Revenue changed by "
            f'<span class="sales-insight-value">'
            f'{growth:+.2f}%'
            "</span> "
            "in the latest month. "
            f'<span class="sales-insight-value">'
            f'{top_category}'
            "</span> is the leading revenue category, "
            "while "
            f'<span class="sales-insight-value">'
            f'{top_region}'
            "</span> is the leading region."
        )

    st.markdown(
        '<div class="sales-insight">'
        '<div class="sales-insight-icon">↗</div>'
        '<div>'
        '<div class="sales-insight-label">'
        'Sales Insights'
        '</div>'
        f'{message}'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )


# ============================================================
# PUBLIC RENDER FUNCTION
# ============================================================

def render_sales_performance_dashboard(
    on_back: Callable[[], None] | None = None,
) -> None:
    """
    Render the expanded Sales Performance dashboard.
    """

    del on_back

    inject_sales_css()

    render_brand()
    render_navigation("sales")

    # ========== FIX: added target="_self" ==========
    st.markdown(
        '<a href="?page=home" '
        'target="_self" '
        'class="sales-floating-home" '
        'aria-label="Back to Home">'
        '<span class="sales-floating-home-icon">'
        '⌂'
        '</span>'
        '<span class="sales-floating-home-text">'
        'BACK TO HOME'
        '</span>'
        '</a>',
        unsafe_allow_html=True,
    )

    sales = _sales_only(
        _get_sales_dataframe()
    )

    latest_date: pd.Timestamp | None = None

    if not sales.empty:
        candidate = sales["posting_date"].max()

        if not pd.isna(candidate):
            latest_date = pd.Timestamp(
                candidate
            )

    st.markdown(
        '<div class="sales-performance-page">',
        unsafe_allow_html=True,
    )

    render_header(
        latest_date
    )

    render_kpis(
        sales
    )

    timeseries_engine = (
        TimeSeriesEngine()
    )

    regional_engine = (
        RegionalEngine()
    )

    with st.container(
        key="sales_revenue_section"
    ):
        render_section_heading(
            "Revenue Performance",
            "How is revenue moving?",
            (
                "Track daily movement and compare "
                "performance across monthly periods."
            ),
            "↗",
            dark=True,
        )

        st.markdown(
            '<div class="sales-chart-grid">',
            unsafe_allow_html=True,
        )

        render_revenue_over_time(
            timeseries_engine,
            sales,
        )

        render_revenue_by_period(
            timeseries_engine,
            sales,
        )

        st.markdown(
            '</div>',
            unsafe_allow_html=True,
        )

    with st.container(
        key="sales_breakdown_section"
    ):
        render_section_heading(
            "Revenue Breakdown",
            "Where is revenue coming from?",
            (
                "Compare category contribution and "
                "the regions generating the most revenue."
            ),
            "▥",
        )

        render_category_and_region(
            sales,
            regional_engine,
        )

    with st.container(
        key="sales_insights_section"
    ):
        render_section_heading(
            "Sales Insights",
            "What should leadership notice?",
            (
                "A concise summary of recent revenue "
                "movement, category strength and "
                "regional performance."
            ),
            "✦",
            dark=True,
        )

        render_sales_insights(
            sales
        )

    st.markdown(
        '</div>',
        unsafe_allow_html=True,
    )


def main() -> None:
    """Render the Sales Performance dashboard."""

    apply_theme(
        "AQVASTAR | Sales Performance"
    )

    render_sales_performance_dashboard()


if __name__ == "__main__":
    main()