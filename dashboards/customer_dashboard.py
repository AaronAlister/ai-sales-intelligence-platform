"""
AQVASTAR Sales Intelligence Platform.

Customer Intelligence Dashboard.

UI rebuilt to match the supplied AQVASTAR Customer Intelligence reference:
- compact hero banner
- integrated section cards
- dark/light alternating intelligence panels
- executive customer KPIs
- key-account ranking table
- customer profile lookup
- customer value charts
- customer lifecycle and acquisition
- loyalty metrics
- ABC / Pareto revenue contribution
"""

from __future__ import annotations

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
from engines.customer_engine import CustomerEngine
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
SUCCESS = "#0B8D80"

SHADOW = "0 10px 28px rgba(5, 57, 70, 0.07)"
SHADOW_DARK = "0 14px 34px rgba(2, 42, 53, 0.15)"


# ============================================================
# FORMATTERS
# ============================================================


def format_currency(value: float) -> str:
    """Format a number using compact Indian dashboard currency notation."""

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
    """Format a dashboard number."""

    numeric_value = float(value)

    if numeric_value.is_integer():
        return f"{int(numeric_value):,}"

    return f"{numeric_value:,.1f}"


def format_percentage(value: float) -> str:
    """Format a percentage with two decimal places."""

    return f"{float(value):.2f}%"


# ============================================================
# SAFE DATA HELPERS
# ============================================================


def _find_column(
    dataframe: pd.DataFrame,
    candidates: tuple[str, ...],
) -> str | None:
    """Return the first available column from the supplied candidates."""

    for candidate in candidates:
        if candidate in dataframe.columns:
            return candidate

    lowered = {
        str(column).strip().lower(): str(column)
        for column in dataframe.columns
    }

    for candidate in candidates:
        match = lowered.get(candidate.strip().lower())
        if match is not None:
            return match

    return None


def _numeric_series(
    dataframe: pd.DataFrame,
    column: str | None,
) -> pd.Series:
    """Return a safe numeric series."""

    if column is None:
        return pd.Series(
            0.0,
            index=dataframe.index,
            dtype="float64",
        )

    return pd.to_numeric(
        dataframe[column],
        errors="coerce",
    ).fillna(0.0)


def _safe_float(
    value: Any,
    default: float = 0.0,
) -> float:
    """Convert a value to float without raising."""

    try:
        numeric_value = float(value)

        if pd.isna(numeric_value):
            return default

        return numeric_value
    except (TypeError, ValueError):
        return default


def _safe_text(
    value: Any,
    default: str = "N/A",
) -> str:
    """Convert a value to display text without raising."""

    if value is None:
        return default

    try:
        if pd.isna(value):
            return default
    except (TypeError, ValueError):
        pass

    text = str(value).strip()
    return text if text else default


def _call_dataframe_method(
    engine: CustomerEngine,
    method_name: str,
    *args: Any,
) -> pd.DataFrame:
    """Safely call an engine method expected to return a dataframe."""

    try:
        method = getattr(engine, method_name, None)

        if not callable(method):
            return pd.DataFrame()

        result = method(*args)

        if isinstance(result, pd.DataFrame):
            return result.copy()

    except (
        AttributeError,
        KeyError,
        TypeError,
        ValueError,
    ):
        pass

    return pd.DataFrame()


# ============================================================
# GLOBAL CSS
# ============================================================


def inject_dashboard_css() -> None:
    """Inject the complete Customer Intelligence visual system."""

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

        .customer-floating-home {{
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

        .customer-floating-home:hover {{
            transform: translateY(-3px);
            border-color: {AQUA};
            box-shadow: 0 16px 36px rgba(4,62,76,0.22);
            color: #087C8A !important;
        }}

        .customer-floating-home-icon {{
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

        .customer-floating-home-text {{
            white-space: nowrap;
        }}

        /* Hide Streamlit's default container border where it
           is not needed, while keeping our keyed section cards. */

        .st-key-customer_lookup_section,
        .st-key-key_accounts_section,
        .st-key-customer_value_section,
        .st-key-customer_activity_section,
        .st-key-customer_loyalty_section,
        .st-key-revenue_contribution_section {{
            position: relative;
            overflow: hidden;
            border-radius: 20px;
            margin-top: 1.05rem;
            margin-bottom: 1.45rem;
            padding: 1.25rem 1.35rem 2.05rem;
        }}

        .st-key-customer_lookup_section,
        .st-key-customer_value_section,
        .st-key-customer_activity_section {{
            background: linear-gradient(
                145deg,
                #F7FCFD 0%,
                #EAF7F9 100%
            );
            border: 1px solid #D8EAEE;
            box-shadow: {SHADOW};
        }}

        .st-key-key_accounts_section,
        .st-key-customer_loyalty_section,
        .st-key-revenue_contribution_section {{
            background:
                radial-gradient(
                    circle at 100% 0%,
                    rgba(40, 192, 204, 0.13),
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

        /* ==================================================
           HERO
           ================================================== */

        .customer-hero {{
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
            box-shadow: 0 14px 34px rgba(5, 60, 74, 0.14);
        }}

        .customer-hero-content {{
            position: relative;
            z-index: 3;
            max-width: 760px;
        }}

        .customer-hero-eyebrow {{
            color: #3BD0D8;
            font-size: 0.60rem;
            font-weight: 800;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            margin-bottom: 0.58rem;
        }}

        .customer-hero-title {{
            color: #FFFFFF;
            font-size: clamp(1.85rem, 3.1vw, 3rem);
            line-height: 1.02;
            font-weight: 800;
            letter-spacing: -0.045em;
            margin-bottom: 0.62rem;
        }}

        .customer-hero-description {{
            max-width: 620px;
            color: rgba(255,255,255,0.76);
            font-size: 0.76rem;
            line-height: 1.45;
        }}

        .customer-hero-asof {{
            position: absolute;
            right: 2.25rem;
            top: 2rem;
            z-index: 4;

            color: rgba(255,255,255,0.62);

            font-size: 0.65rem;
            line-height: 1.4;
            text-align: right;
        }}

        .customer-hero-asof strong {{
            display: block;
            color: #FFFFFF;
            font-size: 0.75rem;
            margin-top: 0.15rem;
        }}

        .hero-ring {{
            position: absolute;
            border: 1px solid rgba(255,255,255,0.13);
            border-radius: 50%;
            pointer-events: none;
        }}

        .hero-person {{
            position: absolute;
            z-index: 1;
            right: 8%;
            top: 25px;
            width: 120px;
            height: 92px;
            opacity: 0.20;
        }}

        .hero-person .head {{
            position: absolute;
            width: 28px;
            height: 28px;
            border-radius: 50%;
            background: #A8E8ED;
        }}

        .hero-person .head.one {{
            left: 45px;
            top: 0;
        }}

        .hero-person .head.two {{
            left: 10px;
            top: 15px;
            width: 22px;
            height: 22px;
        }}

        .hero-person .head.three {{
            right: 10px;
            top: 15px;
            width: 22px;
            height: 22px;
        }}

        .hero-person .body {{
            position: absolute;
            left: 30px;
            top: 29px;
            width: 62px;
            height: 54px;
            border-radius: 36px 36px 8px 8px;
            background: #A8E8ED;
        }}

        .hero-person .body.small {{
            left: 0;
            top: 39px;
            width: 44px;
            height: 40px;
        }}

        .hero-person .body.small.right {{
            left: auto;
            right: 0;
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
            box-shadow: inset 0 0 0 1px rgba(255,255,255,0.12);
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
            font-size: 0.76rem;
            line-height: 1.42;
            margin-top: 0.22rem;
        }}

        .dark-section .section-description {{
            color: rgba(255,255,255,0.66);
        }}

        /* ==================================================
           SELECTBOX
           ================================================== */

        .st-key-customer_lookup_section [data-testid="stSelectbox"] {{
            position: relative;
            z-index: 5;
            margin: 0.05rem 0 0.85rem;
        }}

        .st-key-customer_lookup_section
        [data-testid="stSelectbox"] label {{
            color: {MUTED} !important;
            font-size: 0.68rem !important;
            font-weight: 800 !important;
            letter-spacing: 0.10em !important;
            text-transform: uppercase !important;
        }}

        .st-key-customer_lookup_section
        [data-baseweb="select"] > div {{
            min-height: 39px;
            border-radius: 10px;
            border: 1px solid #CFE1E5;
            background: #FFFFFF;
            box-shadow: none;
        }}

        .st-key-customer_lookup_section
        [data-baseweb="select"] * {{
            font-size: 0.82rem;
        }}

        /* ==================================================
           CUSTOMER PROFILE
           ================================================== */

        .profile-card {{
            position: relative;
            overflow: hidden;
            border: 1px solid {BORDER};
            border-radius: 15px;
            background: #FFFFFF;
            box-shadow: 0 7px 20px rgba(6,59,73,0.05);
        }}

        .profile-header {{
            position: relative;
            z-index: 2;
            display: flex;
            align-items: center;
            gap: 0.72rem;
            padding: 0.82rem 0.9rem;
            border-bottom: 1px solid {BORDER};
        }}

        .profile-icon {{
            width: 43px;
            height: 43px;
            min-width: 43px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            background: {AQUA_SOFT};
            color: {OCEAN};
            font-size: 1rem;
            font-weight: 800;
        }}

        .profile-label {{
            color: #188A9A;
            font-size: 0.53rem;
            font-weight: 800;
            letter-spacing: 0.13em;
            text-transform: uppercase;
            margin-bottom: 0.14rem;
        }}

        .profile-name {{
            color: {TEXT};
            font-size: 0.94rem;
            line-height: 1.15;
            font-weight: 800;
        }}

        .status-pill {{
            display: inline-block;
            margin-left: 0.35rem;
            padding: 0.17rem 0.42rem;
            border-radius: 999px;
            background: #E4F7F3;
            color: {SUCCESS};
            font-size: 0.57rem;
            font-weight: 800;
            vertical-align: middle;
        }}

        .profile-watermark {{
            position: absolute;
            right: -5px;
            top: -22px;
            width: 190px;
            height: 85px;
            opacity: 0.32;
            pointer-events: none;
        }}

        .wave {{
            position: absolute;
            width: 210px;
            height: 55px;
            border-top: 1px solid #B7E5EA;
            border-radius: 50%;
            transform: rotate(-6deg);
        }}

        .wave.one {{
            top: 24px;
            right: -20px;
        }}

        .wave.two {{
            top: 36px;
            right: -18px;
            width: 185px;
        }}

        .profile-grid {{
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
        }}

        .profile-metric {{
            min-width: 0;
            padding: 0.72rem 0.78rem;
            border-right: 1px solid {BORDER};
            border-bottom: 1px solid {BORDER};
        }}

        .profile-metric:nth-child(4n) {{
            border-right: none;
        }}

        .profile-metric:nth-last-child(-n+3) {{
            border-bottom: none;
        }}

        .metric-label {{
            color: {MUTED};
            font-size: 0.57rem;
            font-weight: 800;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 0.18rem;
        }}

        .metric-value {{
            color: {TEXT};
            font-size: 0.92rem;
            line-height: 1.1;
            font-weight: 800;
        }}

        /* ==================================================
           KEY ACCOUNT TABLE
           ================================================== */

        .account-table {{
            position: relative;
            z-index: 2;
            overflow: hidden;
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 13px;
            background: rgba(2, 44, 55, 0.40);
        }}

        .account-row {{
            display: grid;
            grid-template-columns:
                minmax(0, 1.8fr)
                minmax(105px, 0.65fr)
                minmax(145px, 0.9fr);
            align-items: center;
            min-height: 37px;
            padding: 0.35rem 0.7rem;
            border-top: 1px solid rgba(255,255,255,0.065);
        }}

        .account-row.header {{
            min-height: 30px;
            border-top: none;
            background: rgba(255,255,255,0.075);
        }}

        .account-header {{
            color: rgba(255,255,255,0.58);
            font-size: 0.62rem;
            font-weight: 800;
            letter-spacing: 0.11em;
            text-transform: uppercase;
        }}

        .account-name {{
            overflow: hidden;
            color: #FFFFFF;
            font-size: 0.62rem;
            font-weight: 650;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}

        .account-rank {{
            display: inline-flex;
            width: 22px;
            height: 22px;
            margin-right: 0.38rem;
            align-items: center;
            justify-content: center;
            border-radius: 7px;
            background: rgba(255,255,255,0.08);
            color: rgba(255,255,255,0.68);
            font-size: 0.57rem;
            font-weight: 800;
        }}

        .account-rank.top {{
            background: #13A9B6;
            color: #FFFFFF;
        }}

        .account-value {{
            color: #FFFFFF;
            font-size: 0.61rem;
            font-weight: 750;
            text-align: right;
        }}

        .account-contribution {{
            display: flex;
            align-items: center;
            justify-content: flex-end;
            gap: 0.45rem;
        }}

        .account-percentage {{
            min-width: 52px;
            color: #3BD0D8;
            font-size: 0.58rem;
            font-weight: 800;
            text-align: right;
        }}

        .account-bar-track {{
            display: block;
            width: 96px;
            height: 8px;
            overflow: hidden;
            border-radius: 999px;
            background: rgba(255,255,255,0.09);
        }}

        .account-bar {{
            display: block;
            width: 0;
            height: 100%;
            border-radius: 999px;
            background: #18B8C5;
        }}

        /* ==================================================
           INSIGHT STRIP
           ================================================== */

        .insight-strip {{
            position: relative;
            z-index: 2;
            display: flex;
            align-items: flex-start;
            gap: 0.6rem;
            margin-top: 0.82rem;
            margin-bottom: 0.12rem;
            padding: 0.68rem 0.72rem;
            border-radius: 10px;
            border: 1px solid #D6E9EC;
            background: #F1FAFB;
            color: {MUTED};
            font-size: 0.62rem;
            line-height: 1.38;
        }}

        .dark-insight {{
            border-color: rgba(48,202,213,0.18);
            background: rgba(15,170,186,0.10);
            color: rgba(255,255,255,0.70);
        }}

        .insight-icon {{
            width: 27px;
            height: 27px;
            min-width: 27px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            background: #13A9B6;
            color: #FFFFFF;
            font-size: 0.82rem;
            font-weight: 800;
        }}

        .insight-label {{
            color: #1595A5;
            font-size: 0.62rem;
            font-weight: 800;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            margin-bottom: 0.08rem;
        }}

        .dark-insight .insight-label {{
            color: #3BD0D8;
        }}

        .insight-value {{
            color: #1195A4;
            font-weight: 800;
        }}

        .dark-insight .insight-value {{
            color: #3BD0D8;
        }}

        /* ==================================================
           CHART CARDS
           ================================================== */

        .chart-card {{
            position: relative;
            overflow: hidden;
            padding: 0.95rem 1rem;
            margin-bottom: 0.45rem;
            border: 1px solid {BORDER};
            border-radius: 13px;
            background: #FFFFFF;
            box-shadow: 0 6px 18px rgba(7,63,76,0.045);
        }}

        .chart-plot-gap {{
            height: 0.75rem;
        }}

        .chart-title {{
            color: {TEXT};
            font-size: 0.82rem;
            font-weight: 800;
            line-height: 1.2;
        }}

        .chart-description {{
            color: {MUTED};
            font-size: 0.62rem;
            line-height: 1.35;
            margin-top: 0.12rem;
        }}

        .activity-chart-heading {{
            position: relative;
            margin-top: 1.25rem;
            margin-bottom: 0.75rem;
            padding: 0.18rem 0 0.18rem 0.85rem;
            border-left: 4px solid #14A9B8;
        }}

        .activity-chart-heading .chart-title {{
            color: #087F91;
            font-size: 0.90rem;
        }}

        .activity-chart-heading .chart-description {{
            color: #4E7280;
            font-size: 0.68rem;
            margin-top: 0.16rem;
        }}

        .chart-insight {{
            margin-top: 1.15rem;
            margin-bottom: 0.30rem;
            padding: 0.68rem 0.72rem;
            border: 1px solid #D8EAED;
            border-radius: 9px;
            background: {AQUA_SOFT};
            color: {MUTED};
            font-size: 0.64rem;
            line-height: 1.38;
        }}

        .chart-insight strong {{
            color: {OCEAN};
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
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.65rem;
        }}

        .executive-kpi {{
            min-width: 0;
            padding: 0.78rem 0.82rem;
            border: 1px solid #D6E7EB;
            border-radius: 13px;
            background: #FFFFFF;
            box-shadow: 0 6px 18px rgba(7,63,76,0.045);
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
        }}

        .executive-kpi-note {{
            color: {MUTED};
            font-size: 0.57rem;
            line-height: 1.3;
        }}

        /* ==================================================
           KPI TILES
           ================================================== */

        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.55rem;
        }}

        .kpi-card {{
            min-width: 0;
            padding: 0.72rem;
            border-radius: 11px;
            border: 1px solid {BORDER};
            background: #FFFFFF;
            box-shadow: 0 5px 16px rgba(7,63,76,0.045);
        }}

        .dark-section .kpi-card {{
            border-color: rgba(255,255,255,0.08);
        }}

        .kpi-label {{
            color: #198C9B;
            font-size: 0.62rem;
            font-weight: 800;
            line-height: 1.2;
            letter-spacing: 0.09em;
            text-transform: uppercase;
        }}

        .kpi-value {{
            color: {TEXT};
            font-size: 1.15rem;
            line-height: 1.05;
            font-weight: 800;
            letter-spacing: -0.025em;
            margin: 0.28rem 0 0.20rem;
        }}

        .kpi-description {{
            color: {MUTED};
            font-size: 0.58rem;
            line-height: 1.32;
        }}

        /* ==================================================
           ABC / PARETO
           ================================================== */

        .abc-summary {{
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.42rem;
            margin-top: 0.35rem;
        }}

        .abc-item {{
            padding: 0.55rem;
            border-radius: 9px;
            background: rgba(255,255,255,0.055);
            border: 1px solid rgba(255,255,255,0.075);
        }}

        .abc-item-label {{
            color: rgba(255,255,255,0.58);
            font-size: 0.54rem;
            font-weight: 800;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }}

        .abc-item-value {{
            color: #FFFFFF;
            font-size: 0.88rem;
            font-weight: 800;
            margin-top: 0.17rem;
        }}

        .abc-item-sub {{
            color: rgba(255,255,255,0.54);
            font-size: 0.62rem;
            margin-top: 0.08rem;
        }}

        .pareto-callout {{
            height: 100%;
            min-height: 160px;
            padding: 0.85rem;
            border-radius: 12px;
            border: 1px solid rgba(58,204,214,0.20);
            background: rgba(255,255,255,0.055);
        }}

        .pareto-callout-icon {{
            width: 32px;
            height: 32px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 0.55rem;
            border-radius: 10px;
            background: #11A8B7;
            color: #FFFFFF;
            font-size: 0.85rem;
        }}

        .pareto-callout-label {{
            color: #3BD0D8;
            font-size: 0.62rem;
            font-weight: 800;
            letter-spacing: 0.12em;
            text-transform: uppercase;
        }}

        .pareto-callout-title {{
            color: #FFFFFF;
            font-size: 0.86rem;
            line-height: 1.28;
            font-weight: 800;
            margin-top: 0.28rem;
        }}

        .pareto-callout-text {{
            color: rgba(255,255,255,0.64);
            font-size: 0.62rem;
            line-height: 1.45;
            margin-top: 0.38rem;
        }}

        /* ==================================================
           EMPTY STATE
           ================================================== */

        .empty-state {{
            padding: 2.5rem 1.5rem;
            margin-top: 0.8rem;
            border: 1px solid {BORDER};
            border-radius: 18px;
            background: #FFFFFF;
            text-align: center;
            box-shadow: {SHADOW};
        }}

        .empty-title {{
            color: {TEXT};
            font-size: 1.35rem;
            font-weight: 800;
        }}

        .empty-description {{
            color: {MUTED};
            font-size: 0.82rem;
            margin-top: 0.3rem;
        }}

        /* ==================================================
           RESPONSIVE
           ================================================== */

        @media (max-width: 900px) {{
            .profile-grid {{
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }}

            .profile-metric:nth-child(4n) {{
                border-right: 1px solid {BORDER};
            }}

            .profile-metric:nth-child(2n) {{
                border-right: none;
            }}

            .kpi-grid {{
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }}

            .executive-kpi-grid {{
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }}
        }}

        @media (max-width: 650px) {{
            [data-testid="stMainBlockContainer"] {{
                padding-left: 0.65rem;
                padding-right: 0.65rem;
            }}

            .customer-hero {{
                min-height: 150px;
                padding: 1.4rem 1.2rem;
            }}

            .customer-hero-title {{
                font-size: 1.75rem;
            }}

            .customer-hero-description {{
                font-size: 0.74rem;
            }}

            .customer-floating-home {{
                left: 12px;
                bottom: 14px;
                min-height: 44px;
                padding-right: 13px;
            }}

            .section-title {{
                font-size: 1rem;
            }}

            .account-row {{
                grid-template-columns: 1fr;
                gap: 0.18rem;
                padding: 0.55rem 0.65rem;
            }}

            .account-row.header {{
                display: none;
            }}

            .account-value,
            .account-contribution {{
                justify-content: flex-start;
                text-align: left;
                padding-left: 1.85rem;
            }}

            .account-percentage {{
                text-align: left;
            }}

            .profile-grid {{
                grid-template-columns: 1fr;
            }}

            .profile-metric,
            .profile-metric:nth-child(2n),
            .profile-metric:nth-child(4n) {{
                border-right: none;
                border-bottom: 1px solid {BORDER};
            }}

            .profile-metric:last-child {{
                border-bottom: none;
            }}

            .kpi-grid {{
                grid-template-columns: 1fr;
            }}

            .executive-kpi-grid {{
                grid-template-columns: 1fr;
            }}

            .abc-summary {{
                grid-template-columns: 1fr;
            }}
        }}

        </style>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# GENERIC SECTION HEADER
# ============================================================


def render_section_heading(
    eyebrow: str,
    title: str,
    description: str,
    icon: str,
    dark: bool = False,
) -> None:
    """Render a section header inside an already-open section card."""

    section_class = " dark-section" if dark else ""

    html = (
        f'<div class="section-heading{section_class}">'
        f'<div class="section-icon">{escape(icon)}</div>'
        '<div class="section-copy">'
        f'<div class="section-eyebrow">{escape(eyebrow)}</div>'
        f'<div class="section-title">{escape(title)}</div>'
        f'<div class="section-description">{escape(description)}</div>'
        '</div>'
        '</div>'
    )

    st.markdown(html, unsafe_allow_html=True)


# ============================================================
# HERO
# ============================================================


def render_page_header(
    latest_date: pd.Timestamp | None,
) -> None:
    """Render the compact Customer Intelligence hero."""

    date_text = (
        latest_date.strftime("%d %b %Y")
        if latest_date is not None
        else "No sales date available"
    )

    html = (
        '<section class="customer-hero">'

        '<div class="hero-ring" '
        'style="width:330px;height:330px;right:-100px;bottom:-205px;"></div>'

        '<div class="hero-ring" '
        'style="width:460px;height:460px;right:-165px;bottom:-285px;opacity:.62;"></div>'

        '<div class="hero-ring" '
        'style="width:190px;height:190px;right:80px;top:-110px;opacity:.50;"></div>'

        '<div class="hero-person">'
        '<div class="head one"></div>'
        '<div class="head two"></div>'
        '<div class="head three"></div>'
        '<div class="body"></div>'
        '<div class="body small"></div>'
        '<div class="body small right"></div>'
        '</div>'

        '<div class="customer-hero-content">'
        '<div class="customer-hero-eyebrow">'
        'Customer Intelligence'
        '</div>'
        '<div class="customer-hero-title">'
        'Know your customers.<br>'
        'Grow the right relationships.'
        '</div>'
        '<div class="customer-hero-description">'
        'Understand customer value, loyalty, activity and '
        'revenue contribution from a single intelligence layer.'
        '</div>'
        '</div>'

        '<div class="customer-hero-asof">'
        'Data as of:'
        f'<strong>{escape(date_text)}</strong>'
        '</div>'

        '</section>'
    )

    st.markdown(html, unsafe_allow_html=True)


# ============================================================
# EXECUTIVE KPIS
# ============================================================


def render_executive_kpis(
    engine: CustomerEngine,
) -> None:
    """Render the compact executive customer summary."""

    summary = engine.customer_summary()

    if summary.empty:
        return

    revenue_column = _find_column(
        summary,
        ("Revenue", "revenue", "Total Revenue", "total_revenue"),
    )
    orders_column = _find_column(
        summary,
        ("Orders", "orders", "Total Orders", "total_orders"),
    )

    customer_count = len(summary)
    total_revenue = float(
        _numeric_series(summary, revenue_column).sum()
    )
    total_orders = float(
        _numeric_series(summary, orders_column).sum()
    )

    average_order_value = (
        total_revenue / total_orders
        if total_orders > 0
        else 0.0
    )

    retention = 0.0
    if orders_column is not None and customer_count > 0:
        orders = _numeric_series(summary, orders_column)
        retention = float((orders > 1).sum()) / customer_count * 100.0

    metrics = [
        (
            "CUSTOMERS",
            format_number(float(customer_count)),
            "Total customer relationships",
        ),
        (
            "REVENUE",
            format_currency(total_revenue),
            "Total recorded customer revenue",
        ),
        (
            "AVG ORDER",
            format_currency(average_order_value),
            "Revenue divided by total orders",
        ),
        (
            "RETENTION",
            f"{retention:.1f}%",
            "Customers with more than one order",
        ),
    ]

    cards_html = ""

    for label, value, note in metrics:
        cards_html += (
            '<div class="executive-kpi">'
            f'<div class="executive-kpi-label">{escape(label)}</div>'
            f'<div class="executive-kpi-value">{escape(value)}</div>'
            f'<div class="executive-kpi-note">{escape(note)}</div>'
            '</div>'
        )

    html = (
        '<section class="executive-summary">'
        '<div class="executive-kicker">Customers</div>'
        '<div class="executive-title">Executive KPIs</div>'
        '<div class="executive-description">'
        'A quick view of customer scale, revenue, order value and retention.'
        '</div>'
        f'<div class="executive-kpi-grid">{cards_html}</div>'
        '</section>'
    )

    st.markdown(html, unsafe_allow_html=True)


# ============================================================
# PROFILE
# ============================================================


def _profile_metric(
    label: str,
    value: str,
) -> str:
    """Build a profile metric cell."""

    return (
        '<div class="profile-metric">'
        f'<div class="metric-label">{escape(label)}</div>'
        f'<div class="metric-value">{escape(value)}</div>'
        '</div>'
    )


def render_customer_lookup(
    engine: CustomerEngine,
) -> None:
    """Render customer selector and detailed customer profile."""

    summary = engine.customer_summary()

    if summary.empty:
        st.info("No customer data is available.")
        return

    customer_column = _find_column(
        summary,
        (
            "customer",
            "Customer",
            "customer_name",
            "Customer Name",
        ),
    )

    if customer_column is None:
        st.info("No customer field is available.")
        return

    customer_values = (
        summary[customer_column]
        .dropna()
        .astype(str)
        .str.strip()
    )

    customer_list = sorted(
        {
            value
            for value in customer_values.tolist()
            if value
        }
    )

    if not customer_list:
        st.info("No customers are available.")
        return

    selected_customer = st.selectbox(
        "Select a customer",
        customer_list,
        index=0,
        key="customer_dashboard_selector",
    )

    selected_rows = summary.loc[
        summary[customer_column].astype(str).eq(selected_customer)
    ]

    if selected_rows.empty:
        st.info("Customer profile is not available.")
        return

    selected_row = selected_rows.iloc[0]

    revenue_column = _find_column(
        summary,
        ("Revenue", "revenue", "Total Revenue", "total_revenue"),
    )
    quantity_column = _find_column(
        summary,
        ("Quantity", "quantity", "Total Quantity", "total_quantity"),
    )
    orders_column = _find_column(
        summary,
        ("Orders", "orders", "Total Orders", "total_orders"),
    )

    revenue = (
        _safe_float(selected_row[revenue_column])
        if revenue_column is not None
        else 0.0
    )
    quantity = (
        _safe_float(selected_row[quantity_column])
        if quantity_column is not None
        else 0.0
    )
    orders = (
        _safe_float(selected_row[orders_column])
        if orders_column is not None
        else 0.0
    )

    average_order_value = (
        revenue / orders
        if orders > 0
        else 0.0
    )

    total_revenue = float(
        _numeric_series(summary, revenue_column).sum()
    )

    contribution = (
        revenue / total_revenue * 100.0
        if total_revenue > 0
        else 0.0
    )

    ordered_revenue = (
        _numeric_series(summary, revenue_column)
        .sort_values(ascending=False, kind="stable")
    )

    position = 0

    if not selected_rows.empty:
        selected_index = selected_rows.index[0]
        positions = ordered_revenue.index.tolist()

        if selected_index in positions:
            position = positions.index(selected_index)

    cumulative = ordered_revenue.cumsum()

    selected_cumulative = (
        _safe_float(cumulative.iloc[position] / total_revenue * 100.0)
        if total_revenue > 0 and not cumulative.empty
        else 100.0
    )

    if selected_cumulative <= 80.0:
        abc_category = "A"
    elif selected_cumulative <= 95.0:
        abc_category = "B"
    else:
        abc_category = "C"

    status = "Active" if orders > 0 else "Dormant"

    # Use the engine's detailed lookup when available, so the profile
    # can surface its own lifecycle/ABC calculation without changing
    # the dashboard if that method is unavailable.
    try:
        detail_method = getattr(engine, "customer_details", None)

        if callable(detail_method):
            detail = detail_method(selected_customer)

            if isinstance(detail, dict):
                abc_category = _safe_text(
                    detail.get("ABC Category", abc_category),
                    abc_category,
                )
                status = _safe_text(
                    detail.get("Status", status),
                    status,
                )
                contribution = _safe_float(
                    detail.get(
                        "Contribution Percentage",
                        contribution,
                    ),
                    contribution,
                )
    except (
        AttributeError,
        KeyError,
        TypeError,
        ValueError,
    ):
        pass

    profile_html = (
        '<div class="profile-card">'

        '<div class="profile-watermark">'
        '<div class="wave one"></div>'
        '<div class="wave two"></div>'
        '</div>'

        '<div class="profile-header">'
        '<div class="profile-icon">⌂</div>'
        '<div>'
        '<div class="profile-label">Customer Profile</div>'
        '<div class="profile-name">'
        f'{escape(selected_customer)}'
        '<span class="status-pill">'
        f'{escape(status)}'
        '</span>'
        '</div>'
        '</div>'
        '</div>'

        '<div class="profile-grid">'

        + _profile_metric("Revenue", format_currency(revenue))
        + _profile_metric("Quantity", format_number(quantity))
        + _profile_metric("Orders", format_number(orders))
        + _profile_metric(
            "Average Order Value",
            format_currency(average_order_value),
        )
        + _profile_metric("ABC Category", abc_category)
        + _profile_metric(
            "Revenue Contribution",
            format_percentage(contribution),
        )
        + _profile_metric("Customer Status", status)

        + '</div>'
        '</div>'
    )

    st.markdown(profile_html, unsafe_allow_html=True)


# ============================================================
# KEY ACCOUNTS
# ============================================================


def render_customer_table(
    engine: CustomerEngine,
) -> None:
    """Render the ten highest-revenue customer relationships."""

    summary = engine.customer_summary()

    if summary.empty:
        st.info("No customer data is available.")
        return

    customer_column = _find_column(
        summary,
        (
            "customer",
            "Customer",
            "customer_name",
            "Customer Name",
        ),
    )
    revenue_column = _find_column(
        summary,
        ("Revenue", "revenue", "Total Revenue", "total_revenue"),
    )

    if customer_column is None or revenue_column is None:
        st.warning("Customer revenue data is not available.")
        return

    display_df = pd.DataFrame(
        {
            "Customer": (
                summary[customer_column]
                .fillna("Unknown Customer")
                .astype(str)
                .str.strip()
            ),
            "Revenue": _numeric_series(summary, revenue_column),
        }
    )

    total_revenue = float(display_df["Revenue"].sum())

    display_df["Contribution"] = (
        display_df["Revenue"] / total_revenue * 100.0
        if total_revenue > 0
        else 0.0
    )

    display_df = (
        display_df
        .sort_values("Revenue", ascending=False, kind="stable")
        .head(10)
        .reset_index(drop=True)
    )

    rows_html = ""

    for position in range(len(display_df)):
        rank = position + 1
        customer = _safe_text(
            display_df.iloc[position]["Customer"],
            "Unknown Customer",
        )
        revenue = _safe_float(display_df.iloc[position]["Revenue"])
        contribution = _safe_float(
            display_df.iloc[position]["Contribution"]
        )

        bar_width = min(
            max(contribution, 0.0),
            100.0,
        )

        rank_class = " top" if rank == 1 else ""

        rows_html += (
            '<div class="account-row">'
            '<div class="account-name">'
            f'<span class="account-rank{rank_class}">{rank}</span>'
            f'{escape(customer)}'
            '</div>'
            '<div class="account-value">'
            f'{escape(format_currency(revenue))}'
            '</div>'
            '<div class="account-contribution">'
            '<span class="account-percentage">'
            f'{contribution:.2f}%'
            '</span>'
            '<span class="account-bar-track">'
            f'<span class="account-bar" style="width:{bar_width:.2f}%;"></span>'
            '</span>'
            '</div>'
            '</div>'
        )

    top_10_contribution = _safe_float(
        display_df["Contribution"].sum()
    )

    table_html = (
        '<div class="account-table">'
        '<div class="account-row header">'
        '<div class="account-header">Customer</div>'
        '<div class="account-header" style="text-align:right;">Revenue</div>'
        '<div class="account-header" style="text-align:right;">Contribution</div>'
        '</div>'
        f'{rows_html}'
        '</div>'

        '<div class="insight-strip dark-insight">'
        '<div class="insight-icon">↗</div>'
        '<div>'
        '<div class="insight-label">Insight</div>'
        'Top 10 customers contribute '
        '<span class="insight-value">'
        f'{top_10_contribution:.2f}%'
        '</span>'
        ' of total revenue, indicating the level of customer revenue concentration.'
        '</div>'
        '</div>'
    )

    st.markdown(table_html, unsafe_allow_html=True)


# ============================================================
# CUSTOMER VALUE
# ============================================================


def _prepare_customer_chart_data(
    summary: pd.DataFrame,
    customer_column: str,
    value_column: str,
    limit: int = 10,
) -> pd.DataFrame:
    """Prepare ranked customer chart data."""

    result = pd.DataFrame(
        {
            "Customer": (
                summary[customer_column]
                .fillna("Unknown Customer")
                .astype(str)
                .str.strip()
            ),
            "Value": _numeric_series(summary, value_column),
        }
    )

    return (
        result
        .sort_values("Value", ascending=False, kind="stable")
        .head(limit)
        .reset_index(drop=True)
    )


def _base_chart_layout(
    height: int,
) -> dict[str, Any]:
    """Return a compact AQVASTAR Plotly layout."""

    return {
        "height": height,
        "margin": {
            "l": 4,
            "r": 12,
            "t": 8,
            "b": 28,
        },
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {
            "family": "Arial, sans-serif",
            "size": 9,
            "color": TEXT,
        },
        "showlegend": False,
    }


def render_top_customer_charts(
    engine: CustomerEngine,
) -> None:
    """Render revenue and quantity customer rankings."""

    summary = engine.customer_summary()

    if summary.empty:
        return

    customer_column = _find_column(
        summary,
        (
            "customer",
            "Customer",
            "customer_name",
            "Customer Name",
        ),
    )
    revenue_column = _find_column(
        summary,
        ("Revenue", "revenue", "Total Revenue", "total_revenue"),
    )
    quantity_column = _find_column(
        summary,
        ("Quantity", "quantity", "Total Quantity", "total_quantity"),
    )

    if customer_column is None:
        st.info("Customer data is not available.")
        return

    left, right = st.columns(2, gap="medium")

    with left:
        revenue_df = (
            _prepare_customer_chart_data(
                summary,
                customer_column,
                revenue_column,
            )
            if revenue_column is not None
            else pd.DataFrame()
        )

        if revenue_df.empty:
            st.info("Revenue data is not available.")
        else:
            figure = go.Figure(
                go.Bar(
                    x=revenue_df["Value"].tolist(),
                    y=revenue_df["Customer"].tolist(),
                    orientation="h",
                    marker_color=DEEP_2,
                    text=[
                        format_currency(float(value))
                        for value in revenue_df["Value"].tolist()
                    ],
                    textposition="outside",
                    hovertemplate=(
                        "<b>%{y}</b><br>"
                        "Revenue: ₹%{x:,.0f}"
                        "<extra></extra>"
                    ),
                )
            )

            layout = _base_chart_layout(300)
            layout.update(
                {
                    "margin": {
                        "l": 5,
                        "r": 68,
                        "t": 8,
                        "b": 25,
                    },
                }
            )
            figure.update_layout(**layout)

            figure.update_xaxes(
                tickprefix="₹",
                tickformat="~s",
                showgrid=True,
                gridcolor="#E6EFF1",
                zeroline=False,
                tickfont={"size": 8, "color": MUTED},
            )

            figure.update_yaxes(
                showgrid=False,
                autorange="reversed",
                tickfont={"size": 8, "color": TEXT},
                automargin=True,
            )

            st.markdown(
                '<div class="chart-card">'
                '<div class="chart-title">Top Customers by Revenue</div>'
                '<div class="chart-description">'
                'Highest-value customer relationships by revenue.'
                '</div>'
                '</div>'
                '<div class="chart-plot-gap"></div>',
                unsafe_allow_html=True,
            )

            st.plotly_chart(
                figure,
                use_container_width=True,
                config={"displayModeBar": False},
            )

            top_customer = _safe_text(
                revenue_df.iloc[0]["Customer"],
                "Top customer",
            )

            st.markdown(
                '<div class="chart-insight">'
                '<strong>Insight:</strong> '
                f'{escape(top_customer)} '
                'is currently the highest-value customer by recorded revenue.'
                '</div>',
                unsafe_allow_html=True,
            )

    with right:
        quantity_df = (
            _prepare_customer_chart_data(
                summary,
                customer_column,
                quantity_column,
            )
            if quantity_column is not None
            else pd.DataFrame()
        )

        if quantity_df.empty:
            st.info("Quantity data is not available.")
        else:
            figure = go.Figure(
                go.Bar(
                    x=quantity_df["Value"].tolist(),
                    y=quantity_df["Customer"].tolist(),
                    orientation="h",
                    marker_color="#15A5B5",
                    text=[
                        format_number(float(value))
                        for value in quantity_df["Value"].tolist()
                    ],
                    textposition="outside",
                    hovertemplate=(
                        "<b>%{y}</b><br>"
                        "Quantity: %{x:,.1f}"
                        "<extra></extra>"
                    ),
                )
            )

            layout = _base_chart_layout(300)
            layout.update(
                {
                    "margin": {
                        "l": 5,
                        "r": 58,
                        "t": 8,
                        "b": 25,
                    },
                }
            )
            figure.update_layout(**layout)

            figure.update_xaxes(
                tickformat="~s",
                showgrid=True,
                gridcolor="#E6EFF1",
                zeroline=False,
                tickfont={"size": 8, "color": MUTED},
            )

            figure.update_yaxes(
                showgrid=False,
                autorange="reversed",
                tickfont={"size": 8, "color": TEXT},
                automargin=True,
            )

            st.markdown(
                '<div class="chart-card">'
                '<div class="chart-title">Top Customers by Quantity</div>'
                '<div class="chart-description">'
                'Customers generating the highest sales volume.'
                '</div>'
                '</div>'
                '<div class="chart-plot-gap"></div>',
                unsafe_allow_html=True,
            )

            st.plotly_chart(
                figure,
                use_container_width=True,
                config={"displayModeBar": False},
            )

            st.markdown(
                '<div class="chart-insight">'
                '<strong>Insight:</strong> '
                'High sales volume is distributed across the broader customer base.'
                '</div>',
                unsafe_allow_html=True,
            )


# ============================================================
# CUSTOMER ACTIVITY
# ============================================================


def render_activity_section(
    engine: CustomerEngine,
) -> None:
    """Render lifecycle and acquisition analytics."""

    summary = engine.customer_summary()

    if summary.empty:
        return

    # Prefer the actual CustomerEngine activity methods.
    active_df = _call_dataframe_method(
        engine,
        "active_customers",
        90,
    )
    dormant_df = _call_dataframe_method(
        engine,
        "dormant_customers",
        90,
    )
    new_df = _call_dataframe_method(
        engine,
        "new_customers",
        30,
    )

    active_count = len(active_df)
    dormant_count = len(dormant_df)
    new_count = len(new_df)

    if active_df.empty and dormant_df.empty:
        orders_column = _find_column(
            summary,
            ("Orders", "orders", "Total Orders", "total_orders"),
        )

        if orders_column is not None:
            orders = _numeric_series(summary, orders_column)
            active_count = int((orders > 0).sum())
            dormant_count = int((orders == 0).sum())

    customer_count = len(summary)

    if new_df.empty:
        new_count = 0

    # At-risk is intentionally conservative. If the engine exposes
    # a dedicated method later, this block can use it without changing
    # the dashboard layout.
    at_risk_count = 0

    metrics = [
        (
            "ACTIVE CUSTOMERS",
            format_number(float(active_count)),
            (
                f"({active_count / customer_count * 100.0:.1f}%)"
                if customer_count > 0
                else "N/A"
            ),
        ),
        (
            "DORMANT CUSTOMERS",
            format_number(float(dormant_count)),
            (
                f"({dormant_count / customer_count * 100.0:.1f}%)"
                if customer_count > 0
                else "N/A"
            ),
        ),
        (
            "NEW CUSTOMERS",
            format_number(float(new_count)),
            (
                f"({new_count / customer_count * 100.0:.1f}%)"
                if customer_count > 0
                else "N/A"
            ),
        ),
        (
            "AT RISK CUSTOMERS",
            format_number(float(at_risk_count)),
            "No dedicated risk model exposed by engine",
        ),
    ]

    cards_html = ""

    for label, value, description in metrics:
        cards_html += (
            '<div class="kpi-card">'
            f'<div class="kpi-label">{escape(label)}</div>'
            f'<div class="kpi-value">{escape(value)}</div>'
            f'<div class="kpi-description">{escape(description)}</div>'
            '</div>'
        )

    st.markdown(
        f'<div class="kpi-grid">{cards_html}</div>',
        unsafe_allow_html=True,
    )

    lifecycle_values = [
        active_count,
        dormant_count,
        new_count,
    ]

    lifecycle_labels = [
        "Active",
        "Dormant",
        "New · 30d",
    ]

    lifecycle_figure = go.Figure(
        go.Bar(
            x=lifecycle_labels,
            y=lifecycle_values,
            marker_color=[
                DEEP_2,
                "#8FCFD5",
                "#16A7B7",
            ],
            text=[str(value) for value in lifecycle_values],
            textposition="outside",
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Customers: %{y}"
                "<extra></extra>"
            ),
        )
    )

    lifecycle_layout = _base_chart_layout(285)
    lifecycle_layout["margin"] = {
        "l": 42,
        "r": 14,
        "t": 30,
        "b": 46,
    }
    lifecycle_figure.update_layout(**lifecycle_layout)

    lifecycle_figure.update_yaxes(
        showgrid=True,
        gridcolor="#E8F0F2",
        zeroline=False,
        tickfont={"size": 8, "color": MUTED},
    )

    lifecycle_figure.update_xaxes(
        showgrid=False,
        tickfont={"size": 8, "color": TEXT},
    )

    monthly_df = _call_dataframe_method(
        engine,
        "monthly_customer_growth",
    )

    month_column = _find_column(
        monthly_df,
        ("Month", "month", "Date", "date"),
    )
    new_customer_column = _find_column(
        monthly_df,
        (
            "New Customers",
            "New_Customers",
            "new_customers",
            "Customers",
            "customers",
        ),
    )

    monthly_figure = go.Figure()

    if (
        not monthly_df.empty
        and month_column is not None
        and new_customer_column is not None
    ):
        plot_df = monthly_df.copy()
        plot_df["_value"] = _numeric_series(
            plot_df,
            new_customer_column,
        )

        plot_df = plot_df.tail(16)

        x_values = [
            _safe_text(value)
            for value in plot_df[month_column].tolist()
        ]
        y_values = plot_df["_value"].tolist()

        monthly_figure.add_scatter(
            x=x_values,
            y=y_values,
            mode="lines+markers+text",
            text=[format_number(float(value)) for value in y_values],
            textposition="top center",
            line={"color": "#15A5B5", "width": 2},
            marker={
                "color": "#15A5B5",
                "size": 5,
            },
            hovertemplate=(
                "<b>%{x}</b><br>"
                "New customers: %{y}"
                "<extra></extra>"
            ),
        )
    else:
        monthly_figure.add_annotation(
            text="Monthly acquisition data is not available.",
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            showarrow=False,
            font={"size": 10, "color": MUTED},
        )

    monthly_layout = _base_chart_layout(285)
    monthly_layout["margin"] = {
        "l": 42,
        "r": 18,
        "t": 30,
        "b": 58,
    }
    monthly_figure.update_layout(**monthly_layout)

    monthly_figure.update_yaxes(
        showgrid=True,
        gridcolor="#E8F0F2",
        zeroline=False,
        tickfont={"size": 8, "color": MUTED},
    )

    monthly_figure.update_xaxes(
        showgrid=False,
        tickfont={"size": 7, "color": MUTED},
        tickangle=-35,
    )

    left, right = st.columns(2, gap="medium")

    with left:
        st.markdown(
            '<div class="activity-chart-heading">'
            '<div class="chart-title">Customer Lifecycle</div>'
            '<div class="chart-description">'
            'Active, dormant and newly acquired customers.'
            '</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        st.plotly_chart(
            lifecycle_figure,
            use_container_width=True,
            config={"displayModeBar": False},
        )

    with right:
        st.markdown(
            '<div class="activity-chart-heading">'
            '<div class="chart-title">Monthly Customer Acquisition</div>'
            '<div class="chart-description">'
            'New customer acquisition by month.'
            '</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        st.plotly_chart(
            monthly_figure,
            use_container_width=True,
            config={"displayModeBar": False},
        )

    st.markdown(
        '<div class="insight-strip" style="margin-top:1.35rem;">'
        '<div class="insight-icon">↗</div>'
        '<div>'
        '<div class="insight-label">Insight</div>'
        'Focus on re-engaging dormant customers and monitoring acquisition '
        'trends to identify additional revenue opportunities.'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )


# ============================================================
# CUSTOMER LOYALTY
# ============================================================


def render_loyalty_section(
    engine: CustomerEngine,
) -> None:
    """Render customer loyalty metrics."""

    summary = engine.customer_summary()

    if summary.empty:
        return

    orders_column = _find_column(
        summary,
        ("Orders", "orders", "Total Orders", "total_orders"),
    )
    revenue_column = _find_column(
        summary,
        ("Revenue", "revenue", "Total Revenue", "total_revenue"),
    )

    if orders_column is None:
        st.info("Loyalty metrics are not available.")
        return

    orders = _numeric_series(summary, orders_column)
    customer_count = len(summary)

    repeat_count = int((orders > 1).sum())

    repeat_rate = (
        repeat_count / customer_count * 100.0
        if customer_count > 0
        else 0.0
    )

    total_revenue = (
        float(_numeric_series(summary, revenue_column).sum())
        if revenue_column is not None
        else 0.0
    )

    repeat_revenue = (
        float(
            _numeric_series(summary, revenue_column)[orders > 1].sum()
        )
        if revenue_column is not None
        else 0.0
    )

    repeat_revenue_rate = (
        repeat_revenue / total_revenue * 100.0
        if total_revenue > 0
        else 0.0
    )

    frequency_df = _call_dataframe_method(
        engine,
        "purchase_frequency",
    )

    frequency_column = _find_column(
        frequency_df,
        (
            "Purchase_Frequency_Days",
            "purchase_frequency_days",
            "Average_Days_Between_Orders",
            "average_days_between_orders",
        ),
    )

    average_days = 0.0

    if frequency_column is not None:
        frequency_values = pd.to_numeric(
            frequency_df[frequency_column],
            errors="coerce",
        ).dropna()

        frequency_values = frequency_values[
            frequency_values > 0
        ]

        if not frequency_values.empty:
            average_days = float(frequency_values.mean())

    orders_per_customer = (
        float(orders.sum()) / customer_count
        if customer_count > 0
        else 0.0
    )

    # A transparent 0-100 loyalty index built only from the
    # two directly measured engagement ratios.
    loyalty_score = min(
        100.0,
        (repeat_rate * 0.55) + (repeat_revenue_rate * 0.45),
    )

    metrics = [
        (
            "REPEAT CUSTOMERS",
            f"{repeat_rate:.1f}%",
            "Customers with more than one order",
        ),
        (
            "REPEAT REVENUE",
            f"{repeat_revenue_rate:.1f}%",
            "Revenue generated by repeat customers",
        ),
        (
            "AVERAGE DAYS BETWEEN ORDERS",
            f"{average_days:.1f}" if average_days > 0 else "N/A",
            "Average time between consecutive orders",
        ),
        (
            "LOYALTY SCORE",
            f"{loyalty_score:.0f} / 100",
            "Composite of repeat rate and repeat revenue",
        ),
    ]

    cards_html = ""

    for label, value, description in metrics:
        cards_html += (
            '<div class="kpi-card">'
            f'<div class="kpi-label">{escape(label)}</div>'
            f'<div class="kpi-value">{escape(value)}</div>'
            f'<div class="kpi-description">{escape(description)}</div>'
            '</div>'
        )

    st.markdown(
        f'<div class="kpi-grid">{cards_html}</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="insight-strip dark-insight">'
        '<div class="insight-icon">♡</div>'
        '<div>'
        '<div class="insight-label">Insight</div>'
        'Strong repeat purchasing indicates healthier customer engagement '
        'and creates a larger base for retention and reactivation programs.'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )


# ============================================================
# REVENUE CONTRIBUTION
# ============================================================


def render_contribution_section(
    engine: CustomerEngine,
) -> None:
    """Render ABC customer classification and Pareto revenue analysis."""

    summary = engine.customer_summary()

    if summary.empty:
        return

    revenue_column = _find_column(
        summary,
        ("Revenue", "revenue", "Total Revenue", "total_revenue"),
    )

    if revenue_column is None:
        st.info("Revenue contribution data is not available.")
        return

    revenue = _numeric_series(
        summary,
        revenue_column,
    )

    positive_revenue = (
        revenue[revenue > 0]
        .sort_values(ascending=False, kind="stable")
    )

    if positive_revenue.empty:
        st.info("No positive customer revenue is available.")
        return

    total_revenue = float(positive_revenue.sum())

    contribution = (
        positive_revenue / total_revenue * 100.0
    )

    cumulative = contribution.cumsum()

    abc_a = cumulative <= 80.0
    abc_b = (
        (cumulative > 80.0)
        & (cumulative <= 95.0)
    )
    abc_c = cumulative > 95.0

    class_masks = {
        "A": abc_a,
        "B": abc_b,
        "C": abc_c,
    }

    abc_values: list[float] = []
    abc_counts: list[int] = []
    abc_percentages: list[float] = []

    for label in ("A", "B", "C"):
        mask = class_masks[label]
        class_revenue = float(positive_revenue[mask].sum())
        class_count = int(mask.sum())

        abc_values.append(class_revenue)
        abc_counts.append(class_count)
        abc_percentages.append(
            class_revenue / total_revenue * 100.0
            if total_revenue > 0
            else 0.0
        )

    pareto_figure = go.Figure()

    rank_values = list(
        range(1, len(positive_revenue) + 1)
    )

    pareto_figure.add_bar(
        x=rank_values,
        y=positive_revenue.tolist(),
        name="Revenue",
        marker_color="#1599A8",
        opacity=0.78,
        hovertemplate=(
            "Customer rank: %{x}<br>"
            "Revenue: ₹%{y:,.0f}"
            "<extra></extra>"
        ),
    )

    pareto_figure.add_scatter(
        x=rank_values,
        y=cumulative.tolist(),
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
            "Customer rank: %{x}<br>"
            "Cumulative: %{y:.1f}%"
            "<extra></extra>"
        ),
    )

    pareto_figure.update_layout(
        height=300,
        margin={"l": 58, "r": 62, "t": 38, "b": 52},
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
                "text": "Customer Rank",
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

    abc_figure = go.Figure(
        go.Pie(
            labels=["A Customers", "B Customers", "C Customers"],
            values=abc_values,
            hole=0.66,
            textinfo="percent",
            textfont={
                "size": 10,
                "color": "#FFFFFF",
            },
            marker={
                "colors": [
                    "#0B7D8B",
                    "#17A8B6",
                    "#63CDD4",
                ],
                "line": {
                    "color": DEEP,
                    "width": 2,
                },
            },
            hovertemplate=(
                "<b>%{label}</b><br>"
                "Revenue: ₹%{value:,.0f}<br>"
                "Share: %{percent}"
                "<extra></extra>"
            ),
        )
    )

    abc_figure.update_layout(
        height=250,
        margin={"l": 8, "r": 8, "t": 12, "b": 8},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={
            "family": "Arial, sans-serif",
            "color": "#FFFFFF",
        },
        showlegend=False,
        annotations=[
            {
                "text": "ABC",
                "x": 0.5,
                "y": 0.5,
                "showarrow": False,
                "font": {
                    "size": 14,
                    "color": "#FFFFFF",
                    "family": "Arial, sans-serif",
                },
            }
        ],
    )

    abc_cards = ""

    class_names = {
        "A": "High Value",
        "B": "Medium Value",
        "C": "Low Value",
    }

    for position, label in enumerate(("A", "B", "C")):
        abc_cards += (
            '<div class="abc-item">'
            f'<div class="abc-item-label">'
            f'{label} Customers'
            '</div>'
            f'<div class="abc-item-value">'
            f'{abc_percentages[position]:.1f}% revenue'
            '</div>'
            f'<div class="abc-item-sub">'
            f'{abc_counts[position]:,} customers · '
            f'{class_names[label]}'
            '</div>'
            '</div>'
        )

    cutoff_positions = (
        cumulative.ge(80.0).to_numpy().nonzero()[0]
    )
    top_80_cutoff = (
        int(cutoff_positions[0])
        if cutoff_positions.size > 0
        else len(positive_revenue) - 1
    )
    pareto_customer_count = top_80_cutoff + 1

    pareto_customer_percentage = (
        pareto_customer_count
        / len(positive_revenue)
        * 100.0
        if len(positive_revenue) > 0
        else 0.0
    )

    left, right = st.columns(
        [1.05, 1.55],
        gap="medium",
    )

    with left:
        st.markdown(
            '<div class="chart-card">'
            '<div class="chart-title">ABC Analysis</div>'
            '<div class="chart-description">'
            'Customers by revenue contribution.'
            '</div>'
            '</div>'
            '<div class="chart-plot-gap"></div>',
            unsafe_allow_html=True,
        )

        st.plotly_chart(
            abc_figure,
            use_container_width=True,
            config={"displayModeBar": False},
        )

        st.markdown(
            f'<div class="abc-summary">{abc_cards}</div>',
            unsafe_allow_html=True,
        )

    with right:
        st.markdown(
            '<div class="chart-card">'
            '<div class="chart-title">Pareto Analysis</div>'
            '<div class="chart-description">'
            'Cumulative revenue contribution across customer rank.'
            '</div>'
            '</div>'
            '<div class="chart-plot-gap"></div>',
            unsafe_allow_html=True,
        )

        # Plotly is rendered on a dark section, so its text and grid
        # are deliberately light to preserve the reference visual.
        st.plotly_chart(
            pareto_figure,
            use_container_width=True,
            config={"displayModeBar": False},
        )

    st.markdown(
        '<div class="insight-strip dark-insight">'
        '<div class="insight-icon">★</div>'
        '<div>'
        '<div class="insight-label">Insight</div>'
        f'Approximately <span class="insight-value">'
        f'{pareto_customer_percentage:.1f}%'
        '</span> of customers account for the first 80% of revenue. '
        'Focus on key accounts while continuing to nurture the broader customer base.'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )


# ============================================================
# EMPTY STATE
# ============================================================


def render_empty_state() -> None:
    """Render an empty customer-data state."""

    st.markdown(
        '<div class="empty-state">'
        '<div class="section-eyebrow">Customer Intelligence</div>'
        '<div class="empty-title">No customer data available</div>'
        '<div class="empty-description">'
        'Upload valid sales data to populate customer intelligence.'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )


# ============================================================
# MAIN
# ============================================================


def main() -> None:
    """Render the AQVASTAR Customer Intelligence dashboard."""

    apply_theme("AQVASTAR | Customer Intelligence")
    inject_dashboard_css()

    render_brand()
    render_navigation("customers")

    st.markdown(
        '<a href="?page=home" '
        'target="_self" '
        'class="customer-floating-home" '
        'aria-label="Back to Home">'
        '<span class="customer-floating-home-icon">⌂</span>'
        '<span class="customer-floating-home-text">'
        'BACK TO HOME'
        '</span>'
        '</a>',
        unsafe_allow_html=True,
    )

    try:
        engine = CustomerEngine()
    except (
        KeyError,
        TypeError,
        ValueError,
    ) as exc:
        st.error(
            f"Customer engine could not be initialized: {exc}"
        )
        return

    try:
        summary = engine.customer_summary()
    except (
        KeyError,
        TypeError,
        ValueError,
    ) as exc:
        st.error(
            f"Customer engine could not load data: {exc}"
        )
        return

    latest_date = SalesQueries.get_latest_posting_date()

    render_page_header(latest_date)

    if summary.empty:
        render_empty_state()
        return

    # ========================================================
    # EXECUTIVE SUMMARY
    # ========================================================

    render_executive_kpis(engine)

    # ========================================================
    # KEY ACCOUNTS
    # ========================================================

    with st.container(key="key_accounts_section"):
        render_section_heading(
            "Key Accounts",
            "Highest-value customer relationships",
            "The customers currently contributing the most revenue.",
            "♛",
            dark=True,
        )
        render_customer_table(engine)

    # ========================================================
    # CUSTOMER VALUE
    # ========================================================

    with st.container(key="customer_value_section"):
        render_section_heading(
            "Customer Value",
            "Who creates the most value?",
            "Identify the customers contributing the greatest revenue and volume.",
            "▥",
        )
        render_top_customer_charts(engine)

    # ========================================================
    # CUSTOMER LOOKUP
    # ========================================================

    with st.container(key="customer_lookup_section"):
        render_section_heading(
            "Customer Lookup",
            "Drill into an individual customer",
            "Select a customer to view their complete customer profile.",
            "⌕",
        )
        render_customer_lookup(engine)

    # ========================================================
    # CUSTOMER ACTIVITY
    # ========================================================

    with st.container(key="customer_activity_section"):
        render_section_heading(
            "Customer Activity",
            "Who is active, dormant or newly acquired?",
            "Monitor customer engagement and acquisition over time.",
            "▦",
        )
        render_activity_section(engine)

    # ========================================================
    # CUSTOMER LOYALTY
    # ========================================================

    with st.container(key="customer_loyalty_section"):
        render_section_heading(
            "Customer Loyalty",
            "How strong is customer engagement?",
            "Understand repeat purchasing and the time between customer orders.",
            "♡",
            dark=True,
        )
        render_loyalty_section(engine)

    # ========================================================
    # REVENUE CONTRIBUTION
    # ========================================================

    with st.container(key="revenue_contribution_section"):
        render_section_heading(
            "Revenue Contribution",
            "How concentrated is customer revenue?",
            "Use ABC and Pareto analysis to understand customer importance.",
            "◔",
            dark=True,
        )
        render_contribution_section(engine)


if __name__ == "__main__":
    main()
