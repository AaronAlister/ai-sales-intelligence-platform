"""
AQVASTAR Sales Intelligence Platform.

Product Intelligence dashboard rendered from the Home page.

Dashboard orchestration only. Product-level business logic remains in
ProductEngine.
"""

from __future__ import annotations

from collections.abc import Callable
from html import escape
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
from engines.product_engine import ProductEngine
from database.queries import SalesQueries


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
# FORMATTERS
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


def format_percentage(value: float) -> str:
    """Format a percentage."""

    return f"{float(value):.2f}%"


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
# CSS
# ============================================================

def inject_product_css() -> None:
    """Inject the Product Intelligence visual system."""

    st.markdown(
        f"""
        <style>

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
           BACK HOME
           ================================================== */

        .product-floating-home {{
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

            background: rgba(255,255,255,0.98);
            color: #164B59 !important;

            box-shadow: 0 12px 32px rgba(4,62,76,0.18);

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

        .product-floating-home:hover {{
            transform: translateY(-3px);
            border-color: {AQUA};
            box-shadow: 0 16px 36px rgba(4,62,76,0.22);
            color: #087C8A !important;
        }}

        .product-floating-home-icon {{
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

        .product-floating-home-text {{
            white-space: nowrap;
        }}

        /* ==================================================
           HERO
           ================================================== */

        .product-hero {{
            position: relative;
            overflow: hidden;

            min-height: 176px;

            padding: 2rem 2.25rem;
            margin: 0.35rem 0 0.85rem;

            border-radius: 20px;

            background:
                radial-gradient(
                    circle at 83% 30%,
                    rgba(50,202,215,0.50),
                    transparent 28%
                ),
                linear-gradient(
                    115deg,
                    {DEEP_OCEAN} 0%,
                    {OCEAN} 58%,
                    #1597A6 100%
                );

            box-shadow: 0 14px 34px rgba(5,60,74,0.14);
        }}

        .product-hero-content {{
            position: relative;
            z-index: 3;
            max-width: 760px;
        }}

        .product-hero-eyebrow {{
            color: #3BD0D8;

            font-size: 0.60rem;
            font-weight: 800;

            letter-spacing: 0.18em;
            text-transform: uppercase;

            margin-bottom: 0.58rem;
        }}

        .product-hero-title {{
            color: #FFFFFF;

            font-size: clamp(1.85rem, 3.1vw, 3rem);

            line-height: 1.02;
            font-weight: 800;

            letter-spacing: -0.045em;

            margin-bottom: 0.62rem;
        }}

        .product-hero-description {{
            max-width: 620px;

            color: rgba(255,255,255,0.76);

            font-size: 0.76rem;
            line-height: 1.45;
        }}

        .product-hero-asof {{
            position: absolute;
            right: 2.25rem;
            top: 2rem;
            z-index: 4;

            color: rgba(255,255,255,0.62);

            font-size: 0.65rem;
            line-height: 1.4;
            text-align: right;
        }}

        .product-hero-asof strong {{
            display: block;
            color: #FFFFFF;
            font-size: 0.75rem;
            margin-top: 0.15rem;
        }}

        .product-hero-ring {{
            position: absolute;

            border: 1px solid rgba(255,255,255,0.13);
            border-radius: 50%;

            pointer-events: none;
        }}

        /* ==================================================
           SECTION CONTAINERS
           ================================================== */

        .st-key-product_performance_section,
        .st-key-product_returns_section,
        .st-key-product_growth_section,
        .st-key-product_contribution_section,
        .st-key-product_explorer_section {{
            position: relative;
            overflow: hidden;

            border-radius: 20px;

            margin-top: 1.05rem;
            margin-bottom: 1.45rem;

            padding: 1.25rem 1.35rem 2.05rem;
        }}

        .st-key-product_performance_section,
        .st-key-product_growth_section,
        .st-key-product_explorer_section {{
            background:
                linear-gradient(
                    145deg,
                    #F7FCFD 0%,
                    #EAF7F9 100%
                );

            border: 1px solid #D8EAEE;

            box-shadow:
                0 12px 32px
                rgba(5,57,70,0.07);
        }}

        .st-key-product_returns_section,
        .st-key-product_contribution_section {{
            background:
                linear-gradient(
                    145deg,
                    #064652 0%,
                    #0B6C79 100%
                );

            box-shadow:
                0 16px 38px
                rgba(5,57,70,0.13);
        }}

        /* ==================================================
           SECTION HEADING
           ================================================== */

        .product-section-heading {{
            display: flex;
            align-items: flex-start;
            gap: 16px;
            margin-bottom: 1.15rem;
        }}

        .product-section-icon {{
            display: flex;
            align-items: center;
            justify-content: center;
            flex: 0 0 auto;

            width: 52px;
            height: 52px;

            border-radius: 15px;

            background: {AQUA};
            color: #FFFFFF;

            font-size: 1.1rem;
            font-weight: 800;

            box-shadow:
                0 8px 18px
                rgba(17,175,193,0.22);
        }}

        .product-section-eyebrow {{
            color: #0794A5;

            font-size: 0.60rem;
            font-weight: 800;

            letter-spacing: 0.18em;
            text-transform: uppercase;

            margin-bottom: 0.28rem;
        }}

        .product-section-title {{
            color: {TEXT};

            font-size: 1.32rem;
            font-weight: 800;

            letter-spacing: -0.035em;
            line-height: 1.1;
        }}

        .product-section-description {{
            color: {MUTED};

            font-size: 0.73rem;
            line-height: 1.45;

            margin-top: 0.32rem;
        }}

        .product-section-heading.dark
        .product-section-eyebrow {{
            color: #3BD0D8;
        }}

        .product-section-heading.dark
        .product-section-title {{
            color: #FFFFFF;
        }}

        .product-section-heading.dark
        .product-section-description {{
            color: rgba(255,255,255,0.70);
        }}

        /* ==================================================
           KPI STRIP
           ================================================== */

        .product-executive-summary {{
            position: relative;
            overflow: hidden;
            margin: 0.85rem 0 1.15rem;
            padding: 0.15rem 0 0.05rem;
        }}

        .product-executive-kicker {{
            color: #11899A;
            font-size: 0.64rem;
            font-weight: 800;
            letter-spacing: 0.16em;
            text-transform: uppercase;
            margin-bottom: 0.18rem;
        }}

        .product-executive-title {{
            color: {TEXT};
            font-size: 1.32rem;
            line-height: 1.15;
            font-weight: 800;
            letter-spacing: -0.025em;
            margin-bottom: 0.18rem;
        }}

        .product-executive-description {{
            color: {MUTED};
            font-size: 0.74rem;
            line-height: 1.4;
            margin-bottom: 0.68rem;
        }}

        .product-kpi-strip {{
            display: grid;
            grid-template-columns: repeat(5, minmax(0, 1fr));
            gap: 0.65rem;
        }}

        .product-kpi {{
            min-width: 0;
            padding: 0.78rem 0.82rem;
            border: 1px solid #D6E7EB;
            border-radius: 13px;
            background: #FFFFFF;
            box-shadow: 0 6px 18px rgba(7,63,76,0.045);
        }}

        .product-kpi-label {{
            color: #198C9B;
            font-size: 0.57rem;
            font-weight: 800;
            letter-spacing: 0.10em;
            text-transform: uppercase;
        }}

        .product-kpi-value {{
            color: {TEXT};
            font-size: 1.28rem;
            line-height: 1.05;
            font-weight: 800;
            letter-spacing: -0.025em;
            margin: 0.30rem 0 0.16rem;
        }}

        .product-kpi-note {{
            color: {MUTED};
            font-size: 0.57rem;
            line-height: 1.3;
        }}

        /* ==================================================
           CHART CARDS
           ================================================== */

        .product-chart-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 18px;
            margin-bottom: 18px;
        }}

        .product-chart-card {{
            min-width: 0;

            background: #FFFFFF;

            border: 1px solid #E0EAED;
            border-radius: 18px;

            box-shadow:
                0 10px 28px
                rgba(5,57,70,0.06);

            overflow: hidden;
        }}

        .product-chart-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;

            min-height: 62px;

            padding: 14px 18px 10px;

            border-bottom: 1px solid #EDF2F3;
        }}

        .product-chart-title {{
            color: {TEXT};

            font-size: 0.96rem;
            font-weight: 800;

            letter-spacing: -0.02em;
        }}

        .product-chart-description {{
            color: #71878E;

            font-size: 0.67rem;
            margin-top: 3px;
        }}

        .product-chart-badge {{
            padding: 6px 9px;

            border-radius: 8px;

            background: #E8F7F9;
            color: #087C8A;

            font-size: 0.61rem;
            font-weight: 800;
        }}

        /* ==================================================
           TABLE
           ================================================== */

        .product-table {{
            width: 100%;
            border-collapse: collapse;
            background: #FFFFFF;
        }}

        .product-table th {{
            padding: 10px 12px;

            color: #71878E;

            background: #F7FBFC;

            border-bottom: 1px solid #E3EDF0;

            font-size: 0.61rem;
            font-weight: 800;

            letter-spacing: 0.10em;
            text-transform: uppercase;

            text-align: left;
        }}

        .product-table td {{
            padding: 11px 12px;

            color: {TEXT};

            border-bottom: 1px solid #EDF2F3;

            font-size: 0.70rem;
            line-height: 1.35;
        }}

        .product-table tr:last-child td {{
            border-bottom: none;
        }}

        .product-table-name {{
            font-weight: 800;
        }}

        .product-table-value {{
            font-weight: 700;
            white-space: nowrap;
        }}

        .product-class {{
            display: inline-flex;
            align-items: center;
            justify-content: center;

            min-width: 27px;
            height: 27px;

            border-radius: 8px;

            background: #E8F7F9;
            color: #087C8A;

            font-size: 0.66rem;
            font-weight: 900;
        }}

        /* ==================================================
           ABC CARDS
           ================================================== */

        .product-abc-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 14px;
            margin-top: 18px;
        }}

        .product-abc-card {{
            padding: 18px;

            border-radius: 16px;

            background: rgba(255,255,255,0.98);

            border: 1px solid #CFE7EB;

            box-shadow:
                0 8px 24px
                rgba(5,57,70,0.09);
        }}

        .product-abc-label {{
            color: #0794A5;

            font-size: 0.62rem;
            font-weight: 900;

            letter-spacing: 0.16em;
        }}

        .product-abc-value {{
            color: {TEXT};

            font-size: 1.65rem;
            font-weight: 900;

            letter-spacing: -0.04em;

            margin-top: 5px;
        }}

        .product-abc-note {{
            color: {MUTED};

            font-size: 0.68rem;
            line-height: 1.45;

            margin-top: 5px;
        }}

        /* ==================================================
           PROFILE
           ================================================== */

        .product-profile {{
            margin-top: 16px;

            padding: 18px;

            border-radius: 18px;

            background: #FFFFFF;

            border: 1px solid #DDEBED;

            box-shadow:
                0 10px 28px
                rgba(5,57,70,0.06);
        }}

        .product-profile-head {{
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 18px;

            margin-bottom: 16px;
        }}

        .product-profile-eyebrow {{
            color: #0794A5;

            font-size: 0.60rem;
            font-weight: 800;

            letter-spacing: 0.15em;
            text-transform: uppercase;
        }}

        .product-profile-title {{
            color: {TEXT};

            font-size: 1.20rem;
            font-weight: 800;

            margin-top: 4px;
        }}

        .product-profile-class {{
            display: flex;
            align-items: center;
            justify-content: center;

            min-width: 48px;
            height: 42px;

            border-radius: 12px;

            background: {DEEP_OCEAN};
            color: #FFFFFF;

            font-size: 1rem;
            font-weight: 900;
        }}

        .product-profile-metrics {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);

            border: 1px solid #E0EAED;
            border-radius: 14px;

            overflow: hidden;
        }}

        .product-profile-metric {{
            padding: 14px 16px;
            border-right: 1px solid #E0EAED;
        }}

        .product-profile-metric:last-child {{
            border-right: none;
        }}

        .product-profile-label {{
            color: #71878E;

            font-size: 0.60rem;
            font-weight: 800;

            letter-spacing: 0.10em;
            text-transform: uppercase;
        }}

        .product-profile-value {{
            color: {TEXT};

            font-size: 1.10rem;
            font-weight: 800;

            margin-top: 5px;
        }}

        /* ==================================================
           INSIGHT
           ================================================== */

        .product-insight {{
            display: flex;
            align-items: center;
            gap: 12px;

            min-height: 56px;

            margin-top: 18px;
            padding: 10px 14px;

            border: 1px solid #CFE7EB;
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

        .product-insight-icon {{
            display: flex;
            align-items: center;
            justify-content: center;

            flex: 0 0 auto;

            width: 32px;
            height: 32px;

            border-radius: 50%;

            background: {AQUA};
            color: #FFFFFF;

            font-size: 0.9rem;
            font-weight: 800;
        }}

        .product-insight-label {{
            color: #087C8A;

            font-size: 0.61rem;
            font-weight: 800;

            letter-spacing: 0.13em;
            text-transform: uppercase;

            margin-bottom: 2px;
        }}

        .product-insight-value {{
            color: #0A9AAA;
            font-weight: 800;
        }}

        /* ==================================================
           RESPONSIVE
           ================================================== */

        @media (max-width: 900px) {{
            .product-kpi-strip {{
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }}

            .product-chart-grid {{
                grid-template-columns: 1fr;
            }}

            .product-profile-metrics {{
                grid-template-columns: repeat(2, 1fr);
            }}

            .product-profile-metric:nth-child(2) {{
                border-right: none;
            }}

            .product-profile-metric:nth-child(-n+2) {{
                border-bottom: 1px solid #E0EAED;
            }}
        }}

        @media (max-width: 650px) {{
            [data-testid="stMainBlockContainer"] {{
                padding-left: 0.65rem;
                padding-right: 0.65rem;
            }}

            .product-hero {{
                min-height: 150px;
                padding: 1.4rem 1.2rem;
            }}

            .product-hero-title {{
                font-size: 1.75rem;
            }}

            .product-hero-description {{
                font-size: 0.74rem;
            }}

            .product-floating-home {{
                left: 12px;
                bottom: 14px;
                min-height: 44px;
                padding-right: 13px;
            }}


            .product-kpi-strip {{
                grid-template-columns: 1fr;
            }}

            .product-abc-grid {{
                grid-template-columns: 1fr;
            }}

            .product-profile-metrics {{
                grid-template-columns: 1fr;
            }}

            .product-profile-metric,
            .product-profile-metric:nth-child(2) {{
                border-right: none;
                border-bottom: 1px solid #E0EAED;
            }}

            .product-profile-metric:last-child {{
                border-bottom: none;
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
    dark: bool = False,
) -> dict[str, Any]:
    """Return shared Plotly styling."""

    font_color = "#FFFFFF" if dark else TEXT
    grid_color = GRID_DARK if dark else "#E1ECEF"

    return {
        "height": height,
        "margin": {
            "l": 62,
            "r": 38,
            "t": 20,
            "b": 48,
        },
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {
            "family": "Arial, sans-serif",
            "size": 10,
            "color": font_color,
        },
        "showlegend": False,
        "xaxis": {
            "showgrid": False,
            "zeroline": False,
            "tickfont": {
                "family": "Arial, sans-serif",
                "size": 10,
                "color": font_color,
            },
        },
        "yaxis": {
            "showgrid": True,
            "gridcolor": grid_color,
            "gridwidth": 1,
            "zeroline": False,
            "tickfont": {
                "family": "Arial, sans-serif",
                "size": 10,
                "color": font_color,
            },
        },
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

    figure.update_layout(
        **_chart_layout(height)
    )

    figure.update_xaxes(visible=False)
    figure.update_yaxes(visible=False)

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

    section_class = " dark" if dark else ""

    html = (
        f'<div class="product-section-heading{section_class}">'
        f'<div class="product-section-icon">{escape(icon)}</div>'
        '<div>'
        f'<div class="product-section-eyebrow">'
        f'{escape(eyebrow)}'
        '</div>'
        f'<div class="product-section-title">'
        f'{escape(title)}'
        '</div>'
        f'<div class="product-section-description">'
        f'{escape(description)}'
        '</div>'
        '</div>'
        '</div>'
    )

    st.markdown(
        html,
        unsafe_allow_html=True,
    )


# ============================================================
# HERO
# ============================================================

def render_header(
    latest_date: pd.Timestamp | None,
) -> None:
    """Render the Product Intelligence hero."""

    date_text = (
        latest_date.strftime("%d %b %Y")
        if latest_date is not None
        else "No sales date available"
    )

    html = (
        '<section class="product-hero">'

        '<div class="product-hero-ring" '
        'style="width:330px;height:330px;'
        'right:-100px;bottom:-205px;"></div>'

        '<div class="product-hero-ring" '
        'style="width:460px;height:460px;'
        'right:-165px;bottom:-285px;opacity:.62;"></div>'

        '<div class="product-hero-ring" '
        'style="width:190px;height:190px;'
        'right:80px;top:-110px;opacity:.50;"></div>'

        '<div class="product-hero-content">'

        '<div class="product-hero-eyebrow">'
        'Product Intelligence'
        '</div>'

        '<div class="product-hero-title">'
        'Understand what sells.<br>'
        'Identify what drives the portfolio.'
        '</div>'

        '<div class="product-hero-description">'
        'Analyse product performance, returns, growth and contribution '
        'to understand where the business should focus.'
        '</div>'

        '</div>'

        '<div class="product-hero-asof">'
        'Data as of:'
        f'<strong>{escape(date_text)}</strong>'
        '</div>'

        '</section>'
    )

    st.markdown(
        html,
        unsafe_allow_html=True,
    )


# ============================================================
# KPI SUMMARY
# ============================================================

def render_kpis(
    engine: ProductEngine,
) -> None:
    """Render five executive product KPIs."""

    summary = engine.product_summary
    contribution = engine.product_contribution

    if summary.empty:
        return

    total_products = len(summary)
    total_quantity = safe_float(summary["quantity"].sum())
    total_net_revenue = safe_float(
        contribution["net_revenue"].sum()
    )

    total_returned = safe_float(
        summary["returned_quantity"].sum()
    )

    total_quantity_sold = safe_float(
        summary["quantity"].sum()
    )

    return_rate = (
        total_returned / total_quantity_sold * 100.0
        if total_quantity_sold > 0
        else 0.0
    )

    products_for_80 = len(
        engine.pareto_products()
    )

    metrics = [
        (
            "TOTAL PRODUCTS",
            format_number(float(total_products)),
            "Products in the sales portfolio",
        ),
        (
            "TOTAL UNITS",
            format_number(total_quantity),
            "Units sold across products",
        ),
        (
            "NET REVENUE",
            format_currency(total_net_revenue),
            "Gross revenue after returns",
        ),
        (
            "RETURN RATE",
            format_percentage(return_rate),
            "Returned units as a share of units sold",
        ),
        (
            "80% REVENUE",
            format_number(float(products_for_80)),
            "Products needed to reach 80% of net revenue",
        ),
    ]

    cards = "".join(
        (
            '<div class="product-kpi">'
            f'<div class="product-kpi-label">{escape(label)}</div>'
            f'<div class="product-kpi-value">{escape(value)}</div>'
            f'<div class="product-kpi-note">{escape(note)}</div>'
            '</div>'
        )
        for label, value, note in metrics
    )

    html = (
        '<section class="product-executive-summary">'

        '<div class="product-executive-kicker">'
        'Product Portfolio'
        '</div>'

        '<div class="product-executive-title">'
        'Executive KPIs'
        '</div>'

        '<div class="product-executive-description">'
        'A quick view of product scale, sales volume, net revenue, '
        'returns and revenue concentration.'
        '</div>'

        f'<div class="product-kpi-strip">{cards}</div>'

        '</section>'
    )

    st.markdown(
        html,
        unsafe_allow_html=True,
    )


# ============================================================
# GENERIC PRODUCT CHART
# ============================================================

def _product_bar_figure(
    dataframe: pd.DataFrame,
    value_column: str,
    value_label: str,
    currency: bool = False,
    dark: bool = False,
) -> go.Figure:
    """Build a horizontal product ranking chart."""

    if dataframe.empty:
        return _empty_figure(
            "Product data is not available.",
            300,
        )

    if (
        "item_name" not in dataframe.columns
        or value_column not in dataframe.columns
    ):
        return _empty_figure(
            "Product data is not available.",
            300,
        )

    plot = dataframe.copy()

    plot[value_column] = pd.to_numeric(
        plot[value_column],
        errors="coerce",
    ).fillna(0.0)

    plot = plot.sort_values(
        by=value_column,
        ascending=True,
    )

    labels = [
        str(value)
        for value in plot["item_name"].tolist()
    ]

    values = [
        safe_float(value)
        for value in plot[value_column].tolist()
    ]

    if currency:
        text_values = [
            format_currency(value)
            for value in values
        ]
        hover = (
            f"<b>%{{y}}</b><br>"
            f"{value_label}: ₹%{{x:,.0f}}"
            "<extra></extra>"
        )
    else:
        text_values = [
            format_number(value)
            for value in values
        ]
        hover = (
            f"<b>%{{y}}</b><br>"
            f"{value_label}: %{{x:,.1f}}"
            "<extra></extra>"
        )

    axis_color = AXIS_LIGHT if dark else TEXT

    figure = go.Figure(
        go.Bar(
            x=values,
            y=labels,
            orientation="h",
            marker_color=AQUA,
            text=text_values,
            textposition="outside",
            textfont={
                "family": "Arial, sans-serif",
                "size": 10,
                "color": axis_color,
            },
            cliponaxis=False,
            hovertemplate=hover,
        )
    )

    figure.update_layout(
        **_chart_layout(300, dark=dark)
    )

    figure.update_xaxes(
        tickprefix="₹" if currency else "",
        tickformat="~s",
        tickfont={
            "family": "Arial, sans-serif",
            "size": 10,
            "color": axis_color,
        },
    )

    figure.update_yaxes(
        showgrid=False,
        autorange=True,
        automargin=True,
        tickfont={
            "family": "Arial, sans-serif",
            "size": 10,
            "color": axis_color,
        },
    )

    return figure


# ============================================================
# PRODUCT PERFORMANCE
# ============================================================

def render_product_performance(
    engine: ProductEngine,
) -> None:
    """Render top product performance rankings."""

    top_selling = engine.top_selling_products(5)
    top_revenue = engine.highest_revenue_products(5)

    st.markdown(
        '<div class="product-chart-grid">',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<article class="product-chart-card">'
        '<div class="product-chart-header">'
        '<div>'
        '<div class="product-chart-title">'
        'Top Selling Products'
        '</div>'
        '<div class="product-chart-description">'
        'Products generating the highest unit volume'
        '</div>'
        '</div>'
        '<div class="product-chart-badge">Units</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.plotly_chart(
        _product_bar_figure(
            top_selling,
            "quantity",
            "Units",
        ),
        use_container_width=True,
        config={"displayModeBar": False},
    )

    st.markdown(
        '</article>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<article class="product-chart-card">'
        '<div class="product-chart-header">'
        '<div>'
        '<div class="product-chart-title">'
        'Top Revenue Products'
        '</div>'
        '<div class="product-chart-description">'
        'Products generating the highest gross revenue'
        '</div>'
        '</div>'
        '<div class="product-chart-badge">Revenue</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.plotly_chart(
        _product_bar_figure(
            top_revenue,
            "revenue",
            "Revenue",
            currency=True,
        ),
        use_container_width=True,
        config={"displayModeBar": False},
    )

    st.markdown(
        '</article>'
        '</div>',
        unsafe_allow_html=True,
    )


# ============================================================
# RETURNS
# ============================================================

def render_returns(
    engine: ProductEngine,
) -> None:
    """Render return risk analytics."""

    returned = engine.highest_returned_products(5)
    return_value = engine.highest_return_value_products(5)
    return_rate = engine.return_rate_by_product(5)

    st.markdown(
        '<div class="product-chart-grid">',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<article class="product-chart-card">'
        '<div class="product-chart-header">'
        '<div>'
        '<div class="product-chart-title">'
        'Most Returned Products'
        '</div>'
        '<div class="product-chart-description">'
        'Products generating the highest returned quantity'
        '</div>'
        '</div>'
        '<div class="product-chart-badge">Returns</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.plotly_chart(
        _product_bar_figure(
            returned,
            "returned_quantity",
            "Returned units",
            dark=True,
        ),
        use_container_width=True,
        config={"displayModeBar": False},
    )

    st.markdown(
        '</article>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<article class="product-chart-card">'
        '<div class="product-chart-header">'
        '<div>'
        '<div class="product-chart-title">'
        'Return Value Impact'
        '</div>'
        '<div class="product-chart-description">'
        'Products with the highest value of returned sales'
        '</div>'
        '</div>'
        '<div class="product-chart-badge">Value</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.plotly_chart(
        _product_bar_figure(
            return_value,
            "returned_value",
            "Returned value",
            currency=True,
            dark=True,
        ),
        use_container_width=True,
        config={"displayModeBar": False},
    )

    st.markdown(
        '</article>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<article class="product-chart-card">'
        '<div class="product-chart-header">'
        '<div>'
        '<div class="product-chart-title">'
        'Highest Return Rate'
        '</div>'
        '<div class="product-chart-description">'
        'Returned units as a percentage of units sold'
        '</div>'
        '</div>'
        '<div class="product-chart-badge">Rate</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    figure = _product_bar_figure(
        return_rate,
        "return_rate",
        "Return rate",
        dark=True,
    )

    figure.update_xaxes(
        ticksuffix="%",
        tickformat=".0f",
    )

    st.plotly_chart(
        figure,
        use_container_width=True,
        config={"displayModeBar": False},
    )

    st.markdown(
        '</article>',
        unsafe_allow_html=True,
    )


# ============================================================
# GROWTH
# ============================================================

def _growth_dataframe(
    engine: ProductEngine,
) -> pd.DataFrame:
    """Build current-versus-previous month product growth."""

    monthly = engine.monthly_product_sales.copy()

    if monthly.empty or "month" not in monthly.columns:
        return pd.DataFrame()

    months = sorted(
        {
            str(value)
            for value in monthly["month"].dropna().tolist()
        }
    )

    if len(months) < 2:
        return pd.DataFrame()

    current_month = months[-1]
    previous_month = months[-2]

    current = monthly[
        monthly["month"].astype(str).eq(current_month)
    ].copy()

    previous = monthly[
        monthly["month"].astype(str).eq(previous_month)
    ].copy()

    previous = previous.rename(
        columns={
            "quantity": "previous_quantity",
            "revenue": "previous_revenue",
        }
    )

    current = current.merge(
        previous[
            [
                "item_code",
                "previous_quantity",
                "previous_revenue",
            ]
        ],
        on="item_code",
        how="left",
    )

    current["previous_quantity"] = (
        pd.to_numeric(
            current["previous_quantity"],
            errors="coerce",
        )
        .fillna(0.0)
    )

    current["previous_revenue"] = (
        pd.to_numeric(
            current["previous_revenue"],
            errors="coerce",
        )
        .fillna(0.0)
    )

    current["quantity"] = pd.to_numeric(
        current["quantity"],
        errors="coerce",
    ).fillna(0.0)

    current["revenue"] = pd.to_numeric(
        current["revenue"],
        errors="coerce",
    ).fillna(0.0)

    current["quantity_change"] = (
        current["quantity"]
        - current["previous_quantity"]
    )

    current["revenue_change"] = (
        current["revenue"]
        - current["previous_revenue"]
    )

    current["quantity_growth"] = (
        current["quantity_change"]
        / current["previous_quantity"]
        * 100.0
    )

    current["quantity_growth"] = (
        current["quantity_growth"]
        .replace([float("inf"), -float("inf")], 0.0)
        .fillna(0.0)
    )

    current["revenue_growth"] = (
        current["revenue_change"]
        / current["previous_revenue"]
        * 100.0
    )

    current["revenue_growth"] = (
        current["revenue_growth"]
        .replace([float("inf"), -float("inf")], 0.0)
        .fillna(0.0)
    )

    return current


def _growth_chart(
    dataframe: pd.DataFrame,
    value_column: str,
    label: str,
    suffix: str = "",
    currency: bool = False,
) -> go.Figure:
    """Build a growth ranking chart."""

    if dataframe.empty:
        return _empty_figure(
            "Growth data is not available.",
            300,
        )

    plot = dataframe.head(5).copy()

    plot[value_column] = pd.to_numeric(
        plot[value_column],
        errors="coerce",
    ).fillna(0.0)

    plot = plot.sort_values(
        by=value_column,
        ascending=True,
    )

    values = [
        safe_float(value)
        for value in plot[value_column].tolist()
    ]

    labels = [
        str(value)
        for value in plot["item_name"].tolist()
    ]

    if currency:
        texts = [
            format_currency(value)
            for value in values
        ]
        hover = (
            f"<b>%{{y}}</b><br>{label}: ₹%{{x:,.0f}}"
            "<extra></extra>"
        )
    else:
        texts = [
            f"{value:+.1f}{suffix}"
            for value in values
        ]
        hover = (
            f"<b>%{{y}}</b><br>{label}: %{{x:.2f}}{suffix}"
            "<extra></extra>"
        )

    figure = go.Figure(
        go.Bar(
            x=values,
            y=labels,
            orientation="h",
            marker_color=AQUA,
            text=texts,
            textposition="outside",
            textfont={
                "family": "Arial, sans-serif",
                "size": 10,
                "color": TEXT,
            },
            cliponaxis=False,
            hovertemplate=hover,
        )
    )

    figure.update_layout(
        **_chart_layout(300)
    )

    figure.update_xaxes(
        ticksuffix=suffix,
        tickformat=".0f",
    )

    figure.update_yaxes(
        showgrid=False,
        automargin=True,
    )

    return figure


def render_growth(
    engine: ProductEngine,
) -> None:
    """Render month-over-month product growth."""

    growth = _growth_dataframe(engine)

    if growth.empty:
        st.info(
            "At least two monthly product periods are required "
            "to display growth analytics."
        )
        return

    valid_growth = growth[
        growth["previous_quantity"] >= 20
    ].copy()

    fastest = (
        valid_growth
        .nlargest(5, "quantity_growth")
        .reset_index(drop=True)
    )

    declining = (
        valid_growth
        .nsmallest(5, "quantity_growth")
        .reset_index(drop=True)
    )

    volume = (
        growth
        .nlargest(5, "quantity_change")
        .reset_index(drop=True)
    )

    revenue = (
        growth
        .nlargest(5, "revenue_change")
        .reset_index(drop=True)
    )

    charts = [
        (
            "Fastest Growing",
            "Highest percentage increase in units sold",
            _growth_chart(
                fastest,
                "quantity_growth",
                "Growth",
                "%",
            ),
        ),
        (
            "Fastest Declining",
            "Largest percentage decline in units sold",
            _growth_chart(
                declining,
                "quantity_growth",
                "Decline",
                "%",
            ),
        ),
        (
            "Biggest Volume Growth",
            "Largest increase in units sold",
            _growth_chart(
                volume,
                "quantity_change",
                "Unit change",
            ),
        ),
        (
            "Biggest Revenue Growth",
            "Largest increase in revenue",
            _growth_chart(
                revenue,
                "revenue_change",
                "Revenue change",
                currency=True,
            ),
        ),
    ]

    for index in range(0, len(charts), 2):
        st.markdown(
            '<div class="product-chart-grid">',
            unsafe_allow_html=True,
        )

        for title, description, figure in charts[index:index + 2]:
            st.markdown(
                '<article class="product-chart-card">'
                '<div class="product-chart-header">'
                '<div>'
                f'<div class="product-chart-title">'
                f'{escape(title)}'
                '</div>'
                f'<div class="product-chart-description">'
                f'{escape(description)}'
                '</div>'
                '</div>'
                '<div class="product-chart-badge">MoM</div>'
                '</div>',
                unsafe_allow_html=True,
            )

            st.plotly_chart(
                figure,
                use_container_width=True,
                config={"displayModeBar": False},
            )

            st.markdown(
                '</article>',
                unsafe_allow_html=True,
            )

        st.markdown(
            '</div>',
            unsafe_allow_html=True,
        )


# ============================================================
# CONTRIBUTION + ABC
# ============================================================

def _pareto_figure(
    contribution: pd.DataFrame,
) -> go.Figure:
    """Build cumulative net-revenue contribution chart."""

    if contribution.empty:
        return _empty_figure(
            "Contribution data is not available.",
            330,
        )

    plot = contribution.copy().head(50)

    x_values = list(range(1, len(plot) + 1))

    cumulative = [
        safe_float(value)
        for value in plot[
            "cumulative_net_revenue"
        ].tolist()
    ]

    figure = go.Figure()

    figure.add_trace(
        go.Scatter(
            x=x_values,
            y=cumulative,
            mode="lines+markers",
            line={
                "color": AQUA,
                "width": 2.5,
            },
            marker={
                "color": AQUA,
                "size": 5,
            },
            hovertemplate=(
                "Product rank: %{x}<br>"
                "Cumulative net revenue: %{y:.2f}%"
                "<extra></extra>"
            ),
        )
    )

    figure.add_hline(
        y=80,
        line_dash="dash",
        line_color=AXIS_LIGHT,
        annotation_text="80%",
        annotation_position="top left",
        annotation_font={
            "family": "Arial, sans-serif",
            "size": 10,
            "color": AXIS_LIGHT,
        },
    )

    figure.update_layout(
        **_chart_layout(330, dark=True)
    )

    figure.update_xaxes(
        title_text="Products ranked by net revenue",
        title_font={
            "family": "Arial, sans-serif",
            "size": 11,
            "color": AXIS_LIGHT,
        },
        tickfont={
            "family": "Arial, sans-serif",
            "size": 10,
            "color": AXIS_LIGHT,
        },
        showgrid=False,
        zeroline=False,
    )

    figure.update_yaxes(
        title_text="Cumulative net revenue",
        title_font={
            "family": "Arial, sans-serif",
            "size": 11,
            "color": AXIS_LIGHT,
        },
        tickfont={
            "family": "Arial, sans-serif",
            "size": 10,
            "color": AXIS_LIGHT,
        },
        ticksuffix="%",
        range=[0, 105],
        showgrid=True,
        gridcolor=GRID_DARK,
        zeroline=False,
    )

    return figure


def render_contribution(
    engine: ProductEngine,
) -> None:
    """Render Pareto and ABC product contribution."""

    contribution = engine.product_contribution
    abc = engine.abc_summary()

    st.markdown(
        '<article class="product-chart-card">'
        '<div class="product-chart-header">'
        '<div>'
        '<div class="product-chart-title">'
        'Cumulative Net Revenue Contribution'
        '</div>'
        '<div class="product-chart-description">'
        'Products ranked by net revenue after returns'
        '</div>'
        '</div>'
        '<div class="product-chart-badge">Pareto</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.plotly_chart(
        _pareto_figure(contribution),
        use_container_width=True,
        config={"displayModeBar": False},
    )

    st.markdown(
        '</article>',
        unsafe_allow_html=True,
    )

    cards = []

    for abc_class in ("A", "B", "C"):
        row = abc[
            abc["abc_class"].astype(str).eq(abc_class)
        ]

        if row.empty:
            count = 0.0
            share = 0.0
        else:
            count = safe_float(
                row.iloc[0]["product_count"]
            )
            share = safe_float(
                row.iloc[0]["net_revenue_share"]
            )

        cards.append(
            (
                '<div class="product-abc-card">'
                f'<div class="product-abc-label">'
                f'CLASS {abc_class}'
                '</div>'
                f'<div class="product-abc-value">'
                f'{format_number(count)}'
                '</div>'
                '<div class="product-abc-note">'
                'products contributing '
                f'<strong>{format_percentage(share)}</strong>'
                ' of net revenue'
                '</div>'
                '</div>'
            )
        )

    st.markdown(
        '<div class="product-abc-grid">'
        + "".join(cards)
        + '</div>',
        unsafe_allow_html=True,
    )


# ============================================================
# PRODUCT EXPLORER
# ============================================================

def render_product_explorer(
    engine: ProductEngine,
) -> None:
    """Render product lookup and selected-product profile."""

    summary = engine.product_summary.copy()

    if summary.empty:
        st.info("No product data is available.")
        return

    product_names = (
        summary["item_name"]
        .dropna()
        .astype(str)
        .str.strip()
        .tolist()
    )

    product_names = sorted(
        {
            name
            for name in product_names
            if name
        }
    )

    if not product_names:
        st.info("No products are available.")
        return

    selected_name = st.selectbox(
        "Search product",
        product_names,
        index=0,
        key="product_dashboard_selector",
    )

    selected_rows = summary[
        summary["item_name"].astype(str).eq(selected_name)
    ]

    if selected_rows.empty:
        st.info("Product profile is not available.")
        return

    selected = selected_rows.iloc[0]

    item_code = str(
        selected.get("item_code", "")
    )

    contribution_rows = engine.contribution_by_product(
        item_code
    )

    contribution = (
        contribution_rows.iloc[0]
        if not contribution_rows.empty
        else None
    )

    abc_class = engine.class_of_product(
        item_code
    ) or "C"

    quantity = safe_float(
        selected.get("quantity", 0)
    )

    revenue = safe_float(
        selected.get("revenue", 0)
    )

    returned_quantity = safe_float(
        selected.get("returned_quantity", 0)
    )

    returned_value = safe_float(
        selected.get("returned_value", 0)
    )

    net_revenue = (
        safe_float(contribution["net_revenue"])
        if contribution is not None
        else revenue - returned_value
    )

    return_rate = safe_float(
        selected.get("return_rate", 0)
    )

    revenue_share = (
        safe_float(
            contribution["net_revenue_contribution"]
        )
        if contribution is not None
        else 0.0
    )

    quantity_share = (
        safe_float(
            contribution["quantity_contribution"]
        )
        if contribution is not None
        else 0.0
    )

    profile_html = (
        '<div class="product-profile">'
        '<div class="product-profile-head">'
        '<div>'
        '<div class="product-profile-eyebrow">'
        'Selected Product'
        '</div>'
        '<div class="product-profile-title">'
        f'{escape(selected_name)}'
        '</div>'
        '</div>'
        '<div class="product-profile-class">'
        f'{escape(abc_class)}'
        '</div>'
        '</div>'

        '<div class="product-profile-metrics">'

        '<div class="product-profile-metric">'
        '<div class="product-profile-label">Units Sold</div>'
        '<div class="product-profile-value">'
        f'{escape(format_number(quantity))}'
        '</div>'
        '</div>'

        '<div class="product-profile-metric">'
        '<div class="product-profile-label">Net Revenue</div>'
        '<div class="product-profile-value">'
        f'{escape(format_currency(net_revenue))}'
        '</div>'
        '</div>'

        '<div class="product-profile-metric">'
        '<div class="product-profile-label">Return Rate</div>'
        '<div class="product-profile-value">'
        f'{escape(format_percentage(return_rate))}'
        '</div>'
        '</div>'

        '<div class="product-profile-metric">'
        '<div class="product-profile-label">Revenue Share</div>'
        '<div class="product-profile-value">'
        f'{escape(format_percentage(revenue_share))}'
        '</div>'
        '</div>'

        '</div>'

        '<div class="product-insight">'
        '<div class="product-insight-icon">↗</div>'
        '<div>'
        '<div class="product-insight-label">'
        'Product Health'
        '</div>'
        f'This product contributes '
        f'<span class="product-insight-value">'
        f'{escape(format_percentage(revenue_share))}'
        '</span> '
        'of total net revenue and '
        f'<span class="product-insight-value">'
        f'{escape(format_percentage(quantity_share))}'
        '</span> '
        'of total quantity.'
        '</div>'
        '</div>'

        '</div>'
    )

    st.markdown(
        profile_html,
        unsafe_allow_html=True,
    )

    monthly = engine.monthly_product_performance(
        item_code
    )

    if not monthly.empty:
        st.markdown(
            '<article class="product-chart-card" '
            'style="margin-top:18px;">'
            '<div class="product-chart-header">'
            '<div>'
            '<div class="product-chart-title">'
            'Monthly Product Performance'
            '</div>'
            '<div class="product-chart-description">'
            'Revenue movement across historical monthly periods'
            '</div>'
            '</div>'
            '<div class="product-chart-badge">Monthly</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        figure = go.Figure(
            go.Scatter(
                x=monthly["month"].astype(str).tolist(),
                y=[
                    safe_float(value)
                    for value in monthly["revenue"].tolist()
                ],
                mode="lines+markers",
                line={
                    "color": AQUA,
                    "width": 2.5,
                },
                marker={
                    "color": AQUA,
                    "size": 5,
                },
                fill="tozeroy",
                fillcolor="rgba(17,175,193,0.10)",
                hovertemplate=(
                    "<b>%{x}</b><br>"
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
        )

        figure.update_yaxes(
            tickprefix="₹",
            tickformat="~s",
        )

        st.plotly_chart(
            figure,
            use_container_width=True,
            config={"displayModeBar": False},
        )

        st.markdown(
            '</article>',
            unsafe_allow_html=True,
        )

    _ = returned_quantity
    _ = returned_value


# ============================================================
# MAIN DASHBOARD
# ============================================================

def render_product_dashboard(
    on_back: Callable[[], None] | None = None,
) -> None:
    """Render the Product Intelligence dashboard."""

    del on_back

    inject_product_css()

    render_brand()
    render_navigation("products")

    st.markdown(
        '<a href="?page=home" '
        'target="_self" '
        'class="product-floating-home" '
        'aria-label="Back to Home">'
        '<span class="product-floating-home-icon">⌂</span>'
        '<span class="product-floating-home-text">'
        'BACK TO HOME'
        '</span>'
        '</a>',
        unsafe_allow_html=True,
    )

    try:
        engine = ProductEngine()
    except (
        KeyError,
        TypeError,
        ValueError,
    ) as exc:
        st.error(
            f"Product engine could not be initialized: {exc}"
        )
        return

    latest_date = SalesQueries.get_latest_posting_date()

    st.markdown(
        '<div class="product-intelligence-page">',
        unsafe_allow_html=True,
    )

    render_header(latest_date)
    render_kpis(engine)

    with st.container(key="product_performance_section"):
        render_section_heading(
            "Product Performance",
            "What is selling?",
            (
                "Compare the products generating the highest "
                "unit volume and gross revenue."
            ),
            "↗",
        )
        render_product_performance(engine)

    with st.container(key="product_returns_section"):
        render_section_heading(
            "Returns & Product Risk",
            "Which products are creating return pressure?",
            (
                "Identify products with the highest returned volume, "
                "return value and return rates."
            ),
            "!",
            dark=True,
        )
        render_returns(engine)

    with st.container(key="product_growth_section"):
        render_section_heading(
            "Product Growth",
            "What is accelerating or declining?",
            (
                "Compare current monthly product performance with "
                "the previous period."
            ),
            "↗",
        )
        render_growth(engine)

    with st.container(key="product_contribution_section"):
        render_section_heading(
            "Product Contribution",
            "Which products actually matter?",
            (
                "Understand net revenue concentration and "
                "ABC product importance."
            ),
            "▥",
            dark=True,
        )
        render_contribution(engine)

    with st.container(key="product_explorer_section"):
        render_section_heading(
            "Product Explorer",
            "Drill into an individual product",
            (
                "Select a product to view its performance, returns, "
                "contribution and monthly history."
            ),
            "⌕",
        )
        render_product_explorer(engine)

    st.markdown(
        '</div>',
        unsafe_allow_html=True,
    )


def main() -> None:
    """Render the AQVASTAR Product Intelligence dashboard."""

    apply_theme(
        "AQVASTAR | Product Intelligence"
    )

    render_product_dashboard()


if __name__ == "__main__":
    main()
