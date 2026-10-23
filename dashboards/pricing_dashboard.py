"""
AQVASTAR Sales Intelligence Platform.

Pricing Intelligence Dashboard.

Dashboard orchestration only. Pricing business logic remains in
PricingEngine. This dashboard follows the same visual structure as the
Regional and Sales Performance dashboards.
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
from engines.pricing_engine import PricingEngine
from database.queries import SalesQueries


# ============================================================
# DESIGN SYSTEM
# ============================================================

BACKGROUND = "#F3F8FA"
WHITE = "#FFFFFF"
TEXT = "#102631"
MUTED = "#617982"
BORDER = "#D9E8EC"

DEEP = "#063D4A"
DEEP_2 = "#075567"
AQUA_SOFT = "#E8F7F9"
AQUA_LIGHT = "#CDEFF2"

AXIS_LIGHT = "#D8F5F7"
GRID_DARK = "rgba(216,245,247,0.55)"
GRID_LIGHT = "#DCEBED"


# ============================================================
# FORMATTERS
# ============================================================


def safe_float(value: object, default: float = 0.0) -> float:
    """Convert arbitrary values to float safely."""
    try:
        numeric_value = float(value)  # type: ignore[arg-type]
        if pd.isna(numeric_value):
            return default
        return numeric_value
    except (TypeError, ValueError):
        return default


def safe_text(value: object, default: str = "N/A") -> str:
    """Convert arbitrary values to readable text."""
    if value is None:
        return default

    text = str(value).strip()
    return text if text else default


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
        return f"{sign}₹{absolute_value / 1_000:.1f}K"

    return f"{sign}₹{absolute_value:,.0f}"


def format_number(value: float) -> str:
    """Format dashboard counts and quantities."""
    numeric_value = float(value)

    if numeric_value.is_integer():
        return f"{int(numeric_value):,}"

    return f"{numeric_value:,.1f}"


def format_percentage(value: float) -> str:
    """Format a percentage."""
    return f"{float(value):.1f}%"


# ============================================================
# CSS
# ============================================================


def inject_pricing_css() -> None:
    """Inject the Pricing Intelligence visual system."""

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
           BACK TO HOME
           ================================================== */

        .pricing-floating-home {{
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

        .pricing-floating-home:hover {{
            transform: translateY(-3px);
            border-color: {AQUA};
            box-shadow: 0 16px 36px rgba(4,62,76,0.22);
            color: #087C8A !important;
        }}

        .pricing-floating-home-icon {{
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

        .pricing-floating-home-text {{
            white-space: nowrap;
        }}

        /* ==================================================
           HERO
           ================================================== */

        .pricing-hero {{
            position: relative;
            overflow: hidden;

            min-height: 176px;
            padding: 2rem 2.25rem;
            margin: 0.35rem 0 1rem;

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

            box-shadow: 0 14px 34px rgba(5,60,74,0.14);
        }}

        .pricing-hero-content {{
            position: relative;
            z-index: 3;
            max-width: 760px;
        }}

        .pricing-hero-eyebrow {{
            color: #3BD0D8;
            font-size: 0.60rem;
            font-weight: 800;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            margin-bottom: 0.58rem;
        }}

        .pricing-hero-title {{
            color: #FFFFFF;
            font-size: clamp(1.85rem, 3.1vw, 3rem);
            line-height: 1.02;
            font-weight: 800;
            letter-spacing: -0.045em;
            margin-bottom: 0.62rem;
        }}

        .pricing-hero-asof {{
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

        .pricing-hero-asof strong {{
            display: block;

            color: #FFFFFF;

            font-size: 0.75rem;

            margin-top: 0.15rem;
        }}

        .pricing-hero-description {{
            max-width: 620px;
            color: rgba(255,255,255,0.76);
            font-size: 0.76rem;
            line-height: 1.45;
        }}

        .pricing-hero-ring {{
            position: absolute;
            border: 1px solid rgba(255,255,255,0.13);
            border-radius: 50%;
            pointer-events: none;
        }}

        /* ==================================================
           SECTIONS
           ================================================== */

        .st-key-pricing_performance_section,
        .st-key-pricing_discount_section,
        .st-key-pricing_distribution_section,
        .st-key-pricing_effectiveness_section,
        .st-key-pricing_lookup_section {{
            position: relative;
            overflow: hidden;

            border-radius: 20px;
            margin-top: 1.05rem;
            margin-bottom: 1.45rem;

            padding: 1.25rem 1.35rem 2.05rem;
        }}

        .st-key-pricing_performance_section,
        .st-key-pricing_distribution_section {{
            background: linear-gradient(145deg,#064652 0%,#0B6C79 100%);
            box-shadow: 0 16px 38px rgba(5,57,70,0.13);
        }}

        .st-key-pricing_discount_section,
        .st-key-pricing_effectiveness_section,
        .st-key-pricing_lookup_section {{
            background: linear-gradient(145deg,#F7FCFD 0%,#EAF7F9 100%);
            border: 1px solid #D8EAEE;
            box-shadow: 0 12px 32px rgba(5,57,70,0.07);
        }}

        /* ==================================================
           SECTION HEADING
           ================================================== */

        .pricing-section-heading {{
            display: flex;
            align-items: flex-start;
            gap: 16px;
            margin-bottom: 1.15rem;
        }}

        .pricing-section-icon {{
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

            box-shadow: 0 8px 18px rgba(17,175,193,0.22);
        }}

        .pricing-section-eyebrow {{
            color: #0794A5;
            font-size: 0.60rem;
            font-weight: 800;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            margin-bottom: 0.28rem;
        }}

        .pricing-section-title {{
            color: {TEXT};
            font-size: 1.32rem;
            font-weight: 800;
            letter-spacing: -0.035em;
            line-height: 1.1;
        }}

        .pricing-section-description {{
            color: {MUTED};
            font-size: 0.73rem;
            line-height: 1.45;
            margin-top: 0.32rem;
        }}

        .pricing-section-heading.dark .pricing-section-eyebrow {{
            color: #3BD0D8;
        }}

        .pricing-section-heading.dark .pricing-section-title {{
            color: #FFFFFF;
        }}

        .pricing-section-heading.dark .pricing-section-description {{
            color: rgba(255,255,255,0.70);
        }}

        /* ==================================================
           EXECUTIVE KPIs
           ================================================== */

        .pricing-executive {{
            margin: 0.85rem 0 1.15rem;
            padding: 0.15rem 0 0.05rem;
        }}

        .pricing-executive-kicker {{
            color: #11899A;
            font-size: 0.64rem;
            font-weight: 800;
            letter-spacing: 0.16em;
            text-transform: uppercase;
            margin-bottom: 0.18rem;
        }}

        .pricing-executive-title {{
            color: {TEXT};
            font-size: 1.32rem;
            line-height: 1.15;
            font-weight: 800;
            letter-spacing: -0.025em;
            margin-bottom: 0.18rem;
        }}

        .pricing-executive-description {{
            color: {MUTED};
            font-size: 0.74rem;
            line-height: 1.4;
            margin-bottom: 0.68rem;
        }}

        .pricing-kpi-grid {{
            display: grid;
            grid-template-columns: repeat(5,minmax(0,1fr));
            gap: 0.65rem;
        }}

        .pricing-kpi {{
            min-width: 0;
            padding: 0.78rem 0.82rem;
            border: 1px solid #D6E7EB;
            border-radius: 13px;
            background: #FFFFFF;
            box-shadow: 0 6px 18px rgba(7,63,76,0.045);
        }}

        .pricing-kpi-label {{
            color: #198C9B;
            font-size: 0.57rem;
            font-weight: 800;
            letter-spacing: 0.10em;
            text-transform: uppercase;
        }}

        .pricing-kpi-value {{
            color: {TEXT};
            font-size: 1.28rem;
            line-height: 1.05;
            font-weight: 800;
            letter-spacing: -0.025em;
            margin: 0.30rem 0 0.16rem;
        }}

        .pricing-kpi-note {{
            color: {MUTED};
            font-size: 0.57rem;
            line-height: 1.3;
        }}

        /* ==================================================
           CHARTS
           ================================================== */

        .pricing-chart-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 18px;
            margin-bottom: 18px;
        }}

        .pricing-chart-card {{
            min-width: 0;
            background: #FFFFFF;
            border: 1px solid #E0EAED;
            border-radius: 18px;
            box-shadow: 0 10px 28px rgba(5,57,70,0.06);
            overflow: hidden;
        }}

        .dark-card {{
            background: rgba(255,255,255,0.035);
            border-color: rgba(255,255,255,0.10);
        }}

        .pricing-chart-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            min-height: 62px;
            padding: 14px 18px 10px;
            border-bottom: 1px solid #EDF2F3;
        }}

        .dark-card .pricing-chart-header {{
            border-bottom-color: rgba(255,255,255,0.10);
        }}

        .pricing-chart-title {{
            color: {TEXT};
            font-size: 0.96rem;
            font-weight: 800;
            letter-spacing: -0.02em;
        }}

        .dark-card .pricing-chart-title {{
            color: #FFFFFF;
        }}

        .pricing-chart-description {{
            color: #71878E;
            font-size: 0.67rem;
            margin-top: 3px;
        }}

        .dark-card .pricing-chart-description {{
            color: rgba(255,255,255,0.64);
        }}

        .pricing-chart-badge {{
            padding: 6px 9px;
            border-radius: 8px;
            background: #E8F7F9;
            color: #087C8A;
            font-size: 0.61rem;
            font-weight: 800;
        }}

        .dark-card .pricing-chart-badge {{
            background: rgba(255,255,255,0.10);
            color: #8DE5EA;
        }}

        /* ==================================================
           TABLE / PROFILE
           ================================================== */

        .pricing-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.70rem;
        }}

        .pricing-table th {{
            padding: 10px 12px;
            text-align: left;
            color: #6A858D;
            font-size: 0.58rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            border-bottom: 1px solid #E2ECEF;
        }}

        .pricing-table td {{
            padding: 10px 12px;
            color: {TEXT};
            border-bottom: 1px solid #EDF3F4;
        }}

        .pricing-table tr:last-child td {{
            border-bottom: none;
        }}

        .pricing-rank {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 25px;
            height: 25px;
            border-radius: 8px;
            background: #E8F7F9;
            color: #087C8A;
            font-weight: 800;
        }}

        .pricing-profile {{
            padding: 1rem;
            border: 1px solid #D7E9ED;
            border-radius: 16px;
            background: #FFFFFF;
            box-shadow: 0 8px 24px rgba(5,57,70,0.05);
        }}

        .pricing-profile-title {{
            color: {TEXT};
            font-size: 1rem;
            font-weight: 800;
            margin-bottom: 0.15rem;
        }}

        .pricing-profile-subtitle {{
            color: {MUTED};
            font-size: 0.68rem;
            margin-bottom: 1rem;
        }}

        .pricing-profile-grid {{
            display: grid;
            grid-template-columns: repeat(4,minmax(0,1fr));
            border: 1px solid #E0EAED;
            border-radius: 12px;
            overflow: hidden;
        }}

        .pricing-profile-metric {{
            padding: 0.8rem;
            border-right: 1px solid #E0EAED;
        }}

        .pricing-profile-metric:last-child {{
            border-right: none;
        }}

        .pricing-profile-label {{
            color: #71878E;
            font-size: 0.57rem;
            font-weight: 800;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }}

        .pricing-profile-value {{
            color: {TEXT};
            font-size: 0.95rem;
            font-weight: 800;
            margin-top: 0.25rem;
        }}

        .pricing-empty {{
            padding: 1.5rem;
            border: 1px dashed #BFD9DE;
            border-radius: 14px;
            color: {MUTED};
            text-align: center;
            font-size: 0.75rem;
            background: rgba(255,255,255,0.65);
        }}

        @media (max-width: 900px) {{
            .pricing-kpi-grid {{
                grid-template-columns: repeat(2,minmax(0,1fr));
            }}

            .pricing-chart-grid {{
                grid-template-columns: 1fr;
            }}

            .pricing-profile-grid {{
                grid-template-columns: repeat(2,minmax(0,1fr));
            }}

            .pricing-profile-metric:nth-child(2) {{
                border-right: none;
            }}
        }}

        @media (max-width: 650px) {{
            [data-testid="stMainBlockContainer"] {{
                padding-left: 0.65rem;
                padding-right: 0.65rem;
            }}

            .pricing-hero {{
                min-height: 150px;
                padding: 1.4rem 1.2rem;
            }}

            .pricing-hero-title {{
                font-size: 1.75rem;
            }}

            .pricing-hero-asof {{
                right: 20px;
                top: 20px;
            }}

            .pricing-floating-home {{
                left: 12px;
                bottom: 14px;
                min-height: 44px;
                padding-right: 13px;
            }}

            .pricing-kpi-grid {{
                grid-template-columns: 1fr;
            }}

            .pricing-profile-grid {{
                grid-template-columns: 1fr;
            }}

            .pricing-profile-metric,
            .pricing-profile-metric:nth-child(2) {{
                border-right: none;
                border-bottom: 1px solid #E0EAED;
            }}

            .pricing-profile-metric:last-child {{
                border-bottom: none;
            }}
        }}

        </style>
        """,
        unsafe_allow_html=True,
    )


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
    """Render a consistent intelligence section heading."""

    section_class = " dark" if dark else ""

    html = (
        f'<div class="pricing-section-heading{section_class}">'
        f'<div class="pricing-section-icon">{icon}</div>'
        "<div>"
        f'<div class="pricing-section-eyebrow">{escape(eyebrow)}</div>'
        f'<div class="pricing-section-title">{escape(title)}</div>'
        f'<div class="pricing-section-description">'
        f"{escape(description)}"
        "</div>"
        "</div>"
        "</div>"
    )

    st.markdown(html, unsafe_allow_html=True)


# ============================================================
# HERO
# ============================================================


def render_header(
    latest_date: pd.Timestamp | None,
) -> None:
    """Render the Pricing Intelligence hero."""

    date_text = (
        latest_date.strftime("%d %b %Y")
        if latest_date is not None
        else "No sales date available"
    )

    html = (
        '<section class="pricing-hero">'
        '<div class="pricing-hero-ring" '
        'style="width:330px;height:330px;right:-100px;bottom:-205px;"></div>'
        '<div class="pricing-hero-ring" '
        'style="width:460px;height:460px;right:-165px;bottom:-285px;opacity:.62;"></div>'
        '<div class="pricing-hero-ring" '
        'style="width:190px;height:190px;right:80px;top:-110px;opacity:.50;"></div>'
        '<div class="pricing-hero-content">'
        '<div class="pricing-hero-eyebrow">Pricing Intelligence</div>'
        '<div class="pricing-hero-title">'
        'Understand price.<br>'
        'See where discounts change revenue.'
        '</div>'
        '<div class="pricing-hero-description">'
        'Track selling prices, discount intensity, price realization and '
        'the relationship between pricing decisions and sales outcomes.'
        '</div>'
        '</div>'
        '<div class="pricing-hero-asof">'
        'Data as of:'
        f'<strong>{date_text}</strong>'
        '</div>'
        "</section>"
    )

    st.markdown(html, unsafe_allow_html=True)


# ============================================================
# EXECUTIVE KPIs
# ============================================================


def _summary_value(summary: pd.DataFrame, metric: str) -> float:
    """Read a numeric metric from pricing_summary()."""

    if summary.empty:
        return 0.0

    rows = summary[
        summary["Metric"].astype(str).eq(metric)
    ]

    if rows.empty:
        return 0.0

    return safe_float(rows.iloc[0]["Value"])


def render_executive_kpis(engine: PricingEngine) -> None:
    """Render five executive pricing KPIs."""

    try:
        summary = engine.pricing_summary()
    except (KeyError, TypeError, ValueError):
        summary = pd.DataFrame()

    revenue = _summary_value(summary, "Revenue")
    quantity = _summary_value(summary, "Quantity")
    orders = _summary_value(summary, "Orders")
    products = _summary_value(summary, "Products")
    discount = _summary_value(summary, "Average Discount")

    average_order_value = revenue / orders if orders else 0.0
    average_selling_price = revenue / quantity if quantity else 0.0

    metrics = [
        (
            "REVENUE",
            format_currency(revenue),
            "Recorded sales revenue",
        ),
        (
            "ORDERS",
            format_number(orders),
            "Distinct sales invoices",
        ),
        (
            "AVG SELLING PRICE",
            format_currency(average_selling_price),
            "Revenue per unit",
        ),
        (
            "AVG DISCOUNT",
            format_percentage(discount),
            "Quantity-weighted discount",
        ),
        (
            "AVG ORDER VALUE",
            format_currency(average_order_value),
            "Revenue per order",
        ),
    ]

    cards = "".join(
        (
            '<div class="pricing-kpi">'
            f'<div class="pricing-kpi-label">{escape(label)}</div>'
            f'<div class="pricing-kpi-value">{escape(value)}</div>'
            f'<div class="pricing-kpi-note">{escape(note)}</div>'
            "</div>"
        )
        for label, value, note in metrics
    )

    html = (
        '<section class="pricing-executive">'
        '<div class="pricing-executive-kicker">Pricing</div>'
        '<div class="pricing-executive-title">Executive KPIs</div>'
        '<div class="pricing-executive-description">'
        "A compact view of revenue scale, selling price, discount intensity "
        "and order economics."
        "</div>"
        f'<div class="pricing-kpi-grid">{cards}</div>'
        "</section>"
    )

    st.markdown(html, unsafe_allow_html=True)


# ============================================================
# CHART HELPERS
# ============================================================


def _empty_figure(
    message: str,
    height: int = 300,
    dark: bool = False,
) -> go.Figure:
    """Create a readable empty Plotly figure."""

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
            "color": "#FFFFFF" if dark else MUTED,
        },
    )

    figure.update_layout(
        height=height,
        margin={"l": 45, "r": 25, "t": 18, "b": 42},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={
            "family": "Arial, sans-serif",
            "size": 10,
            "color": "#FFFFFF" if dark else TEXT,
        },
        showlegend=False,
    )

    return figure


def _apply_chart_layout(
    figure: go.Figure,
    height: int = 300,
    dark: bool = False,
) -> None:
    """Apply shared Plotly styling without dictionary unpacking."""

    font_color = "#FFFFFF" if dark else TEXT
    grid_color = GRID_DARK if dark else GRID_LIGHT

    figure.update_layout(
        height=height,
        margin={"l": 62, "r": 42, "t": 22, "b": 48},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={
            "family": "Arial, sans-serif",
            "size": 10,
            "color": font_color,
        },
        showlegend=False,
    )

    figure.update_xaxes(
        showgrid=False,
        zeroline=False,
        tickfont={
            "family": "Arial, sans-serif",
            "size": 10,
            "color": font_color,
        },
    )

    figure.update_yaxes(
        showgrid=True,
        gridcolor=grid_color,
        gridwidth=1,
        zeroline=False,
        tickfont={
            "family": "Arial, sans-serif",
            "size": 10,
            "color": font_color,
        },
    )


def _render_chart_card(
    title: str,
    description: str,
    badge: str,
    figure: go.Figure,
    dark: bool = False,
) -> None:
    """Render one chart with the chart itself inside the same visual card."""

    card_class = "pricing-chart-card dark-card" if dark else "pricing-chart-card"

    st.markdown(
        f'<article class="{card_class}">'
        '<div class="pricing-chart-header">'
        "<div>"
        f'<div class="pricing-chart-title">{escape(title)}</div>'
        f'<div class="pricing-chart-description">'
        f"{escape(description)}"
        "</div>"
        "</div>"
        f'<div class="pricing-chart-badge">{escape(badge)}</div>'
        "</div>",
        unsafe_allow_html=True,
    )

    st.plotly_chart(
        figure,
        use_container_width=True,
        config={"displayModeBar": False},
    )

    st.markdown("</article>", unsafe_allow_html=True)


# ============================================================
# PRICING PERFORMANCE
# ============================================================


def _price_realization_figure(
    engine: PricingEngine,
) -> go.Figure:
    """Build price-realization bars."""

    try:
        dataframe = engine.price_realization().head(10).copy()
    except (KeyError, TypeError, ValueError):
        dataframe = pd.DataFrame()

    if dataframe.empty:
        return _empty_figure(
            "Price realization data is not available.",
            dark=True,
        )

    required = {
        "Product",
        "Price Realization %",
    }

    if not required.issubset(dataframe.columns):
        return _empty_figure(
            "Price realization data is not available.",
            dark=True,
        )

    dataframe["Price Realization %"] = pd.to_numeric(
        dataframe["Price Realization %"],
        errors="coerce",
    ).fillna(0.0)

    dataframe = dataframe.sort_values(
        by="Price Realization %",
        ascending=True,
    ).tail(8)

    labels = [
        safe_text(value)
        for value in dataframe["Product"].tolist()
    ]

    values = [
        safe_float(value)
        for value in dataframe["Price Realization %"].tolist()
    ]

    figure = go.Figure(
        go.Bar(
            x=values,
            y=labels,
            orientation="h",
            marker_color=AQUA,
            text=[f"{value:.1f}%" for value in values],
            textposition="outside",
            textfont={
                "family": "Arial, sans-serif",
                "size": 9,
                "color": "#FFFFFF",
            },
            cliponaxis=False,
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Price realization: %{x:.1f}%"
                "<extra></extra>"
            ),
        )
    )

    _apply_chart_layout(figure, 340, dark=True)

    figure.update_xaxes(
        range=[0, max(105.0, max(values, default=0.0) * 1.12)],
        ticksuffix="%",
        showgrid=True,
        gridcolor=GRID_DARK,
    )

    figure.update_yaxes(
        showgrid=False,
        automargin=True,
    )

    return figure


def _highest_price_figure(
    engine: PricingEngine,
) -> go.Figure:
    """Build highest average selling price bars."""

    try:
        dataframe = engine.highest_priced_products(8).copy()
    except (KeyError, TypeError, ValueError):
        dataframe = pd.DataFrame()

    if dataframe.empty:
        return _empty_figure(
            "Selling-price data is not available.",
            dark=True,
        )

    required = {"Product", "Average Selling Price"}

    if not required.issubset(dataframe.columns):
        return _empty_figure(
            "Selling-price data is not available.",
            dark=True,
        )

    dataframe["Average Selling Price"] = pd.to_numeric(
        dataframe["Average Selling Price"],
        errors="coerce",
    ).fillna(0.0)

    dataframe = dataframe.sort_values(
        by="Average Selling Price",
        ascending=True,
    )

    labels = [
        safe_text(value)
        for value in dataframe["Product"].tolist()
    ]

    values = [
        safe_float(value)
        for value in dataframe["Average Selling Price"].tolist()
    ]

    figure = go.Figure(
        go.Bar(
            x=values,
            y=labels,
            orientation="h",
            marker_color="#74D3D9",
            text=[format_currency(value) for value in values],
            textposition="outside",
            textfont={
                "family": "Arial, sans-serif",
                "size": 9,
                "color": "#FFFFFF",
            },
            cliponaxis=False,
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Average selling price: ₹%{x:,.0f}"
                "<extra></extra>"
            ),
        )
    )

    _apply_chart_layout(figure, 340, dark=True)

    figure.update_xaxes(
        tickprefix="₹",
        tickformat="~s",
        showgrid=True,
        gridcolor=GRID_DARK,
    )

    figure.update_yaxes(
        showgrid=False,
        automargin=True,
    )

    return figure


def render_pricing_performance(
    engine: PricingEngine,
) -> None:
    """Render core selling-price performance."""

    st.markdown(
        '<div class="pricing-chart-grid">',
        unsafe_allow_html=True,
    )

    _render_chart_card(
        "Price Realization by Product",
        "How much of nominal selling value is actually realized?",
        "REALIZATION",
        _price_realization_figure(engine),
        dark=True,
    )

    _render_chart_card(
        "Highest Selling Prices",
        "Products with the highest weighted average selling price.",
        "PRICE",
        _highest_price_figure(engine),
        dark=True,
    )

    st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# DISCOUNT BANDS
# ============================================================


def _discount_band_figure(
    engine: PricingEngine,
    metric: str,
) -> go.Figure:
    """Build discount-band revenue or order-value chart."""

    try:
        dataframe = engine.discount_band_analysis().copy()
    except (KeyError, TypeError, ValueError):
        dataframe = pd.DataFrame()

    if dataframe.empty:
        return _empty_figure(
            "Discount-band data is not available.",
        )

    if metric not in dataframe.columns:
        return _empty_figure(
            "Discount-band data is not available.",
        )

    dataframe["Discount Band"] = (
        dataframe["Discount Band"].astype(str)
    )

    dataframe[metric] = pd.to_numeric(
        dataframe[metric],
        errors="coerce",
    ).fillna(0.0)

    band_order = [
        "0-5%",
        "5-10%",
        "10-15%",
        "15-20%",
        "20%+",
    ]

    dataframe["sort_order"] = dataframe["Discount Band"].map(
        {band: index for index, band in enumerate(band_order)}
    )

    dataframe = dataframe.sort_values("sort_order")

    labels = dataframe["Discount Band"].tolist()
    values = [
        safe_float(value)
        for value in dataframe[metric].tolist()
    ]

    is_revenue = metric == "Revenue"

    figure = go.Figure(
        go.Bar(
            x=labels,
            y=values,
            marker_color=AQUA,
            text=[
                format_currency(value) if is_revenue
                else format_currency(value)
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
                "<b>%{x}</b><br>"
                + (
                    "Revenue: ₹%{y:,.0f}"
                    if is_revenue
                    else "Average revenue/order: ₹%{y:,.0f}"
                )
                + "<extra></extra>"
            ),
        )
    )

    _apply_chart_layout(figure, 315)

    figure.update_yaxes(
        tickprefix="₹",
        tickformat="~s",
        showgrid=True,
        gridcolor=GRID_LIGHT,
    )

    return figure


def render_discount_bands(
    engine: PricingEngine,
) -> None:
    """Render discount-band economics."""

    st.markdown(
        '<div class="pricing-chart-grid">',
        unsafe_allow_html=True,
    )

    _render_chart_card(
        "Revenue by Discount Band",
        "Revenue generated across different discount levels.",
        "REVENUE",
        _discount_band_figure(engine, "Revenue"),
    )

    _render_chart_card(
        "Average Revenue per Order",
        "Order economics across the same discount bands.",
        "ORDER VALUE",
        _discount_band_figure(
            engine,
            "Average Revenue per Order",
        ),
    )

    st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# DISCOUNT DISTRIBUTION
# ============================================================


def _discount_dimension_figure(
    dataframe: pd.DataFrame,
    label_column: str,
    dark: bool = True,
) -> go.Figure:
    """Build a horizontal average-discount ranking."""

    if dataframe.empty:
        return _empty_figure(
            "Discount distribution is not available.",
            dark=dark,
        )

    if (
        label_column not in dataframe.columns
        or "Average Discount %" not in dataframe.columns
    ):
        return _empty_figure(
            "Discount distribution is not available.",
            dark=dark,
        )

    plot = dataframe.copy()

    plot["Average Discount %"] = pd.to_numeric(
        plot["Average Discount %"],
        errors="coerce",
    )

    plot = plot.dropna(
        subset=["Average Discount %"]
    )

    # The engine returns percentages as values such as 40.66.
    # This guard also handles fractional values such as 0.4066.
    if not plot.empty and plot["Average Discount %"].abs().max() <= 1.5:
        plot["Average Discount %"] *= 100.0

    # Discount analytics are valid only in the 0-100% range.
    plot = plot[
        plot["Average Discount %"].between(0, 100)
    ]

    plot = (
        plot.sort_values(
            by="Average Discount %",
            ascending=False,
        )
        .head(8)
        .sort_values(
            by="Average Discount %",
            ascending=True,
        )
    )

    if plot.empty:
        return _empty_figure(
            "Discount distribution is not available.",
            dark=dark,
        )

    labels = [
        safe_text(value)
        for value in plot[label_column].tolist()
    ]

    values = [
        safe_float(value)
        for value in plot["Average Discount %"].tolist()
    ]

    figure = go.Figure(
        go.Bar(
            x=values,
            y=labels,
            orientation="h",
            marker_color=AQUA,
            text=[f"{value:.1f}%" for value in values],
            textposition="outside",
            textfont={
                "family": "Arial, sans-serif",
                "size": 9,
                "color": "#FFFFFF" if dark else TEXT,
            },
            cliponaxis=False,
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Average discount: %{x:.2f}%"
                "<extra></extra>"
            ),
        )
    )

    _apply_chart_layout(
        figure,
        330,
        dark=dark,
    )

    max_discount = max(values) if values else 0.0
    axis_max = min(100.0, max(10.0, ((max_discount // 10) + 1) * 10))

    figure.update_xaxes(
        range=[0, axis_max],
        dtick=10,
        ticksuffix="%",
        showgrid=True,
        gridcolor=GRID_DARK if dark else GRID_LIGHT,
        zeroline=False,
    )

    figure.update_yaxes(
        showgrid=False,
        automargin=True,
    )

    return figure


def render_discount_distribution(
    engine: PricingEngine,
) -> None:
    """Render discount intensity across regions and customers."""

    try:
        regions = engine.average_discount_by_region().copy()
    except (KeyError, TypeError, ValueError):
        regions = pd.DataFrame()

    try:
        customers = engine.average_discount_by_customer().copy()
    except (KeyError, TypeError, ValueError):
        customers = pd.DataFrame()

    st.markdown(
        '<div class="pricing-chart-grid">',
        unsafe_allow_html=True,
    )

    _render_chart_card(
        "Quantity-Weighted Average Discount by Region",
        "Markets receiving the highest quantity-weighted average discount.",
        "REGIONS",
        _discount_dimension_figure(
            regions,
            "Region",
            dark=True,
        ),
        dark=True,
    )

    _render_chart_card(
        "Quantity-Weighted Average Discount by Customer",
        "Customers receiving the highest quantity-weighted average discount.",
        "CUSTOMERS",
        _discount_dimension_figure(
            customers,
            "Customer",
            dark=True,
        ),
        dark=True,
    )

    st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# DISCOUNT EFFECTIVENESS
# ============================================================


def _discount_sales_scatter(
    engine: PricingEngine,
) -> go.Figure:
    """Build product-level discount versus quantity scatter."""

    try:
        result: dict[str, Any] = engine.discount_vs_sales()
    except (KeyError, TypeError, ValueError):
        result = {}

    dataframe = result.get("product_data")

    if not isinstance(dataframe, pd.DataFrame):
        return _empty_figure(
            "Discount-sales data is not available.",
        )

    if dataframe.empty:
        return _empty_figure(
            "Discount-sales data is not available.",
        )

    required = {
        "Average Discount %",
        "Quantity",
        "Revenue",
        "Product",
    }

    if not required.issubset(dataframe.columns):
        return _empty_figure(
            "Discount-sales data is not available.",
        )

    plot = dataframe.copy()

    plot["Average Discount %"] = pd.to_numeric(
        plot["Average Discount %"],
        errors="coerce",
    )

    plot["Quantity"] = pd.to_numeric(
        plot["Quantity"],
        errors="coerce",
    )

    plot["Revenue"] = pd.to_numeric(
        plot["Revenue"],
        errors="coerce",
    )

    plot = plot.dropna(
        subset=[
            "Average Discount %",
            "Quantity",
            "Revenue",
        ]
    )

    if plot.empty:
        return _empty_figure(
            "Discount-sales data is not available.",
        )

    # Normalize fraction-form discounts to percentage points.
    if not plot.empty and plot["Average Discount %"].abs().max() <= 1.5:
        plot["Average Discount %"] = plot["Average Discount %"] * 100

    # Discount effectiveness uses only valid 0-100% discounts.
    plot = plot[plot["Average Discount %"].between(0, 100)]

    if plot.empty:
        return _empty_figure(
            "Discount-sales data is not available.",
        )

    correlation = safe_float(
        result.get("correlation")
    )

    figure = go.Figure(
        go.Scatter(
            x=plot["Average Discount %"].tolist(),
            y=plot["Quantity"].tolist(),
            mode="markers",
            marker={
                "color": AQUA,
                "size": 7,
                "opacity": 0.70,
            },
            customdata=plot[
                ["Product", "Revenue"]
            ].astype(str).values.tolist(),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Discount: %{x:.2f}%<br>"
                "Quantity: %{y:,.1f}<br>"
                "Revenue: ₹%{customdata[1]} "
                "<extra></extra>"
            ),
        )
    )

    _apply_chart_layout(figure, 330)

    figure.update_xaxes(
        title="Average Discount %",
        ticksuffix="%",
        showgrid=True,
        gridcolor=GRID_LIGHT,
    )

    figure.update_yaxes(
        title="Quantity Sold",
        showgrid=True,
        gridcolor=GRID_LIGHT,
    )

    figure.add_annotation(
        x=0.98,
        y=0.96,
        xref="paper",
        yref="paper",
        xanchor="right",
        yanchor="top",
        text=f"Correlation: {correlation:.3f}",
        showarrow=False,
        bgcolor="#E8F7F9",
        bordercolor="#CDEFF2",
        borderwidth=1,
        font={
            "family": "Arial, sans-serif",
            "size": 10,
            "color": "#087C8A",
        },
    )

    return figure


def _highest_discounted_table(
    engine: PricingEngine,
) -> str:
    """Build a compact highest-discounted-products table."""

    try:
        dataframe = engine.highest_discounted_products(8).copy()
    except (KeyError, TypeError, ValueError):
        dataframe = pd.DataFrame()

    if dataframe.empty:
        return (
            '<div class="pricing-empty">'
            "Highest-discounted product data is not available."
            "</div>"
        )

    dataframe = dataframe.copy()

    if "Average Discount %" in dataframe.columns:
        dataframe["Average Discount %"] = pd.to_numeric(
            dataframe["Average Discount %"],
            errors="coerce",
        )

        valid_discounts = dataframe["Average Discount %"].dropna()

        # Support either 0-1 fractions or 0-100 percentage points.
        if (
            not valid_discounts.empty
            and valid_discounts.abs().max() <= 1.5
        ):
            dataframe["Average Discount %"] = (
                dataframe["Average Discount %"] * 100
            )

        # Never display invalid discounts such as negative or >100%.
        dataframe = dataframe[
            dataframe["Average Discount %"].between(0, 100)
        ]

    if dataframe.empty:
        return (
            '<div class="pricing-empty">'
            "No valid highest-discounted product data is available."
            "</div>"
        )

    rows: list[str] = []

    for _, row in dataframe.iterrows():
        rank = int(safe_float(row.get("Rank")))
        product = safe_text(row.get("Product"))
        revenue = safe_float(row.get("Revenue"))
        discount = safe_float(
            row.get("Average Discount %")
        )

        rows.append(
            "<tr>"
            "<td>"
            f'<span class="pricing-rank">{rank}</span>'
            "</td>"
            f"<td>{escape(product)}</td>"
            f"<td>{escape(format_currency(revenue))}</td>"
            f"<td>{escape(format_percentage(discount))}</td>"
            "</tr>"
        )

    return (
        '<table class="pricing-table">'
        "<thead><tr>"
        "<th>#</th>"
        "<th>Product</th>"
        "<th>Revenue</th>"
        "<th>Avg Discount</th>"
        "</tr></thead>"
        "<tbody>"
        + "".join(rows)
        + "</tbody></table>"
    )


def render_discount_effectiveness(
    engine: PricingEngine,
) -> None:
    """Render discount-sales relationship and exception table."""

    st.markdown(
        '<div class="pricing-chart-grid">',
        unsafe_allow_html=True,
    )

    _render_chart_card(
        "Discount vs Quantity Sold",
        "Product-level relationship between discount intensity and units sold.",
        "CORRELATION",
        _discount_sales_scatter(engine),
    )

    st.markdown(
        '<article class="pricing-chart-card">'
        '<div class="pricing-chart-header">'
        "<div>"
        '<div class="pricing-chart-title">'
        "Highest Quantity-Weighted Discounted Products"
        "</div>"
        '<div class="pricing-chart-description">'
        "Products receiving the largest quantity-weighted discounts."
        "</div>"
        "</div>"
        '<div class="pricing-chart-badge">EXCEPTIONS</div>'
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        _highest_discounted_table(engine),
        unsafe_allow_html=True,
    )

    st.markdown("</article>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# PRODUCT LOOKUP
# ============================================================


def _product_codes(engine: PricingEngine) -> list[str]:
    """Return available item codes from the pricing engine."""

    try:
        data = engine.average_selling_price()
    except (KeyError, TypeError, ValueError):
        return []

    if data.empty or "Item Code" not in data.columns:
        return []

    return sorted(
        {
            str(value).strip()
            for value in data["Item Code"].dropna().tolist()
            if str(value).strip()
        }
    )


def render_product_lookup(
    engine: PricingEngine,
) -> None:
    """Render an individual product pricing profile."""

    codes = _product_codes(engine)

    if not codes:
        st.markdown(
            '<div class="pricing-empty">'
            "No product pricing data is available."
            "</div>",
            unsafe_allow_html=True,
        )
        return

    selected_code = st.selectbox(
        "Select product",
        codes,
        index=0,
        key="pricing_product_selector",
    )

    try:
        details = engine.product_price_details(
            selected_code
        )
    except (KeyError, TypeError, ValueError):
        details = pd.DataFrame()

    if details.empty:
        st.markdown(
            '<div class="pricing-empty">'
            "Pricing details are not available for this product."
            "</div>",
            unsafe_allow_html=True,
        )
        return

    row = details.iloc[0]

    product = safe_text(row.get("Product"))
    quantity = safe_float(row.get("Quantity"))
    revenue = safe_float(row.get("Revenue"))
    selling_price = safe_float(
        row.get("Average Selling Price")
    )
    discount = safe_float(
        row.get("Average Discount %")
    )

    profile_html = (
        '<div class="pricing-profile">'
        f'<div class="pricing-profile-title">'
        f"{escape(product)}"
        "</div>"
        '<div class="pricing-profile-subtitle">'
        f"Item Code: {escape(selected_code)}"
        "</div>"
        '<div class="pricing-profile-grid">'
        '<div class="pricing-profile-metric">'
        '<div class="pricing-profile-label">Quantity</div>'
        f'<div class="pricing-profile-value">'
        f"{escape(format_number(quantity))}"
        "</div></div>"
        '<div class="pricing-profile-metric">'
        '<div class="pricing-profile-label">Revenue</div>'
        f'<div class="pricing-profile-value">'
        f"{escape(format_currency(revenue))}"
        "</div></div>"
        '<div class="pricing-profile-metric">'
        '<div class="pricing-profile-label">Avg Selling Price</div>'
        f'<div class="pricing-profile-value">'
        f"{escape(format_currency(selling_price))}"
        "</div></div>"
        '<div class="pricing-profile-metric">'
        '<div class="pricing-profile-label">Avg Discount</div>'
        f'<div class="pricing-profile-value">'
        f"{escape(format_percentage(discount))}"
        "</div></div>"
        "</div>"
        "</div>"
    )

    st.markdown(
        profile_html,
        unsafe_allow_html=True,
    )


# ============================================================
# MAIN DASHBOARD
# ============================================================


def render_pricing_dashboard(
    on_back: Callable[[], None] | None = None,
) -> None:
    """Render the complete Pricing Intelligence dashboard."""

    del on_back

    apply_theme("AQVASTAR | Pricing Intelligence")
    inject_pricing_css()

    render_brand()
    render_navigation("pricing")

    # Match Regional and Sales dashboards exactly:
    # fixed bottom-left position and same-tab routing.
    st.markdown(
        '<a href="?page=home" '
        'target="_self" '
        'class="pricing-floating-home" '
        'aria-label="Back to Home">'
        '<span class="pricing-floating-home-icon">⌂</span>'
        '<span class="pricing-floating-home-text">'
        "BACK TO HOME"
        "</span>"
        "</a>",
        unsafe_allow_html=True,
    )

    try:
        engine = PricingEngine()
    except (
        KeyError,
        TypeError,
        ValueError,
    ) as exc:
        st.error(
            f"Pricing engine could not be initialized: {exc}"
        )
        return

    latest_date = SalesQueries.get_latest_posting_date()

    render_header(latest_date)
    render_executive_kpis(engine)

    # ========================================================
    # PRICING PERFORMANCE
    # ========================================================

    with st.container(
        key="pricing_performance_section"
    ):
        render_section_heading(
            "Pricing Performance",
            "How effectively are prices being realized?",
            (
                "Compare realized selling value with product pricing "
                "across the portfolio."
            ),
            "₹",
            dark=True,
        )

        render_pricing_performance(engine)

    # ========================================================
    # DISCOUNT ANALYSIS
    # ========================================================

    with st.container(
        key="pricing_discount_section"
    ):
        render_section_heading(
            "Discount Analysis",
            "Where is revenue being given away?",
            (
                "Compare revenue and order economics across different "
                "discount levels."
            ),
            "%",
        )

        render_discount_bands(engine)

    # ========================================================
    # DISCOUNT DISTRIBUTION
    # ========================================================

    with st.container(
        key="pricing_distribution_section"
    ):
        render_section_heading(
            "Discount Distribution",
            "Who is receiving the deepest discounts?",
            (
                "Compare discount intensity across markets and customer "
                "relationships."
            ),
            "◈",
            dark=True,
        )

        render_discount_distribution(engine)

    # ========================================================
    # DISCOUNT EFFECTIVENESS
    # ========================================================

    with st.container(
        key="pricing_effectiveness_section"
    ):
        render_section_heading(
            "Discount Effectiveness",
            "Do higher discounts actually move more product?",
            (
                "Examine the relationship between discount levels, "
                "quantity sold and high-discount products."
            ),
            "↗",
        )

        render_discount_effectiveness(engine)

    # ========================================================
    # PRODUCT LOOKUP
    # ========================================================

    with st.container(
        key="pricing_lookup_section"
    ):
        render_section_heading(
            "Pricing Explorer",
            "Inspect the economics of an individual product",
            (
                "Select a product to view its quantity, revenue, "
                "selling price and average discount."
            ),
            "⌕",
        )

        render_product_lookup(engine)


def main() -> None:
    """Render the AQVASTAR Pricing Intelligence dashboard."""
    render_pricing_dashboard()


if __name__ == "__main__":
    main()
