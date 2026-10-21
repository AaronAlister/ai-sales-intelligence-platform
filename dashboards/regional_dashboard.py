"""
AQVASTAR Sales Intelligence Platform.

Regional Intelligence Dashboard.

Dashboard orchestration only. Regional business logic remains in
RegionalEngine. This dashboard follows the same visual blueprint as the
Customer Intelligence page: compact hero, executive KPIs, alternating
light/dark intelligence sections, consistent spacing, typography and
responsive behavior.
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
from engines.regional_engine import RegionalEngine


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
SUCCESS = "#0B8D80"

AXIS_LIGHT = "#D8F5F7"
GRID_DARK = "rgba(216,245,247,0.55)"

SHADOW = "0 10px 28px rgba(5, 57, 70, 0.07)"
SHADOW_DARK = "0 14px 34px rgba(2, 42, 53, 0.15)"


# ============================================================
# FORMATTERS
# ============================================================


def format_currency(value: float) -> str:
    """Format Indian currency using compact dashboard notation."""

    numeric_value = float(value)
    absolute_value = abs(numeric_value)

    if absolute_value >= 1_000_000_000:
        return f"₹{numeric_value / 1_000_000_000:.2f}B"

    if absolute_value >= 1_000_000:
        return f"₹{numeric_value / 1_000_000:.2f}M"

    if absolute_value >= 1_000:
        return f"₹{numeric_value / 1_000:.1f}K"

    return f"₹{numeric_value:,.0f}"


def format_number(value: float) -> str:
    """Format dashboard counts and quantities."""

    numeric_value = float(value)

    if numeric_value.is_integer():
        return f"{int(numeric_value):,}"

    return f"{numeric_value:,.1f}"


def format_percentage(value: float) -> str:
    """Format a percentage."""

    return f"{float(value):.1f}%"


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


def _safe_text(
    value: object,
    default: str = "N/A",
) -> str:
    """Convert arbitrary values into readable text."""

    if value is None:
        return default

    text = str(value).strip()

    return text if text else default


# ============================================================
# CSS
# ============================================================


def inject_dashboard_css() -> None:
    """Inject the Regional Intelligence visual system."""

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
           BACK HOME
           ================================================== */

        .regional-floating-home {{
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

        .regional-floating-home:hover {{
            transform: translateY(-3px);
            border-color: {AQUA};
            box-shadow: 0 16px 36px rgba(4,62,76,0.22);
            color: #087C8A !important;
        }}

        .regional-floating-home-icon {{
            display: flex;
            align-items: center;
            justify-content: center;

            width: 32px;
            height: 32px;

            border-radius: 10px;

            background: {DEEP};
            color: #FFFFFF;

            font-size: 0.95rem;
            font-weight: 800;
            line-height: 1;
        }}

        .regional-floating-home-text {{
            white-space: nowrap;
        }}

        /* ==================================================
           SECTION CONTAINERS
           ================================================== */

        .st-key-regional_performance_section,
        .st-key-regional_growth_section,
        .st-key-regional_contribution_section,
        .st-key-regional_demand_section,
        .st-key-regional_lookup_section {{
            position: relative;
            overflow: hidden;

            border-radius: 20px;

            margin-top: 1.05rem;
            margin-bottom: 1.45rem;

            padding: 1.25rem 1.35rem 2.05rem;
        }}

        .st-key-regional_performance_section,
        .st-key-regional_contribution_section {{
            background:
                radial-gradient(
                    circle at 100% 0%,
                    rgba(40,192,204,0.13),
                    transparent 25%
                ),
                linear-gradient(
                    135deg,
                    {DEEP} 0%,
                    {DEEP_2} 62%,
                    #087285 100%
                );

            border: 1px solid rgba(255,255,255,0.08);

            box-shadow: {SHADOW_DARK};
        }}

        .st-key-regional_growth_section,
        .st-key-regional_demand_section,
        .st-key-regional_lookup_section {{
            background:
                linear-gradient(
                    145deg,
                    #F7FCFD 0%,
                    #EAF7F9 100%
                );

            border: 1px solid #D8EAEE;

            box-shadow: {SHADOW};
        }}

        /* ==================================================
           HERO
           ================================================== */

        .regional-hero {{
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

            box-shadow:
                0 14px 34px
                rgba(5,60,74,0.14);
        }}

        .regional-hero-content {{
            position: relative;
            z-index: 3;

            max-width: 760px;
        }}

        .regional-hero-eyebrow {{
            color: #3BD0D8;

            font-size: 0.60rem;
            font-weight: 800;

            letter-spacing: 0.18em;
            text-transform: uppercase;

            margin-bottom: 0.58rem;
        }}

        .regional-hero-title {{
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

        .regional-hero-description {{
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

        .regional-hero-asof {{
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

        .regional-hero-asof strong {{
            display: block;

            color: #FFFFFF;

            font-size: 0.75rem;

            margin-top: 0.15rem;
        }}

        .regional-hero-ring {{
            position: absolute;

            border:
                1px solid
                rgba(255,255,255,0.13);

            border-radius: 50%;

            pointer-events: none;
        }}

        /* Abstract regional network */
        .regional-network {{
            position: absolute;
            right: 8%;
            top: 24px;

            width: 145px;
            height: 110px;

            opacity: 0.19;
            pointer-events: none;
        }}

        .regional-network-line {{
            position: absolute;

            height: 1px;

            background: #A8E8ED;

            transform-origin: left center;
        }}

        .regional-network-node {{
            position: absolute;

            width: 12px;
            height: 12px;

            border-radius: 50%;

            background: #A8E8ED;

            box-shadow:
                0 0 0 7px rgba(168,232,237,0.08);
        }}

        /* ==================================================
           SECTION HEADER
           ================================================== */

        .section-heading {{
            position: relative;
            z-index: 2;

            display: flex;
            align-items: flex-start;

            gap: 0.90rem;

            margin: 0 0 1.15rem;
        }}

        .section-icon {{
            width: 43px;
            height: 43px;
            min-width: 43px;

            display: flex;
            align-items: center;
            justify-content: center;

            border-radius: 11px;

            background: {AQUA};
            color: #FFFFFF;

            font-size: 1rem;
            font-weight: 800;

            box-shadow:
                inset 0 0 0 1px
                rgba(255,255,255,0.12);
        }}

        .dark-section .section-icon {{
            background: #0C8FA0;
        }}

        .section-copy {{
            min-width: 0;
        }}

        .section-eyebrow {{
            color: #11899A;

            font-size: 0.64rem;
            font-weight: 800;

            letter-spacing: 0.15em;
            text-transform: uppercase;

            margin-bottom: 0.18rem;
        }}

        .dark-section .section-eyebrow {{
            color: #36CBD5;
        }}

        .section-title {{
            color: {TEXT};

            font-size: 1.38rem;
            line-height: 1.12;
            font-weight: 800;

            letter-spacing: -0.03em;
        }}

        .dark-section .section-title {{
            color: #FFFFFF;
        }}

        .section-description {{
            color: {MUTED};

            font-size: 0.72rem;
            line-height: 1.42;

            margin-top: 0.28rem;
        }}

        .dark-section .section-description {{
            color: rgba(255,255,255,0.68);
        }}

        /* ==================================================
           EXECUTIVE SUMMARY
           ================================================== */

        .executive-summary {{
            position: relative;
            overflow: hidden;

            margin: 0.85rem 0 1.15rem;

            padding: 0.15rem 0 0.05rem;
        }}

        .executive-kicker {{
            color: #11899A;

            font-size: 0.64rem;
            font-weight: 800;

            letter-spacing: 0.16em;
            text-transform: uppercase;

            margin-bottom: 0.18rem;
        }}

        .executive-title {{
            color: {TEXT};

            font-size: 1.32rem;
            line-height: 1.15;
            font-weight: 800;

            letter-spacing: -0.025em;

            margin-bottom: 0.18rem;
        }}

        .executive-description {{
            color: {MUTED};

            font-size: 0.74rem;
            line-height: 1.4;

            margin-bottom: 0.68rem;
        }}

        .executive-kpi-grid {{
            display: grid;

            grid-template-columns:
                repeat(4, minmax(0, 1fr));

            gap: 0.65rem;
        }}

        .executive-kpi {{
            min-width: 0;

            padding: 0.78rem 0.82rem;

            border: 1px solid #D6E7EB;
            border-radius: 13px;

            background: #FFFFFF;

            box-shadow:
                0 6px 18px
                rgba(7,63,76,0.045);
        }}

        .executive-kpi-label {{
            color: #198C9B;

            font-size: 0.57rem;
            font-weight: 800;

            letter-spacing: 0.10em;
            text-transform: uppercase;
        }}

        .executive-kpi-value {{
            color: {TEXT};

            font-size: 1.28rem;
            line-height: 1.05;
            font-weight: 800;

            letter-spacing: -0.025em;

            margin: 0.30rem 0 0.16rem;

            white-space: nowrap;
        }}

        .executive-kpi-note {{
            color: {MUTED};

            font-size: 0.57rem;
            line-height: 1.3;
        }}

        /* ==================================================
           CHART CARDS
           ================================================== */

        .chart-grid {{
            display: grid;

            grid-template-columns:
                repeat(2, minmax(0, 1fr));

            gap: 0.85rem;
        }}

        .chart-card {{
            min-width: 0;

            border:
                1px solid
                #D8E7EA;

            border-radius: 14px;

            background: #FFFFFF;

            box-shadow:
                0 6px 18px
                rgba(7,63,76,0.045);

            overflow: hidden;
        }}

        .dark-section .chart-card {{
            background: rgba(255,255,255,0.055);

            border-color:
                rgba(255,255,255,0.09);

            box-shadow: none;
        }}

        .chart-title {{
            color: {TEXT};

            font-size: 0.86rem;
            font-weight: 800;

            letter-spacing: -0.02em;

            padding: 0.78rem 0.85rem 0.08rem;
        }}

        .dark-section .chart-title {{
            color: #FFFFFF;
        }}

        .chart-description {{
            color: #71878E;

            font-size: 0.62rem;

            padding: 0 0.85rem 0.42rem;
        }}

        .dark-section .chart-description {{
            color: rgba(255,255,255,0.58);
        }}

        .chart-badge {{
            display: inline-flex;

            margin:
                0.05rem 0.85rem 0.45rem;

            padding:
                0.28rem 0.45rem;

            border-radius: 7px;

            background: #E8F7F9;

            color: #087C8A;

            font-size: 0.55rem;
            font-weight: 800;

            letter-spacing: 0.05em;
            text-transform: uppercase;
        }}

        .dark-section .chart-badge {{
            background: rgba(59,208,216,0.12);
            color: #70E0E5;
        }}

        /* ==================================================
           RANKING TABLE
           ================================================== */

        .regional-table {{
            width: 100%;

            border-collapse: collapse;

            background: #FFFFFF;
        }}

        .regional-table th {{
            padding: 0.55rem 0.70rem;

            color: #71878E;

            background: #F7FBFC;

            border-bottom: 1px solid #E3EDF0;

            font-size: 0.57rem;
            font-weight: 800;

            letter-spacing: 0.10em;
            text-transform: uppercase;

            text-align: left;
        }}

        .regional-table td {{
            padding: 0.62rem 0.70rem;

            color: {TEXT};

            border-bottom: 1px solid #EDF2F3;

            font-size: 0.67rem;
            line-height: 1.35;
        }}

        .regional-table tr:last-child td {{
            border-bottom: none;
        }}

        .rank-pill {{
            display: inline-flex;

            align-items: center;
            justify-content: center;

            min-width: 26px;
            height: 26px;

            border-radius: 8px;

            background: #E8F7F9;
            color: #087C8A;

            font-size: 0.62rem;
            font-weight: 900;
        }}

        .dark-section .rank-pill {{
            background: rgba(255,255,255,0.09);
            color: #8DE8ED;
        }}

        .region-name {{
            font-weight: 800;
        }}

        .region-value {{
            font-weight: 700;
            white-space: nowrap;
        }}

        /* ==================================================
           GROWTH CARDS
           ================================================== */

        .growth-grid {{
            display: grid;

            grid-template-columns:
                repeat(2, minmax(0, 1fr));

            gap: 0.85rem;

            margin-top: 0.85rem;
        }}

        .growth-card {{
            min-width: 0;

            padding: 0.75rem;

            border-radius: 13px;

            background: #FFFFFF;

            border: 1px solid #D8E7EA;

            box-shadow:
                0 6px 18px
                rgba(7,63,76,0.045);
        }}

        .growth-card-title {{
            color: {TEXT};

            font-size: 0.78rem;
            font-weight: 800;
        }}

        .growth-card-note {{
            color: {MUTED};

            font-size: 0.61rem;

            margin-top: 0.16rem;
        }}

        .growth-region {{
            display: flex;

            align-items: center;
            justify-content: space-between;

            gap: 0.5rem;

            padding:
                0.48rem
                0.15rem;

            border-bottom: 1px solid #EDF2F3;
        }}

        .growth-region:last-child {{
            border-bottom: none;
        }}

        .growth-region-name {{
            min-width: 0;

            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;

            color: {TEXT};

            font-size: 0.65rem;
            font-weight: 700;
        }}

        .growth-region-value {{
            flex: 0 0 auto;

            font-size: 0.64rem;
            font-weight: 800;
        }}

        .growth-filter-note {{
            margin-top: 0.55rem;
            padding: 0.50rem 0.62rem;
            border-radius: 9px;
            background: #F0FAFB;
            border: 1px solid #D7ECEF;
            color: #58727A;
            font-size: 0.60rem;
            line-height: 1.45;
        }}

        .growth-filter-note strong {{
            color: #087C8A;
            font-weight: 800;
        }}

        .growth-positive {{
            color: {SUCCESS};
        }}

        .growth-negative {{
            color: #B45B5B;
        }}

        /* ==================================================
           ABC STRUCTURE
           ================================================== */

        .st-key-abc_structure {{
            margin-top: 0.95rem;
            padding: 1.20rem 1.20rem 1.25rem;
            border-radius: 18px;
            background: #FFFFFF;
            border: 1px solid #D7E7EB;
            box-shadow: 0 10px 28px rgba(3, 52, 65, 0.08);
        }}

        .abc-section-top {{
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 1.25rem;
            margin-bottom: 1rem;
        }}

        .abc-section-copy {{
            min-width: 0;
        }}

        .st-key-abc_structure .abc-section-title {{
            color: #102631;
            font-size: 1.02rem;
            font-weight: 850;
            letter-spacing: -0.025em;
            margin: 0;
        }}

        .st-key-abc_structure .abc-section-description {{
            color: #617982;
            font-size: 0.67rem;
            line-height: 1.45;
            margin-top: 0.25rem;
        }}

        .st-key-abc_structure .abc-section-badge {{
            display: inline-flex;
            padding: 0.30rem 0.50rem;
            border-radius: 999px;
            background: #E8F7F9;
            color: #087C8A;
            font-size: 0.54rem;
            font-weight: 850;
            letter-spacing: 0.07em;
            text-transform: uppercase;
            margin-top: 0.58rem;
        }}

        .abc-rules {{
            flex: 0 0 auto;
            max-width: 310px;
            padding: 0.62rem 0.78rem;
            border: 1px solid #D9EAED;
            border-radius: 12px;
            background: #F5FBFC;
            color: #526F78;
            font-size: 0.58rem;
            line-height: 1.45;
        }}

        .abc-rules strong {{
            color: #173E49;
            font-weight: 850;
        }}

        .abc-rules-title {{
            color: #087C8A;
            font-size: 0.52rem;
            font-weight: 850;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 0.18rem;
        }}

        .st-key-abc_structure [data-testid="stHorizontalBlock"] {{
            gap: 0.78rem;
            align-items: stretch;
        }}

        /* ==================================================
           ABC CARDS
           ================================================== */

        .st-key-abc_structure [data-testid="column"] {{
            min-width: 0;
        }}

        /* --------------------------------------------------
           Individual ABC card containers
           -------------------------------------------------- */

        .st-key-abc_structure [class*="st-key-abc_card_"] {{
            position: relative;
            min-height: auto; /* Let content dictate height */
            padding: 0.75rem 0.85rem; /* Tighter padding */

            border-radius: 14px;

            background: #FFFFFF;

            border: 1.5px solid #CDE7EB;

            box-shadow:
                0 4px 14px
                rgba(7, 63, 76, 0.05);

            transition:
                transform 150ms ease,
                box-shadow 150ms ease,
                border-color 150ms ease,
                background 150ms ease;

            display: flex;
            flex-direction: column;
        }}

        /* --------------------------------------------------
           Subtle tonal hierarchy
           Same palette, NOT different colors
           -------------------------------------------------- */

        .st-key-abc_structure [class*="st-key-abc_card_A"] {{
            background: #F2FBFC;
            border-color: #7CCED6;
        }}

        .st-key-abc_structure [class*="st-key-abc_card_B"] {{
            background: #F6FCFD;
            border-color: #A0DCE2;
        }}

        .st-key-abc_structure [class*="st-key-abc_card_C"] {{
            background: #FAFDFD;
            border-color: #B9E3E7;
        }}

        /* --------------------------------------------------
           Hover
           -------------------------------------------------- */

        .st-key-abc_structure [class*="st-key-abc_card_"]:hover {{
            transform: translateY(-2px);

            border-color: #1599A8;

            box-shadow:
                0 8px 20px
                rgba(7, 63, 76, 0.10);
        }}

        /* --------------------------------------------------
           Card content
           -------------------------------------------------- */

        .abc-card-letter {{
            color: #087C8A;

            font-size: 1.25rem;
            line-height: 1;

            font-weight: 900;

            letter-spacing: 0.025em;

            margin-bottom: 0.25rem;
        }}

        .abc-card-label {{
            color: #58727A;

            font-size: 0.52rem;
            font-weight: 800;

            letter-spacing: 0.11em;
            text-transform: uppercase;

            margin-bottom: 0.10rem;
        }}

        .abc-card-value {{
            color: #102631;

            font-size: 0.80rem;
            line-height: 1.25;

            font-weight: 850;

            margin-bottom: 0.10rem;
        }}

        .abc-card-description {{
            color: #617982;

            font-size: 0.58rem;
            line-height: 1.35;
        }}

        /* --------------------------------------------------
           Card divider
           -------------------------------------------------- */

        .abc-card-divider {{
            width: 100%;
            height: 1px;

            margin: 0.4rem 0 0.3rem;

            background: #DDECEF;
        }}

        /* --------------------------------------------------
           View regions button (Styled as a simple text link)
           -------------------------------------------------- */

        .st-key-abc_structure [class*="st-key-abc_card_"] [data-testid="stButton"] {{
            margin-top: 0.2rem; /* Reduced margin to bring button up */
            padding-top: 0;
        }}

        .st-key-abc_structure [class*="st-key-abc_card_"] [data-testid="stButton"] button {{
            width: 100% !important;

            min-height: auto !important; /* Remove default button height */
            padding: 0 !important; /* Remove default padding */

            background: transparent !important;
            border: none !important;
            box-shadow: none !important;

            color: #087C8A !important;

            font-size: 0.65rem !important;
            font-weight: 800 !important;
            letter-spacing: 0.03em;

            text-align: center !important; /* Center the text */
            justify-content: center !important; /* Center the content */

            display: flex;
            align-items: center;
            gap: 0.25rem;

            transition: color 120ms ease;
        }}

        .st-key-abc_structure [class*="st-key-abc_card_"] [data-testid="stButton"] button:hover {{
            color: #056B78 !important;
            text-decoration: underline;
        }}

        .st-key-abc_structure [class*="st-key-abc_card_"] [data-testid="stButton"] button:focus-visible {{
            outline: none !important;
            box-shadow: none !important;
            color: #087C8A !important;
            text-decoration: underline;
        }}

        /* --------------------------------------------------
           Selected card
           -------------------------------------------------- */

        .st-key-abc_structure [class*="st-key-abc_card_selected"] {{
            border-color: #087C8A;

            background:
                linear-gradient(
                    145deg,
                    #EAF8FA 0%,
                    #F7FCFD 100%
                );

            box-shadow:
                0 0 0 2px rgba(8,124,138,0.10),
                0 8px 20px rgba(7,63,76,0.10);
        }}

        /* --------------------------------------------------
           Mobile
           -------------------------------------------------- */

        @media (max-width: 850px) {{

            .st-key-abc_structure
            [data-testid="stHorizontalBlock"] {{
                flex-direction: column;
            }}

            .st-key-abc_structure
            [data-testid="column"] {{
                width: 100% !important;
            }}

            .st-key-abc_structure
            [class*="st-key-abc_card_"] {{
                min-height: 100px;
            }}
        }}

        /* ==================================================
           ABC DETAIL TABLE + COVERAGE FOOTER
           ================================================== */

        .abc-detail {{
            margin-top: 1rem;
            padding: 1rem;
            border: 1px solid #BDE1E5;
            border-radius: 16px;
            background: linear-gradient(145deg, #F6FCFD 0%, #FFFFFF 100%);
            box-shadow: 0 6px 18px rgba(7,63,76,0.045);
        }}

        .abc-detail-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            padding-bottom: 0.72rem;
            margin-bottom: 0.68rem;
            border-bottom: 1px solid #DFECEF;
        }}

        .abc-detail-title {{
            color: #102631;
            font-size: 0.94rem;
            font-weight: 850;
        }}

        .abc-detail-count {{
            padding: 0.28rem 0.50rem;
            border-radius: 999px;
            background: #E8F7F9;
            color: #087C8A;
            font-size: 0.57rem;
            font-weight: 850;
            white-space: nowrap;
        }}

        .abc-detail-note {{
            color: #617982;
            font-size: 0.63rem;
            line-height: 1.45;
            margin-bottom: 0.72rem;
        }}

        .abc-table-header,
        .abc-region-row {{
            display: grid;
            grid-template-columns: 0.45fr 2fr 1.15fr 1fr 1.15fr;
            gap: 0.6rem;
            align-items: center;
        }}

        .abc-table-header {{
            padding: 0.48rem 0.68rem;
            border-radius: 9px;
            background: #EAF7F9;
            color: #58727A;
            font-size: 0.53rem;
            font-weight: 850;
            letter-spacing: 0.06em;
            text-transform: uppercase;
        }}

        /* Fix table header alignment */
        .abc-table-header span:nth-child(1),
        .abc-table-header span:nth-child(2) {{
            text-align: left;
        }}

        .abc-table-header span:nth-child(3),
        .abc-table-header span:nth-child(4),
        .abc-table-header span:nth-child(5) {{
            text-align: right;
        }}

        .abc-region-row {{
            min-height: 43px;
            padding: 0.48rem 0.68rem;
            margin-top: 0.28rem;
            background: #FFFFFF;
            border: 1px solid #E0ECEF;
            border-radius: 9px;
            transition: background 120ms ease, border-color 120ms ease;
        }}

        .abc-region-row:hover {{
            background: #F4FAFB;
            border-color: #C6E1E5;
        }}

        .abc-region-rank {{
            color: #738A92;
            font-size: 0.60rem;
            font-weight: 750;
        }}

        .abc-region-name {{
            color: #102631;
            font-size: 0.66rem;
            font-weight: 850;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}

        .abc-region-meta {{
            color: #526F78;
            font-size: 0.60rem;
            font-weight: 750;
            text-align: right;
            white-space: nowrap;
        }}

        .abc-coverage {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            margin-top: 0.45rem; /* Reduced margin to bring it up */
            margin-bottom: 0.10rem;
            padding: 0.68rem 0.78rem;
            border: 1px solid #CFE7EA;
            border-radius: 11px;
            background: #F0FAFB;
            color: #58727A;
            font-size: 0.61rem;
            line-height: 1.45;
        }}

        .abc-coverage strong {{
            color: #087C8A;
            font-weight: 850;
        }}

        @media (max-width: 850px) {{
            .abc-section-top {{
                flex-direction: column;
            }}

            .abc-rules {{
                max-width: none;
                width: 100%;
            }}

            .abc-table-header,
            .abc-region-row {{
                grid-template-columns: 0.45fr 1.8fr 1.2fr;
            }}

            .abc-table-header span:nth-child(4),
            .abc-table-header span:nth-child(5),
            .abc-region-row > span:nth-child(4),
            .abc-region-row > span:nth-child(5) {{
                display: none;
            }}
        }}

        @media (max-width: 650px) {{
            .abc-table-header,
            .abc-region-row {{
                grid-template-columns: 0.5fr 1.8fr 1fr;
            }}

            .abc-region-row {{
                min-height: 48px;
            }}

            .abc-coverage {{
                align-items: flex-start;
                flex-direction: column;
            }}
        }}

        /* ==================================================
           PROFILE
           ================================================== */

        .profile-card {{
            position: relative;
            overflow: hidden;

            padding: 0.95rem;

            border-radius: 15px;

            background: #FFFFFF;

            border: 1px solid #D6E7EB;

            box-shadow:
                0 7px 22px
                rgba(7,63,76,0.055);
        }}

        .profile-watermark {{
            position: absolute;

            right: -25px;
            top: -45px;

            width: 190px;
            height: 150px;

            opacity: 0.34;
        }}

        .profile-wave {{
            position: absolute;

            border:
                1px solid
                rgba(17,175,193,0.18);

            border-radius: 50%;
        }}

        .profile-wave.one {{
            width: 170px;
            height: 170px;

            right: -75px;
            top: 0;
        }}

        .profile-wave.two {{
            width: 120px;
            height: 120px;

            right: 5px;
            top: 25px;
        }}

        .profile-header {{
            position: relative;
            z-index: 2;

            display: flex;
            align-items: center;

            gap: 0.65rem;

            margin-bottom: 0.85rem;
        }}

        .profile-icon {{
            display: flex;

            align-items: center;
            justify-content: center;

            width: 39px;
            height: 39px;

            border-radius: 11px;

            background: {DEEP};
            color: #FFFFFF;

            font-size: 0.95rem;
            font-weight: 800;
        }}

        .profile-label {{
            color: #11899A;

            font-size: 0.56rem;
            font-weight: 800;

            letter-spacing: 0.13em;
            text-transform: uppercase;
        }}

        .profile-name {{
            color: {TEXT};

            font-size: 1.04rem;
            font-weight: 800;

            margin-top: 0.10rem;
        }}

        .status-pill {{
            display: inline-flex;

            margin-left: 0.40rem;

            padding:
                0.18rem
                0.40rem;

            border-radius: 999px;

            background: #E7F6F2;
            color: {SUCCESS};

            font-size: 0.52rem;
            font-weight: 800;

            vertical-align: middle;
        }}

        .profile-grid {{
            position: relative;
            z-index: 2;

            display: grid;

            grid-template-columns:
                repeat(4, minmax(0, 1fr));

            border:
                1px solid
                #E0EAED;

            border-radius: 11px;

            overflow: hidden;
        }}

        .profile-metric {{
            min-width: 0;

            padding:
                0.60rem
                0.68rem;

            border-right: 1px solid #E0EAED;
        }}

        .profile-metric:nth-child(4n) {{
            border-right: none;
        }}

        .profile-label {{
            color: #71878E;

            font-size: 0.53rem;
            font-weight: 800;

            letter-spacing: 0.08em;
            text-transform: uppercase;
        }}

        .profile-value {{
            color: {TEXT};

            font-size: 0.86rem;
            font-weight: 800;

            margin-top: 0.20rem;

            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        /* ==================================================
           INSIGHT
           ================================================== */

        .chart-insight {{
            margin:
                0.30rem
                0.85rem
                0.85rem;

            padding:
                0.55rem
                0.68rem;

            border:
                1px solid
                #D6E9ED;

            border-radius: 10px;

            background:
                linear-gradient(
                    120deg,
                    #F5FBFC 0%,
                    #EAF7F9 100%
                );

            color: #52727B;

            font-size: 0.61rem;
            line-height: 1.4;
        }}

        .dark-section .chart-insight {{
            background: rgba(255,255,255,0.055);
            border-color: rgba(255,255,255,0.09);
            color: rgba(255,255,255,0.66);
        }}

        .chart-insight strong {{
            color: #087C8A;
        }}

        .dark-section .chart-insight strong {{
            color: #70E0E5;
        }}

        /* ==================================================
           EMPTY STATE
           ================================================== */

        .regional-empty {{
            padding: 2rem 1rem;

            text-align: center;

            color: {MUTED};

            font-size: 0.74rem;
        }}

        /* ==================================================
           STREAMLIT SELECTBOX
           ================================================== */

        div[data-baseweb="select"] > div {{
            border-radius: 10px;
            border-color: #CFE3E7;
            background: #FFFFFF;
        }}

        /* ==================================================
           RESPONSIVE
           ================================================== */

        @media (max-width: 1000px) {{
            .abc-summary {{
                grid-template-columns: repeat(3, minmax(0, 1fr));
            }}


            .executive-kpi-grid {{
                grid-template-columns:
                    repeat(2, minmax(0, 1fr));
            }}

            .chart-grid,
            .growth-grid {{
                grid-template-columns: 1fr;
            }}

            .profile-grid {{
                grid-template-columns:
                    repeat(2, minmax(0, 1fr));
            }}

            .profile-metric:nth-child(4n) {{
                border-right: 1px solid #E0EAED;
            }}

            .profile-metric:nth-child(2n) {{
                border-right: none;
            }}

            .profile-metric:nth-child(-n+2) {{
                border-bottom: 1px solid #E0EAED;
            }}

            .profile-metric:nth-child(3),
            .profile-metric:nth-child(4) {{
                border-bottom: none;
            }}
        }}

        @media (max-width: 650px) {{
            .abc-region-row {{
                align-items: flex-start;
                flex-direction: column;
                gap: 0.15rem;
            }}

            .abc-region-meta {{
                text-align: left;
                white-space: normal;
            }}


            .abc-summary {{
                grid-template-columns: 1fr;
            }}


            .regional-floating-home {{
                left: 12px;
                bottom: 14px;
                min-height: 44px;
                padding-right: 13px;
            }}

            .regional-hero {{
                padding: 24px 20px;
                min-height: 170px;
            }}

            .regional-hero-asof {{
                right: 20px;
                top: 20px;
            }}

            .executive-kpi-grid {{
                grid-template-columns: 1fr;
            }}

            .profile-grid {{
                grid-template-columns: 1fr;
            }}

            .profile-metric,
            .profile-metric:nth-child(2n),
            .profile-metric:nth-child(4n) {{
                border-right: none;
                border-bottom: 1px solid #E0EAED;
            }}

            .profile-metric:last-child {{
                border-bottom: none;
            }}

            .regional-network {{
                right: 2%;
                opacity: 0.11;
            }}

        }}

        </style>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# CHART HELPERS
# ============================================================


def _base_chart_layout(
    height: int = 300,
    dark: bool = False,
) -> dict[str, Any]:
    """Return shared Plotly styling."""

    font_color = "#FFFFFF" if dark else TEXT
    grid_color = GRID_DARK if dark else "#E1ECEF"

    return {
        "height": height,
        "margin": {
            "l": 58,
            "r": 52,
            "t": 18,
            "b": 42,
        },
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {
            "family": "Arial, sans-serif",
            "size": 9,
            "color": font_color,
        },
        "showlegend": False,
        "xaxis": {
            "showgrid": True,
            "gridcolor": grid_color,
            "gridwidth": 1,
            "zeroline": False,
            "tickfont": {
                "family": "Arial, sans-serif",
                "size": 9,
                "color": font_color,
            },
        },
        "yaxis": {
            "showgrid": False,
            "zeroline": False,
            "tickfont": {
                "family": "Arial, sans-serif",
                "size": 9,
                "color": font_color,
            },
        },
    }


def _empty_figure(
    message: str,
    height: int = 300,
    dark: bool = False,
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
            "size": 10,
            "color": "#FFFFFF" if dark else MUTED,
        },
    )

    figure.update_layout(
        **_base_chart_layout(height, dark=dark)
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
    """Render a consistent intelligence section heading."""

    section_class = " dark-section" if dark else ""

    html = (
        f'<div class="section-heading{section_class}">'
        f'<div class="section-icon">{escape(icon)}</div>'
        '<div class="section-copy">'
        f'<div class="section-eyebrow">{escape(eyebrow)}</div>'
        f'<div class="section-title">{escape(title)}</div>'
        f'<div class="section-description">'
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


def render_page_header(
    latest_date: pd.Timestamp | None,
) -> None:
    """Render the Regional Intelligence hero."""

    date_text = (
        latest_date.strftime("%d %b %Y")
        if latest_date is not None
        else "No sales date available"
    )

    html = (
        '<section class="regional-hero">'

        '<div class="regional-hero-ring" '
        'style="width:330px;height:330px;'
        'right:-100px;bottom:-205px;"></div>'

        '<div class="regional-hero-ring" '
        'style="width:460px;height:460px;'
        'right:-165px;bottom:-285px;opacity:.62;"></div>'

        '<div class="regional-hero-ring" '
        'style="width:190px;height:190px;'
        'right:80px;top:-110px;opacity:.50;"></div>'

        '<div class="regional-network">'

        '<div class="regional-network-node" '
        'style="left:16px;top:52px;"></div>'

        '<div class="regional-network-node" '
        'style="left:66px;top:17px;"></div>'

        '<div class="regional-network-node" '
        'style="left:112px;top:46px;"></div>'

        '<div class="regional-network-node" '
        'style="left:73px;top:86px;"></div>'

        '<div class="regional-network-line" '
        'style="left:27px;top:58px;width:53px;'
        'transform:rotate(-35deg);"></div>'

        '<div class="regional-network-line" '
        'style="left:78px;top:23px;width:45px;'
        'transform:rotate(32deg);"></div>'

        '<div class="regional-network-line" '
        'style="left:27px;top:59px;width:48px;'
        'transform:rotate(34deg);"></div>'

        '<div class="regional-network-line" '
        'style="left:80px;top:90px;width:39px;'
        'transform:rotate(-43deg);"></div>'

        '</div>'

        '<div class="regional-hero-content">'

        '<div class="regional-hero-eyebrow">'
        'Regional Intelligence'
        '</div>'

        '<div class="regional-hero-title">'
        'Know where you grow.<br>'
        'Focus on the markets that matter.'
        '</div>'

        '<div class="regional-hero-description">'
        'Understand regional revenue, demand, growth and customer '
        'reach from a single geographic intelligence layer.'
        '</div>'

        '</div>'

        '<div class="regional-hero-asof">'
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
# EXECUTIVE KPIS
# ============================================================


def render_executive_kpis(
    engine: RegionalEngine,
) -> None:
    """Render four compact executive regional KPIs."""

    try:
        summary = engine.region_summary()
    except (
        KeyError,
        TypeError,
        ValueError,
    ):
        summary = pd.DataFrame()

    if summary.empty:
        return

    total_regions = len(summary)
    total_revenue = safe_float(summary["Revenue"].sum())
    total_orders = safe_float(summary["Orders"].sum())
    total_customers = safe_float(summary["Customers"].sum())

    metrics = [
        (
            "REGIONS",
            format_number(float(total_regions)),
            "Active regions in the sales footprint",
        ),
        (
            "REVENUE",
            format_currency(total_revenue),
            "Total recorded regional revenue",
        ),
        (
            "ORDERS",
            format_number(total_orders),
            "Distinct sales orders across regions",
        ),
        (
            "CUSTOMERS",
            format_number(total_customers),
            "Customer relationships across regions",
        ),
    ]

    cards_html = ""

    for label, value, note in metrics:
        cards_html += (
            '<div class="executive-kpi">'
            f'<div class="executive-kpi-label">'
            f'{escape(label)}'
            '</div>'
            f'<div class="executive-kpi-value">'
            f'{escape(value)}'
            '</div>'
            f'<div class="executive-kpi-note">'
            f'{escape(note)}'
            '</div>'
            '</div>'
        )

    html = (
        '<section class="executive-summary">'

        '<div class="executive-kicker">'
        'Regions'
        '</div>'

        '<div class="executive-title">'
        'Executive KPIs'
        '</div>'

        '<div class="executive-description">'
        'A quick view of regional scale, revenue, order volume and '
        'customer reach.'
        '</div>'

        f'<div class="executive-kpi-grid">'
        f'{cards_html}'
        '</div>'

        '</section>'
    )

    st.markdown(
        html,
        unsafe_allow_html=True,
    )


# ============================================================
# REGIONAL PERFORMANCE
# ============================================================


def _regional_bar_figure(
    dataframe: pd.DataFrame,
    value_column: str,
    label_column: str,
    value_label: str,
    currency: bool = False,
    dark: bool = False,
    height: int = 300,
) -> go.Figure:
    """Build a horizontal regional ranking chart."""

    if dataframe.empty:
        return _empty_figure(
            "Regional data is not available.",
            height,
            dark,
        )

    if (
        value_column not in dataframe.columns
        or label_column not in dataframe.columns
    ):
        return _empty_figure(
            "Regional data is not available.",
            height,
            dark,
        )

    plot = dataframe.copy()

    plot[value_column] = pd.to_numeric(
        plot[value_column],
        errors="coerce",
    ).fillna(0.0)

    plot = plot.sort_values(
        by=value_column,
        ascending=True,
    ).tail(8)

    labels = [
        _safe_text(value)
        for value in plot[label_column].tolist()
    ]

    values = [
        safe_float(value)
        for value in plot[value_column].tolist()
    ]

    axis_color = "#FFFFFF" if dark else TEXT

    if currency:
        text_values = [
            format_currency(value)
            for value in values
        ]

        hover = (
            f"<b>%{{y}}</b><br>"
            f"{escape(value_label)}: ₹%{{x:,.0f}}"
            "<extra></extra>"
        )
    else:
        text_values = [
            format_number(value)
            for value in values
        ]

        hover = (
            f"<b>%{{y}}</b><br>"
            f"{escape(value_label)}: %{{x:,.1f}}"
            "<extra></extra>"
        )

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
                "size": 9,
                "color": axis_color,
            },
            cliponaxis=False,
            hovertemplate=hover,
        )
    )

    figure.update_layout(
        **_base_chart_layout(
            height,
            dark=dark,
        )
    )

    figure.update_xaxes(
        tickprefix="₹" if currency else "",
        tickformat="~s",
    )

    figure.update_yaxes(
        automargin=True,
    )

    return figure


def render_regional_performance(
    engine: RegionalEngine,
) -> None:
    """Render regional revenue and customer footprint."""

    try:
        revenue = engine.top_regions_by_revenue(8)
    except (
        KeyError,
        TypeError,
        ValueError,
    ):
        revenue = pd.DataFrame()

    try:
        customers = engine.region_customer_distribution().head(8)
    except (
        KeyError,
        TypeError,
        ValueError,
    ):
        customers = pd.DataFrame()

    st.markdown(
        '<div class="chart-grid">',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<article class="chart-card">'
        '<div class="chart-title">'
        'Revenue by Region'
        '</div>'
        '<div class="chart-description">'
        'The regions contributing the highest recorded revenue.'
        '</div>'
        '<span class="chart-badge">Revenue</span>',
        unsafe_allow_html=True,
    )

    st.plotly_chart(
        _regional_bar_figure(
            revenue,
            "Revenue",
            "Region",
            "Revenue",
            currency=True,
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
        '<article class="chart-card">'
        '<div class="chart-title">'
        'Customer Footprint'
        '</div>'
        '<div class="chart-description">'
        'Regions with the broadest customer relationships.'
        '</div>'
        '<span class="chart-badge">Customers</span>',
        unsafe_allow_html=True,
    )

    st.plotly_chart(
        _regional_bar_figure(
            customers,
            "Customers",
            "Region",
            "Customers",
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


# ============================================================
# REGIONAL GROWTH
# ============================================================


def _growth_rows(
    dataframe: pd.DataFrame,
    positive: bool,
) -> str:
    """Build compact regional growth rows."""

    if dataframe.empty:
        return (
            '<div class="regional-empty">'
            'No comparable regional growth data is available.'
            '</div>'
        )

    rows = []

    for _, row in dataframe.head(6).iterrows():
        region = _safe_text(row.get("Region"))
        growth = safe_float(row.get("Growth %"))

        if growth == float("inf"):
            value = "New"
        else:
            value = f"{growth:+.1f}%"

        value_class = (
            "growth-positive"
            if positive
            else "growth-negative"
        )

        rows.append(
            '<div class="growth-region">'
            f'<div class="growth-region-name">'
            f'{escape(region)}'
            '</div>'
            f'<div class="growth-region-value '
            f'{value_class}">'
            f'{escape(value)}'
            '</div>'
            '</div>'
        )

    return "".join(rows)


def render_regional_growth(
    engine: RegionalEngine,
) -> None:
    """Render fastest-growing and declining regions with filter context."""

    growth_cutoff = 100000
    decline_cutoff = 100000

    try:
        growth_data = engine.regional_growth()
    except (
        KeyError,
        TypeError,
        ValueError,
    ):
        growth_data = pd.DataFrame()

    try:
        growing = engine.fastest_growing_regions(
            6,
            min_previous_revenue=growth_cutoff,
        )
    except (
        KeyError,
        TypeError,
        ValueError,
    ):
        growing = pd.DataFrame()

    try:
        declining = engine.declining_regions(
            6,
            min_current_revenue=decline_cutoff,
        )
    except (
        KeyError,
        TypeError,
        ValueError,
    ):
        declining = pd.DataFrame()

    qualifying_count = 0

    if not growth_data.empty:
        qualifying = growth_data[
            (growth_data["Growth %"] > 0)
            & (
                growth_data["Previous Revenue"]
                >= growth_cutoff
            )
        ]
        qualifying_count = len(qualifying)

    cutoff_text = format_currency(growth_cutoff)

    if qualifying_count == 0:
        growth_context = (
            f'No regions meet the positive-growth cutoff '
            f'of {escape(cutoff_text)} previous-month revenue.'
        )
    elif qualifying_count == 1:
        region_name = (
            _safe_text(growing.iloc[0].get("Region"))
            if not growing.empty
            else "One region"
        )

        growth_context = (
            f'<strong>Cutoff:</strong> positive month-over-month growth '
            f'with previous-month revenue ≥ {escape(cutoff_text)}. '
            f'{escape(region_name)} is the only qualifying region.'
        )
    else:
        growth_context = (
            f'<strong>Cutoff:</strong> positive month-over-month growth '
            f'with previous-month revenue ≥ {escape(cutoff_text)}. '
            f'{qualifying_count} regions qualify; showing the top 6.'
        )

    html = (
        '<div class="growth-grid">'

        '<article class="growth-card">'
        '<div class="growth-card-title">'
        'Fastest Growing Regions'
        '</div>'
        '<div class="growth-card-note">'
        'Positive month-over-month revenue movement.'
        '</div>'
        f'{_growth_rows(growing, positive=True)}'
        '<div class="growth-filter-note">'
        f'{growth_context}'
        '</div>'
        '</article>'

        '<article class="growth-card">'
        '<div class="growth-card-title">'
        'Declining Regions'
        '</div>'
        '<div class="growth-card-note">'
        'Negative month-over-month revenue movement.'
        f' Cutoff: current-month revenue ≥ '
        f'{escape(format_currency(decline_cutoff))}.'
        '</div>'
        f'{_growth_rows(declining, positive=False)}'
        '</article>'

        '</div>'
    )

    st.markdown(
        html,
        unsafe_allow_html=True,
    )

    try:
        monthly = engine.monthly_regional_sales()
    except (
        KeyError,
        TypeError,
        ValueError,
    ):
        monthly = pd.DataFrame()

    if monthly.empty:
        return

    months = (
        monthly["Month"]
        .dropna()
        .astype(str)
        .drop_duplicates()
        .sort_values()
        .tolist()
    )

    if not months:
        return

    recent_months = months[-12:]
    recent = monthly[
        monthly["Month"].astype(str).isin(recent_months)
    ].copy()

    trend = (
        recent.groupby("Month", as_index=False)
        .agg(Revenue=("Revenue", "sum"))
        .sort_values(by="Month")
        .reset_index(drop=True)
    )

    figure = go.Figure(
        go.Scatter(
            x=trend["Month"].tolist(),
            y=[
                safe_float(value)
                for value in trend["Revenue"].tolist()
            ],
            mode="lines+markers",
            line={
                "color": DEEP_2,
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
                "Regional revenue: ₹%{y:,.0f}"
                "<extra></extra>"
            ),
        )
    )

    figure.update_layout(
        **_base_chart_layout(250)
    )

    figure.update_xaxes(
        showgrid=False,
        tickangle=-25,
    )

    figure.update_yaxes(
        tickprefix="₹",
        tickformat="~s",
    )

    st.markdown(
        '<article class="chart-card" style="margin-top:0.85rem;">'
        '<div class="chart-title">Regional Revenue Trend</div>'
        '<div class="chart-description">'
        'Total revenue generated across the regional footprint over time.'
        '</div>'
        '<span class="chart-badge">Monthly</span>',
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


# ============================================================
# REGIONAL CONTRIBUTION
# ============================================================


def _render_abc_cards(
    abc: pd.DataFrame,
    pareto_count: int,
) -> None:
    """Render interactive ABC cards with a clear visual hierarchy."""

    if abc.empty:
        st.info("ABC regional classification is not available.")
        return

    total_revenue = safe_float(abc["Revenue"].sum())

    selected_class = st.session_state.get(
        "regional_abc_selected",
        None,
    )

    tier_labels = {
        "A": "HIGHEST-VALUE",
        "B": "MID-VALUE",
        "C": "LONG-TAIL",
    }

    tier_descriptions = {
        "A": "Regions carrying the bulk of total revenue.",
        "B": "Regions adding meaningful incremental revenue.",
        "C": "Long-tail markets with low individual contribution.",
    }

    with st.container(key="abc_structure"):
        st.markdown(
            '<div class="abc-section-top">'
            '<div class="abc-section-copy">'
            '<div class="abc-section-title">Regional ABC Structure</div>'
            '<div class="abc-section-description">'
            'Classify regions by cumulative revenue contribution. '
            'Click a class to inspect the regions inside it.'
            '</div>'
            '<span class="abc-section-badge">ABC Classification</span>'
            '</div>'
            '<div class="abc-rules">'
            '<div class="abc-rules-title">Classification logic</div>'
            '<strong>A</strong> ≤ 80% &nbsp;|&nbsp; '
            '<strong>B</strong> 80%–95% &nbsp;|&nbsp; '
            '<strong>C</strong> &gt; 95%'
            '</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        columns = st.columns(3, gap="small")

        for column, label in zip(columns, ("A", "B", "C")):
            rows = abc[
                abc["ABC Class"].astype(str).eq(label)
            ].copy()

            count = len(rows)

            share = (
                safe_float(rows["Revenue"].sum())
                / total_revenue
                * 100.0
                if not rows.empty and total_revenue > 0
                else 0.0
            )

            is_selected = selected_class == label

            container_key = (
                "abc_card_selected"
                if is_selected
                else f"abc_card_{label}"
            )

            action_text = (
                "Hide regions"
                if is_selected
                else "View regions →"
            )

            with column:
                with st.container(key=container_key):
                    st.markdown(
                        f'<div class="abc-card-letter">'
                        f'{escape(label)}'
                        f'</div>'
                        f'<div class="abc-card-label">'
                        f'{escape(tier_labels[label])}'
                        f'</div>'
                        f'<div class="abc-card-value">'
                        f'{escape(format_number(float(count)))} regions'
                        f'</div>'
                        f'<div class="abc-card-value">'
                        f'{escape(format_percentage(share))} revenue'
                        f'</div>'
                        f'<div class="abc-card-description">'
                        f'{escape(tier_descriptions[label])}'
                        f'</div>'
                        f'<div class="abc-card-divider"></div>',
                        unsafe_allow_html=True,
                    )

                    clicked = st.button(
                        action_text,
                        key=f"abc_card_button_{label}",
                        use_container_width=True,
                    )

            if clicked:
                st.session_state["regional_abc_selected"] = (
                    None
                    if is_selected
                    else label
                )
                st.rerun()

        if selected_class is not None:
            rows = abc[
                abc["ABC Class"].astype(str).eq(selected_class)
            ].copy()

            rows = (
                rows.sort_values(
                    by="Revenue",
                    ascending=False,
                )
                .reset_index(drop=True)
            )

            st.markdown(
                '<div class="abc-detail">'
                '<div class="abc-detail-header">'
                f'<div class="abc-detail-title">'
                f'Regions in Class {escape(selected_class)}'
                '</div>'
                f'<div class="abc-detail-count">'
                f'{len(rows)} regions'
                '</div>'
                '</div>'
                '<div class="abc-detail-note">'
                'Ordered from highest to lowest revenue. '
                'Share shows each region’s contribution to total revenue; '
                'cumulative % shows its position in the concentration curve.'
                '</div>'
                '<div class="abc-table-header">'
                '<span>Rank</span>'
                '<span>Region</span>'
                '<span>Revenue</span>'
                '<span>Share</span>'
                '<span>Cumulative</span>'
                '</div>',
                unsafe_allow_html=True,
            )

            for _, row in rows.iterrows():
                rank = int(
                    safe_float(
                        row.get("Rank"),
                        float(len(rows)),
                    )
                )
                region = _safe_text(row.get("Region"))
                revenue = safe_float(row.get("Revenue"))
                share = (
                    revenue / total_revenue * 100.0
                    if total_revenue > 0
                    else 0.0
                )
                cumulative = safe_float(
                    row.get("Cumulative Contribution %")
                )

                st.markdown(
                    '<div class="abc-region-row">'
                    f'<span class="abc-region-rank">{rank}</span>'
                    f'<span class="abc-region-name">{escape(region)}</span>'
                    f'<span class="abc-region-meta">'
                    f'{escape(format_currency(revenue))}'
                    '</span>'
                    f'<span class="abc-region-meta">'
                    f'{escape(format_percentage(share))}'
                    '</span>'
                    f'<span class="abc-region-meta">'
                    f'{escape(format_percentage(cumulative))}'
                    '</span>'
                    '</div>',
                    unsafe_allow_html=True,
                )

            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown(
            '<div class="abc-coverage">'
            '<span>'
            '<strong>80% coverage:</strong> '
            f'{escape(format_number(float(pareto_count)))} '
            'regions reach the 80% cumulative revenue threshold.'
            '</span>'
            '<span>Click any class card to view its regions.</span>'
            '</div>',
            unsafe_allow_html=True,
        )


def render_regional_contribution(
    engine: RegionalEngine,
) -> None:
    """Render regional Pareto contribution and ABC classification."""

    try:
        contribution = engine.regional_contribution()
    except (
        KeyError,
        TypeError,
        ValueError,
    ):
        contribution = pd.DataFrame()

    try:
        abc = engine.abc_region_analysis()
    except (
        KeyError,
        TypeError,
        ValueError,
    ):
        abc = pd.DataFrame()

    if contribution.empty:
        st.info("Regional contribution data is not available.")
        return

    plot = contribution.head(20).copy()

    x_values = list(
        range(1, len(plot) + 1)
    )

    revenue_values = [
        safe_float(value)
        for value in plot["Revenue"].tolist()
    ]

    cumulative_values = [
        safe_float(value)
        for value in plot[
            "Cumulative Contribution %"
        ].tolist()
    ]

    figure = go.Figure()

    figure.add_bar(
        x=x_values,
        y=revenue_values,
        name="Revenue",
        marker_color="#1599A8",
        opacity=0.78,
        hovertemplate=(
            "Region rank: %{x}<br>"
            "Revenue: ₹%{y:,.0f}"
            "<extra></extra>"
        ),
    )

    figure.add_scatter(
        x=x_values,
        y=cumulative_values,
        name="Cumulative %",
        yaxis="y2",
        mode="lines+markers",
        line={
            "color": "#45D5DC",
            "width": 2.5,
        },
        marker={
            "color": "#31C4D0",
            "size": 4,
        },
        hovertemplate=(
            "Region rank: %{x}<br>"
            "Cumulative: %{y:.1f}%"
            "<extra></extra>"
        ),
    )

    figure.add_hline(
        y=80,
        line_dash="dash",
        line_color="rgba(255,255,255,0.38)",
        annotation_text="80%",
        annotation_font={
            "size": 9,
            "color": "rgba(255,255,255,0.70)",
        },
    )

    figure.update_layout(
        height=300,
        margin={
            "l": 58,
            "r": 62,
            "t": 32,
            "b": 48,
        },
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={
            "family": "Arial, sans-serif",
            "size": 8,
            "color": "#FFFFFF",
        },
        showlegend=True,
        legend={
            "orientation": "h",
            "x": 0.5,
            "xanchor": "center",
            "y": 1.10,
            "font": {
                "size": 8,
                "color": "rgba(255,255,255,0.72)",
            },
        },
        xaxis={
            "showgrid": False,
            "tickfont": {
                "size": 7,
                "color": "rgba(255,255,255,0.52)",
            },
            "title": {
                "text": "Region Rank",
                "font": {
                    "size": 9,
                    "color": "rgba(255,255,255,0.72)",
                },
            },
        },
        yaxis={
            "tickprefix": "₹",
            "showgrid": True,
            "gridcolor": "rgba(255,255,255,0.09)",
            "zeroline": False,
            "tickfont": {
                "size": 7,
                "color": "rgba(255,255,255,0.52)",
            },
            "title": {
                "text": "Revenue",
                "font": {
                    "size": 9,
                    "color": "rgba(255,255,255,0.72)",
                },
            },
        },
        yaxis2={
            "overlaying": "y",
            "side": "right",
            "range": [0, 100],
            "ticksuffix": "%",
            "showgrid": False,
            "tickfont": {
                "size": 7,
                "color": "rgba(255,255,255,0.52)",
            },
            "title": {
                "text": "Cumulative %",
                "font": {
                    "size": 9,
                    "color": "rgba(255,255,255,0.72)",
                },
            },
        },
    )

    st.markdown(
        '<div class="chart-grid">',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<article class="chart-card">'
        '<div class="chart-title">'
        'Regional Revenue Concentration'
        '</div>'
        '<div class="chart-description">'
        'See how quickly the highest-value regions accumulate revenue.'
        '</div>'
        '<span class="chart-badge">Pareto</span>',
        unsafe_allow_html=True,
    )

    st.plotly_chart(
        figure,
        use_container_width=True,
        config={"displayModeBar": False},
    )

    st.markdown(
        '</article></div>',
        unsafe_allow_html=True,
    )

    pareto_regions = engine.pareto_regions(80)

    pareto_count = len(pareto_regions)

    _render_abc_cards(
        abc,
        pareto_count,
    )


# ============================================================
# REGIONAL DEMAND
# ============================================================


def _render_region_table(
    dataframe: pd.DataFrame,
) -> None:
    """Render a compact top-region table."""

    if dataframe.empty:
        st.info("Regional ranking data is not available.")
        return

    rows = []

    for _, row in dataframe.head(8).iterrows():
        rank = safe_float(row.get("Rank"))
        region = _safe_text(row.get("Region"))
        revenue = safe_float(row.get("Revenue"))
        orders = safe_float(row.get("Orders"))

        rows.append(
            '<tr>'
            '<td>'
            f'<span class="rank-pill">{int(rank)}</span>'
            '</td>'
            f'<td class="region-name">'
            f'{escape(region)}'
            '</td>'
            f'<td class="region-value">'
            f'{escape(format_currency(revenue))}'
            '</td>'
            f'<td class="region-value">'
            f'{escape(format_number(orders))}'
            '</td>'
            '</tr>'
        )

    html = (
        '<table class="regional-table">'
        '<thead>'
        '<tr>'
        '<th>#</th>'
        '<th>Region</th>'
        '<th>Revenue</th>'
        '<th>Orders</th>'
        '</tr>'
        '</thead>'
        '<tbody>'
        + "".join(rows)
        + '</tbody>'
        '</table>'
    )

    st.markdown(
        html,
        unsafe_allow_html=True,
    )


def render_regional_demand(
    engine: RegionalEngine,
) -> None:
    """Render regional demand and order-value views."""

    try:
        summary = engine.region_summary()
    except (
        KeyError,
        TypeError,
        ValueError,
    ):
        summary = pd.DataFrame()

    try:
        aov = engine.regional_average_order_value()
    except (
        KeyError,
        TypeError,
        ValueError,
    ):
        aov = pd.DataFrame()

    left, right = st.columns(
        2,
        gap="medium",
    )

    with left:
        st.markdown(
            '<article class="chart-card">'
            '<div class="chart-title">'
            'Regional Revenue Ranking'
            '</div>'
            '<div class="chart-description">'
            'A compact view of the highest-value regional markets.'
            '</div>'
            '<span class="chart-badge">Ranking</span>',
            unsafe_allow_html=True,
        )

        _render_region_table(summary)

        st.markdown(
            '</article>',
            unsafe_allow_html=True,
        )

    with right:
        st.markdown(
            '<article class="chart-card">'
            '<div class="chart-title">'
            'Average Order Value by Region'
            '</div>'
            '<div class="chart-description">'
            'Compare revenue generated per order across markets.'
            '</div>'
            '<span class="chart-badge">AOV</span>',
            unsafe_allow_html=True,
        )

        st.plotly_chart(
            _regional_bar_figure(
                aov.head(8),
                "Average Order Value",
                "Region",
                "Average order value",
                currency=True,
                height=320,
            ),
            use_container_width=True,
            config={"displayModeBar": False},
        )

        st.markdown(
            '</article>',
            unsafe_allow_html=True,
        )


# ============================================================
# REGION EXPLORER
# ============================================================


def _profile_metric(
    label: str,
    value: str,
) -> str:
    """Build a region profile metric."""

    return (
        '<div class="profile-metric">'
        f'<div class="profile-label">{escape(label)}</div>'
        f'<div class="profile-value">{escape(value)}</div>'
        '</div>'
    )


def render_region_lookup(
    engine: RegionalEngine,
) -> None:
    """Render selected-region profile and product demand."""

    try:
        regions = engine.get_regions()
    except (
        KeyError,
        TypeError,
        ValueError,
    ):
        regions = []

    if not regions:
        st.markdown(
            '<div class="regional-empty">'
            'No regions are available for exploration.'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    selected_region = st.selectbox(
        "Select a region",
        regions,
        index=0,
        key="regional_dashboard_selector",
    )

    try:
        detail = engine.region_details(
            selected_region
        )
    except (
        KeyError,
        TypeError,
        ValueError,
    ) as exc:
        st.warning(
            f"Region profile is not available: {exc}"
        )
        return

    top_product = _safe_text(
        detail.get("Top Product"),
        "No product",
    )

    profile_html = (
        '<div class="profile-card">'

        '<div class="profile-watermark">'
        '<div class="profile-wave one"></div>'
        '<div class="profile-wave two"></div>'
        '</div>'

        '<div class="profile-header">'
        '<div class="profile-icon">⌖</div>'
        '<div>'
        '<div class="profile-label">'
        'Regional Profile'
        '</div>'
        '<div class="profile-name">'
        f'{escape(_safe_text(detail.get("Region")))}'
        '<span class="status-pill">'
        'Active'
        '</span>'
        '</div>'
        '</div>'
        '</div>'

        '<div class="profile-grid">'

        + _profile_metric(
            "Revenue",
            format_currency(
                safe_float(detail.get("Revenue"))
            ),
        )

        + _profile_metric(
            "Quantity",
            format_number(
                safe_float(detail.get("Quantity"))
            ),
        )

        + _profile_metric(
            "Orders",
            format_number(
                safe_float(detail.get("Orders"))
            ),
        )

        + _profile_metric(
            "Customers",
            format_number(
                safe_float(detail.get("Customers"))
            ),
        )

        + _profile_metric(
            "Average Order Value",
            format_currency(
                safe_float(
                    detail.get("Average Order Value")
                )
            ),
        )

        + _profile_metric(
            "Revenue Contribution",
            format_percentage(
                safe_float(
                    detail.get(
                        "Revenue Contribution %"
                    )
                )
            ),
        )

        + _profile_metric(
            "Top Product",
            top_product,
        )

        + _profile_metric(
            "Top Product Revenue",
            format_currency(
                safe_float(
                    detail.get(
                        "Top Product Revenue"
                    )
                )
            ),
        )

        + '</div>'
        '</div>'
    )

    st.markdown(
        profile_html,
        unsafe_allow_html=True,
    )

    try:
        products = engine.top_products_by_region(
            selected_region,
            8,
        )
    except (
        KeyError,
        TypeError,
        ValueError,
    ):
        products = pd.DataFrame()

    if not products.empty:
        figure = _regional_bar_figure(
            products,
            "Quantity",
            "Product",
            "Units",
            dark=False,
            height=310,
        )

        st.markdown(
            '<article class="chart-card" '
            'style="margin-top:0.85rem;">'
            '<div class="chart-title">'
            'Top Products in Selected Region'
            '</div>'
            '<div class="chart-description">'
            'Products generating the highest unit demand in this market.'
            '</div>'
            '<span class="chart-badge">Demand</span>',
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

    try:
        monthly = engine.monthly_regional_sales()
    except (
        KeyError,
        TypeError,
        ValueError,
    ):
        monthly = pd.DataFrame()

    if not monthly.empty:
        selected_monthly = monthly[
            monthly["Region"].astype(str).eq(
                str(selected_region)
            )
        ].copy()

        if not selected_monthly.empty:
            selected_monthly = (
                selected_monthly
                .sort_values(by="Month")
                .tail(12)
            )

            figure = go.Figure(
                go.Scatter(
                    x=selected_monthly["Month"].tolist(),
                    y=[
                        safe_float(value)
                        for value in selected_monthly[
                            "Revenue"
                        ].tolist()
                    ],
                    mode="lines+markers",
                    line={
                        "color": DEEP_2,
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
                **_base_chart_layout(260)
            )

            figure.update_xaxes(
                showgrid=False,
                tickangle=-25,
            )

            figure.update_yaxes(
                tickprefix="₹",
                tickformat="~s",
            )

            st.markdown(
                '<article class="chart-card" '
                'style="margin-top:0.85rem;">'
                '<div class="chart-title">'
                'Selected Region Revenue Trend'
                '</div>'
                '<div class="chart-description">'
                'Monthly revenue history for the selected market.'
                '</div>'
                '<span class="chart-badge">Monthly</span>',
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


# ============================================================
# EMPTY STATE
# ============================================================


def render_empty_state() -> None:
    """Render a clean empty state."""

    st.markdown(
        '<div class="regional-empty">'
        'Regional sales data is not available yet.'
        '</div>',
        unsafe_allow_html=True,
    )


# ============================================================
# MAIN DASHBOARD
# ============================================================


def render_regional_dashboard(
    on_back: Callable[[], None] | None = None,
) -> None:
    """Render the Regional Intelligence dashboard."""

    del on_back

    apply_theme(
        "AQVASTAR | Regional Intelligence"
    )

    inject_dashboard_css()

    render_brand()
    render_navigation("regions")

    st.markdown(
        '<a href="?page=home" '
        'target="_self" '
        'class="regional-floating-home" '
        'aria-label="Back to Home">'
        '<span class="regional-floating-home-icon">⌂</span>'
        '<span class="regional-floating-home-text">'
        'BACK TO HOME'
        '</span>'
        '</a>',
        unsafe_allow_html=True,
    )

    try:
        engine = RegionalEngine()
    except (
        KeyError,
        TypeError,
        ValueError,
    ) as exc:
        st.error(
            f"Regional engine could not be initialized: {exc}"
        )
        return

    try:
        monthly = engine.monthly_regional_sales()
    except (
        KeyError,
        TypeError,
        ValueError,
    ):
        monthly = pd.DataFrame()

    latest_date: pd.Timestamp | None = None

    if not monthly.empty and "Month" in monthly.columns:
        values = (
            monthly["Month"]
            .dropna()
            .astype(str)
            .tolist()
        )

        if values:
            parsed = pd.to_datetime(
                max(values),
                format="%Y-%m",
                errors="coerce",
            )

            if isinstance(parsed, pd.Timestamp):
                latest_date = parsed

    render_page_header(latest_date)

    try:
        summary = engine.region_summary()
    except (
        KeyError,
        TypeError,
        ValueError,
    ):
        summary = pd.DataFrame()

    if summary.empty:
        render_empty_state()
        return

    # ========================================================
    # EXECUTIVE SUMMARY
    # ========================================================

    render_executive_kpis(engine)

    # ========================================================
    # REGIONAL PERFORMANCE
    # ========================================================

    with st.container(
        key="regional_performance_section"
    ):
        render_section_heading(
            "Regional Performance",
            "Where is revenue coming from?",
            (
                "Compare regional revenue and customer reach "
                "across the current sales footprint."
            ),
            "⌖",
            dark=True,
        )

        render_regional_performance(engine)

    # ========================================================
    # REGIONAL GROWTH
    # ========================================================

    with st.container(
        key="regional_growth_section"
    ):
        render_section_heading(
            "Regional Growth",
            "Which markets are accelerating or declining?",
            (
                "Track month-over-month movement and identify "
                "the regions changing fastest."
            ),
            "↗",
        )

        render_regional_growth(engine)

    # ========================================================
    # REGIONAL CONTRIBUTION
    # ========================================================

    with st.container(
        key="regional_contribution_section"
    ):
        render_section_heading(
            "Regional Contribution",
            "How concentrated is the geographic footprint?",
            (
                "Use Pareto and ABC analysis to understand how "
                "regional markets contribute to total revenue."
            ),
            "◔",
            dark=True,
        )

        render_regional_contribution(engine)

    # ========================================================
    # REGIONAL DEMAND
    # ========================================================

    with st.container(
        key="regional_demand_section"
    ):
        render_section_heading(
            "Regional Demand",
            "What does each market actually buy?",
            (
                "Compare regional rankings and average order value "
                "to understand market quality."
            ),
            "▥",
        )

        render_regional_demand(engine)

    # ========================================================
    # REGION LOOKUP
    # ========================================================

    with st.container(
        key="regional_lookup_section"
    ):
        render_section_heading(
            "Region Explorer",
            "Drill into an individual market",
            (
                "Select a region to view its commercial profile, "
                "top products and revenue history."
            ),
            "⌕",
        )

        render_region_lookup(engine)


def main() -> None:
    """Render the AQVASTAR Regional Intelligence dashboard."""

    render_regional_dashboard()


if __name__ == "__main__":
    main()