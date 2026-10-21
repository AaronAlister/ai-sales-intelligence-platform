"""
AQVASTAR Sales Intelligence Platform.

Forecast Intelligence Dashboard.

Dashboard orchestration only. Forecasting business logic remains in
TimeSeriesEngine.
"""

from __future__ import annotations

from collections.abc import Callable
from html import escape

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from dashboards.components.navigation import render_brand, render_navigation
from dashboards.components.theme import AQUA, DEEP_OCEAN, OCEAN, apply_theme
from engines.forecast_engine import TimeSeriesEngine


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
GRID_LIGHT = "#DCEBED"


# ============================================================
# FORMATTERS
# ============================================================

def safe_float(value: object, default: float = 0.0) -> float:
    try:
        number = float(value)  # type: ignore[arg-type]
        return default if pd.isna(number) else number
    except (TypeError, ValueError):
        return default


def format_currency(value: float) -> str:
    value = safe_float(value)
    if abs(value) >= 1_000_000_000:
        return f"₹{value / 1_000_000_000:.2f}B"
    if abs(value) >= 1_000_000:
        return f"₹{value / 1_000_000:.2f}M"
    if abs(value) >= 1_000:
        return f"₹{value / 1_000:.1f}K"
    return f"₹{value:,.0f}"


def format_number(value: float) -> str:
    value = safe_float(value)
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    if abs(value) >= 1_000:
        return f"{value / 1_000:.1f}K"
    return f"{value:,.0f}"


def format_percentage(value: float) -> str:
    return f"{safe_float(value):.1f}%"


def method_label(method: str) -> str:
    labels = {
        "naive": "Naive",
        "moving_average": "Moving Average",
        "linear_trend": "Linear Trend",
    }
    return labels.get(method.strip().lower(), method.replace("_", " ").title())


# ============================================================
# CSS
# ============================================================

def inject_forecast_css() -> None:
    st.markdown(
        f"""
        <style>
        .stApp {{
            background:
                radial-gradient(
                    circle at 100% 0%,
                    rgba(22,174,192,0.045),
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

        .forecast-floating-home {{
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

        .forecast-floating-home:hover {{
            transform: translateY(-3px);
            border-color: {AQUA};
            box-shadow: 0 16px 36px rgba(4,62,76,0.22);
            color: #087C8A !important;
        }}

        .forecast-floating-home-icon {{
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

        .forecast-floating-home-text {{
            white-space: nowrap;
        }}

        .st-key-forecast_controls {{
            margin-top: 0.75rem;
            padding: 1.15rem 1.25rem 1.2rem;
            border: 1px solid #CFE3E7;
            border-radius: 18px;
            background: rgba(255,255,255,0.96);
            box-shadow: 0 7px 20px rgba(11,73,88,0.045);
        }}


        /* ==================================================
           FORECAST CONTROL SELECTS - AGGRESSIVE OVERRIDE
           ================================================== */

        /* Style the labels above the selectboxes */
        [data-testid="stWidgetLabel"] p {{
            color: #164B59 !important;
            font-weight: 700 !important;
            font-size: 0.82rem !important;
            letter-spacing: 0.02em !important;
        }}

        /* Force the background and border of the actual selectbox element */
        div[data-baseweb="select"] > div {{
            background-color: #E8F7F9 !important; /* Light Aqua */
            background-image: none !important;
            border: 1.5px solid #10AFC0 !important; /* Bright Teal */
            border-radius: 12px !important;
            min-height: 46px !important;
            box-shadow: 0 5px 14px rgba(8,124,138,0.08) !important;
        }}

        /* Force ALL text and icons inside the selectbox to be Deep Ocean */
        div[data-baseweb="select"] > div * {{
            color: #063D4A !important;
            -webkit-text-fill-color: #063D4A !important; /* Overrides Streamlit dark mode text */
            background-color: transparent !important; /* Prevents nested black boxes */
        }}

        /* Specifically target the dropdown arrow icon */
        div[data-baseweb="select"] svg {{
            fill: #087C8A !important;
            color: #087C8A !important;
        }}

        /* Hover state */
        div[data-baseweb="select"] > div:hover {{
            border-color: #087C8A !important;
            box-shadow: 0 6px 16px rgba(8,124,138,0.14) !important;
        }}

        /* Focus state */
        div[data-baseweb="select"] > div:focus-within,
        div[data-baseweb="select"] > div[aria-expanded="true"] {{
            border-color: #10AFC0 !important;
            box-shadow: 0 0 0 2px rgba(16,175,192,0.16) !important;
            outline: none !important;
        }}

        /* Dropdown menu popup (when clicked) */
        div[data-baseweb="popover"] div[data-baseweb="menu"] {{
            background-color: #FFFFFF !important;
            border: 1px solid #CFE3E7 !important;
            border-radius: 12px !important;
            box-shadow: 0 14px 32px rgba(4,62,76,0.18) !important;
        }}

        div[data-baseweb="popover"] div[data-baseweb="menu"] ul {{
            background-color: #FFFFFF !important;
        }}

        div[data-baseweb="popover"] div[data-baseweb="menu"] li {{
            background-color: #FFFFFF !important;
            color: #164B59 !important;
            font-weight: 600 !important;
        }}

        div[data-baseweb="popover"] div[data-baseweb="menu"] li:hover,
        div[data-baseweb="popover"] div[data-baseweb="menu"] li[aria-selected="true"] {{
            background-color: #E8F8FA !important;
            color: #087C8A !important;
        }}

        .st-key-forecast_run_button button {{
            min-height: 44px !important;
            padding: 0 22px !important;
            border: 0 !important;
            border-radius: 12px !important;
            background: linear-gradient(135deg, #0B5968, #10AFC0) !important;
            color: #FFFFFF !important;
            font-size: 0.76rem !important;
            font-weight: 800 !important;
            letter-spacing: 0.04em !important;
            box-shadow: 0 8px 20px rgba(8,124,138,0.20) !important;
        }}

        .st-key-forecast_run_button button:hover {{
            background: linear-gradient(135deg, #087C8A, #16AFC0) !important;
            transform: translateY(-1px);
        }}

        .forecast-ready {{
            min-height: 175px;
            margin: 1.1rem 0;
            display: flex;
            align-items: center;
            justify-content: center;
            border: 1px solid #CDEFF2;
            border-radius: 18px;
            background:
                radial-gradient(circle at 50% 35%, rgba(50,202,215,0.12), transparent 40%),
                linear-gradient(135deg, #F4FCFD, #FFFFFF);
            text-align: center;
        }}

        .forecast-ready-inner {{
            max-width: 620px;
        }}

        .forecast-ready-title {{
            color: #063B49;
            font-size: 1.15rem;
            font-weight: 850;
            letter-spacing: -0.02em;
        }}

        .forecast-ready-note {{
            margin-top: 0.35rem;
            color: #607782;
            font-size: 0.75rem;
        }}

        .forecast-calculating {{
            min-height: 175px;
            margin: 1.1rem 0;
            display: flex;
            align-items: center;
            justify-content: center;
            border: 1px solid #CDEFF2;
            border-radius: 18px;
            background:
                radial-gradient(
                    circle at 50% 35%,
                    rgba(50,202,215,0.16),
                    transparent 38%
                ),
                linear-gradient(135deg, #F4FCFD, #FFFFFF);
            box-shadow: 0 10px 28px rgba(11,73,88,0.06);
            text-align: center;
        }}

        .forecast-calculating-inner {{
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 10px;
        }}

        .forecast-calculating-spinner {{
            width: 34px;
            height: 34px;
            border: 3px solid #CDEFF2;
            border-top-color: {AQUA};
            border-radius: 50%;
            animation: forecast-spin 0.9s linear infinite;
        }}

        .forecast-calculating-title {{
            color: {TEXT};
            font-size: 1.08rem;
            font-weight: 850;
            letter-spacing: -0.015em;
        }}

        .forecast-calculating-note {{
            color: {MUTED};
            font-size: 0.70rem;
        }}

        @keyframes forecast-spin {{
            to {{ transform: rotate(360deg); }}
        }}

        .forecast-hero {{
            position: relative;
            overflow: hidden;
            min-height: 176px;
            padding: 2rem 2.25rem;
            margin: 0.35rem 0 1rem;
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

        .forecast-hero-content {{
            position: relative;
            z-index: 2;
            max-width: 900px;
        }}

        .forecast-hero-eyebrow {{
            color: #3BD0D8;
            font-size: 0.65rem;
            font-weight: 900;
            letter-spacing: 0.17em;
            text-transform: uppercase;
            margin-bottom: 0.62rem;
        }}

        .forecast-hero-title {{
            color: #FFFFFF;
            font-size: clamp(2rem, 3.6vw, 3.15rem);
            line-height: 0.98;
            font-weight: 900;
            letter-spacing: -0.045em;
        }}

        .forecast-hero-description {{
            max-width: 760px;
            margin-top: 0.78rem;
            color: rgba(255,255,255,0.76);
            font-size: 0.78rem;
            line-height: 1.55;
        }}

        .forecast-hero-asof {{
            position: absolute;
            top: 2rem;
            right: 2.25rem;
            z-index: 3;
            color: rgba(255,255,255,0.76);
            font-size: 0.65rem;
            font-weight: 600;
            text-align: right;
            line-height: 1.45;
        }}

        .forecast-hero-asof strong {{
            display: block;
            color: #FFFFFF;
            font-size: 0.75rem;
            font-weight: 800;
        }}

        .forecast-ring {{
            position: absolute;
            border: 1px solid rgba(255,255,255,0.12);
            border-radius: 50%;
            pointer-events: none;
        }}

        .forecast-section {{
            margin: 1.15rem 0 0.8rem;
        }}

        .forecast-kicker {{
            color: #11899A;
            font-size: 0.64rem;
            font-weight: 800;
            letter-spacing: 0.16em;
            text-transform: uppercase;
            margin-bottom: 0.18rem;
        }}

        .forecast-title {{
            color: {TEXT};
            font-size: 1.32rem;
            line-height: 1.15;
            font-weight: 800;
            letter-spacing: -0.025em;
            margin-bottom: 0.18rem;
        }}

        .forecast-description {{
            color: {MUTED};
            font-size: 0.74rem;
            line-height: 1.4;
            margin-bottom: 0.72rem;
        }}

        .forecast-kpi-grid {{
            display: grid;
            grid-template-columns: repeat(5, minmax(0, 1fr));
            gap: 12px;
        }}

        .forecast-kpi {{
            min-height: 102px;
            padding: 15px 16px;
            border: 1px solid {BORDER};
            border-radius: 15px;
            background: {WHITE};
            box-shadow: 0 7px 20px rgba(11,73,88,0.055);
        }}

        .forecast-kpi-label {{
            color: #198A9A;
            font-size: 0.59rem;
            font-weight: 900;
            letter-spacing: 0.12em;
            text-transform: uppercase;
        }}

        .forecast-kpi-value {{
            margin-top: 8px;
            color: {TEXT};
            font-size: 1.25rem;
            line-height: 1.05;
            font-weight: 850;
            letter-spacing: -0.025em;
        }}

        .forecast-kpi-note {{
            margin-top: 6px;
            color: {MUTED};
            font-size: 0.62rem;
            line-height: 1.3;
        }}

        .forecast-card {{
            border: 1px solid {BORDER};
            border-radius: 17px;
            background: {WHITE};
            padding: 17px 18px 12px;
            box-shadow: 0 7px 20px rgba(11,73,88,0.045);
        }}

        .forecast-table-wrap {{
            width: 100%;
            overflow-x: auto;
            margin-top: 0.15rem;
            border: 1px solid #D9E8EC;
            border-radius: 12px;
            background: #FFFFFF;
        }}

        .forecast-light-table {{
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            font-family: Inter, Arial, sans-serif;
            font-size: 0.78rem;
            color: #102631;
            background: #FFFFFF;
        }}

        .forecast-light-table thead th {{
            padding: 11px 14px;
            text-align: left;
            font-weight: 800;
            color: #164B59;
            background: #E8F7F9;
            border-bottom: 1px solid #CDEFF2;
            white-space: nowrap;
        }}

        .forecast-light-table tbody td {{
            padding: 11px 14px;
            color: #294650;
            background: #FFFFFF;
            border-bottom: 1px solid #E5EFF1;
            white-space: nowrap;
        }}

        .forecast-light-table tbody tr:last-child td {{
            border-bottom: 0;
        }}

        .forecast-light-table tbody tr:hover td {{
            background: #F4FBFC;
        }}

        .forecast-light-table th:not(:last-child),
        .forecast-light-table td:not(:last-child) {{
            border-right: 1px solid #EDF3F4;
        }}

        .forecast-card-title {{
            color: {TEXT};
            font-size: 0.92rem;
            font-weight: 800;
            margin-bottom: 0.18rem;
        }}

        .forecast-card-note {{
            color: {MUTED};
            font-size: 0.68rem;
            line-height: 1.4;
            margin-bottom: 0.5rem;
        }}

        .forecast-insight {{
            border-radius: 15px;
            padding: 16px 18px;
            background: linear-gradient(135deg, #E8F7F9, #F8FCFD);
            border: 1px solid #CDEFF2;
        }}

        .forecast-insight-label {{
            color: #11899A;
            font-size: 0.60rem;
            font-weight: 900;
            letter-spacing: 0.14em;
            text-transform: uppercase;
        }}

        .forecast-insight-title {{
            margin-top: 6px;
            color: {TEXT};
            font-size: 1rem;
            font-weight: 850;
        }}

        .forecast-insight-text {{
            margin-top: 5px;
            color: {MUTED};
            font-size: 0.69rem;
            line-height: 1.5;
        }}

        @media (max-width: 900px) {{
            .forecast-kpi-grid {{
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }}

            .forecast-hero-asof {{
                top: 20px;
                right: 20px;
            }}
        }}

        @media (max-width: 620px) {{
            .forecast-kpi-grid {{
                grid-template-columns: 1fr;
            }}

            .forecast-hero {{
                padding: 1.45rem;
            }}

            .forecast-hero-title {{
                font-size: 2rem;
            }}

            .forecast-hero-asof {{
                position: static;
                margin-top: 1.2rem;
                text-align: left;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# UI HELPERS
# ============================================================

def render_section(eyebrow: str, title: str, description: str) -> None:
    st.markdown(
        f"""
        <section class="forecast-section">
            <div class="forecast-kicker">{escape(eyebrow)}</div>
            <div class="forecast-title">{escape(title)}</div>
            <div class="forecast-description">{escape(description)}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def empty_figure(message: str, height: int = 360) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        showarrow=False,
        font={"size": 13, "color": MUTED},
    )
    fig.update_layout(
        height=height,
        paper_bgcolor=WHITE,
        plot_bgcolor=WHITE,
        margin={"l": 20, "r": 20, "t": 15, "b": 15},
    )
    return fig


def style_figure(fig: go.Figure, height: int = 390) -> go.Figure:
    fig.update_layout(
        height=height,
        paper_bgcolor=WHITE,
        plot_bgcolor=WHITE,
        font={"family": "Inter, Arial, sans-serif", "color": TEXT},
        margin={"l": 15, "r": 18, "t": 20, "b": 45},
        hovermode="x unified",
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.01,
            "xanchor": "left",
            "x": 0,
            "font": {"size": 10, "color": TEXT},
            "bgcolor": "rgba(255,255,255,0.92)",
            "bordercolor": BORDER,
            "borderwidth": 1,
        },
    )
    fig.update_xaxes(
        showgrid=False,
        showline=True,
        linecolor="#8AAAB2",
        linewidth=1.2,
        ticks="outside",
        tickcolor="#8AAAB2",
        ticklen=5,
        tickfont={"size": 10, "color": TEXT},
    )
    fig.update_yaxes(
        showgrid=True,
        showline=True,
        linecolor="#8AAAB2",
        linewidth=1.2,
        ticks="outside",
        tickcolor="#8AAAB2",
        ticklen=5,
        gridcolor=GRID_LIGHT,
        zeroline=False,
        tickfont={"size": 10, "color": TEXT},
    )
    return fig


# ============================================================
# HERO
# ============================================================

def render_header(latest_date: pd.Timestamp | None) -> None:
    date_text = (
        latest_date.strftime("%d %b %Y")
        if latest_date is not None
        else "No sales date available"
    )

    html = (
        '<section class="forecast-hero">'
        '<div class="forecast-ring" '
        'style="width:330px;height:330px;right:-100px;bottom:-205px;"></div>'
        '<div class="forecast-ring" '
        'style="width:460px;height:460px;right:-165px;bottom:-285px;opacity:.62;"></div>'
        '<div class="forecast-ring" '
        'style="width:190px;height:190px;right:80px;top:-110px;opacity:.50;"></div>'
        '<div class="forecast-hero-content">'
        '<div class="forecast-hero-eyebrow">Forecast Intelligence</div>'
        '<div class="forecast-hero-title">'
        'See what comes next.<br>'
        'Plan revenue with confidence.'
        '</div>'
        '<div class="forecast-hero-description">'
        'Project future monthly revenue, compare forecasting methods, '
        'measure historical accuracy and understand forecast uncertainty.'
        '</div>'
        '</div>'
        '<div class="forecast-hero-asof">'
        'Data as of:'
        f'<strong>{escape(date_text)}</strong>'
        '</div>'
        '</section>'
    )

    st.markdown(html, unsafe_allow_html=True)


# ============================================================
# CONTROLS
# ============================================================

def render_controls() -> tuple[int, str, str, int, float, bool]:
    with st.container(key="forecast_controls"):
        st.markdown(
            '<div class="forecast-card-title">Forecast Controls</div>'
            '<div class="forecast-card-note">'
            'Choose the planning horizon, forecasting method and confidence level.'
            '</div>',
            unsafe_allow_html=True,
        )

        # Equal column ratios [1, 1, 1, 1] for equal sizing
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

        with col1:
            periods = st.selectbox(
                "Forecast horizon",
                options=[3, 6, 12],
                index=0,
                format_func=lambda value: f"{value} months",
            )

        with col2:
            method_option = st.selectbox(
                "Forecast method",
                options=["Auto", "Moving Average", "Naive", "Linear Trend"],
                index=0,
            )

        with col3:
            window = st.selectbox(
                "Moving-average window",
                options=[3, 6, 12],
                index=0,
                format_func=lambda value: f"{value} months",
                disabled=method_option not in {"Auto", "Moving Average"},
            )

        with col4:
            confidence = st.selectbox(
                "Confidence",
                options=[0.90, 0.95, 0.99],
                index=1,
                format_func=lambda value: f"{int(value * 100)}%",
            )

        with st.container(key="forecast_run_button"):
            run_forecast = st.button(
                "RUN FORECAST  →",
                use_container_width=True,
            )

    method_map = {
        "Moving Average": "moving_average",
        "Naive": "naive",
        "Linear Trend": "linear_trend",
    }

    selected_method = method_map.get(
        method_option,
        "moving_average",
    )

    return periods, method_option, selected_method, window, confidence, run_forecast


def render_executive_kpis(
    forecast: pd.DataFrame,
    reliability: dict[str, object],
    method: str,
) -> None:
    forecast_values = (
        pd.to_numeric(forecast["Forecast"], errors="coerce")
        if not forecast.empty
        else pd.Series(dtype="float64")
    )

    first_month = safe_float(forecast_values.iloc[0]) if not forecast_values.empty else 0.0
    total_forecast = safe_float(forecast_values.sum()) if not forecast_values.empty else 0.0
    average_forecast = (
        safe_float(forecast_values.mean())
        if not forecast_values.empty
        else 0.0
    )

    mape = safe_float(reliability.get("mape"), 0.0)
    reliability_level = str(reliability.get("reliability_level", "N/A"))
    periods = int(safe_float(reliability.get("backtest_periods"), 0))

    metrics = [
        ("NEXT MONTH", format_currency(first_month), "Forecast revenue"),
        ("HORIZON TOTAL", format_currency(total_forecast), "Projected revenue"),
        ("MONTHLY AVERAGE", format_currency(average_forecast), "Average forecast"),
        ("FORECAST MAPE", format_percentage(mape), f"{periods} backtest periods"),
        ("RELIABILITY", reliability_level, method_label(method)),
    ]

    cards = "".join(
        (
            '<div class="forecast-kpi">'
            f'<div class="forecast-kpi-label">{escape(label)}</div>'
            f'<div class="forecast-kpi-value">{escape(value)}</div>'
            f'<div class="forecast-kpi-note">{escape(note)}</div>'
            "</div>"
        )
        for label, value, note in metrics
    )

    st.markdown(
        '<section class="forecast-section">'
        '<div class="forecast-kicker">Forecast</div>'
        '<div class="forecast-title">Executive KPIs</div>'
        '<div class="forecast-description">'
        'A compact view of expected revenue, forecast accuracy and model reliability.'
        '</div>'
        f'<div class="forecast-kpi-grid">{cards}</div>'
        '</section>',
        unsafe_allow_html=True,
    )


# ============================================================
# FORECAST CHART
# ============================================================

def render_forecast_chart(
    engine: TimeSeriesEngine,
    forecast: pd.DataFrame,
    periods: int,
    method: str,
    window: int,
    confidence: float,
) -> None:
    history = engine.monthly_sales().copy()

    if history.empty or forecast.empty:
        st.plotly_chart(
            empty_figure("Forecast data is not available."),
            use_container_width=True,
        )
        return

    history["Month"] = pd.to_datetime(history["Month"], errors="coerce")
    history["Revenue"] = pd.to_numeric(history["Revenue"], errors="coerce")
    history = history.dropna(subset=["Month", "Revenue"]).sort_values("Month")

    forecast = forecast.copy()
    forecast["Month"] = pd.to_datetime(forecast["Month"], errors="coerce")
    forecast["Forecast"] = pd.to_numeric(forecast["Forecast"], errors="coerce")
    forecast["Lower Bound"] = pd.to_numeric(
        forecast["Lower Bound"], errors="coerce"
    )
    forecast["Upper Bound"] = pd.to_numeric(
        forecast["Upper Bound"], errors="coerce"
    )
    forecast = forecast.dropna(subset=["Month", "Forecast"])

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=history["Month"],
            y=history["Revenue"],
            mode="lines",
            name="Actual Revenue",
            line={"color": DEEP, "width": 2.6},
        )
    )

    fig.add_trace(
        go.Scatter(
            x=forecast["Month"],
            y=forecast["Upper Bound"],
            mode="lines",
            line={"width": 0},
            showlegend=False,
            hoverinfo="skip",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=forecast["Month"],
            y=forecast["Lower Bound"],
            mode="lines",
            fill="tonexty",
            fillcolor="rgba(22,174,192,0.14)",
            line={"width": 0},
            name=f"{int(confidence * 100)}% Prediction Interval",
            hoverinfo="skip",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=forecast["Month"],
            y=forecast["Forecast"],
            mode="lines+markers",
            name=f"{method_label(method)} Forecast",
            line={"color": "#1597A6", "width": 2.8, "dash": "dot"},
            marker={"size": 7},
        )
    )

    fig.add_vline(
        x=history["Month"].max(),
        line_width=1,
        line_dash="dash",
        line_color="#8AAAB2",
    )

    fig.add_annotation(
        x=history["Month"].max(),
        y=1.03,
        xref="x",
        yref="paper",
        text="Forecast begins",
        showarrow=False,
        font={"size": 9, "color": MUTED},
    )

    fig.update_xaxes(title_text="Month")
    fig.update_yaxes(
        title_text="Revenue",
        tickprefix="₹",
        tickformat="~s",
    )
    fig = style_figure(fig, height=430)

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={"displayModeBar": False},
    )

    st.caption(
        f"{periods}-month {method_label(method).lower()} forecast with "
        f"{int(confidence * 100)}% prediction interval."
    )


# ============================================================
# LIGHT THEMED TABLES
# ============================================================

def render_light_table(display: pd.DataFrame) -> None:
    table_html = display.to_html(
        index=False,
        classes="forecast-light-table",
        escape=True,
        border=0,
    )
    st.markdown(
        f'<div class="forecast-table-wrap">{table_html}</div>',
        unsafe_allow_html=True,
    )


# ============================================================
# FORECAST TABLE
# ============================================================

def render_forecast_table(forecast: pd.DataFrame) -> None:
    if forecast.empty:
        st.info("No forecast values are available.")
        return

    table = forecast.copy()
    table["Month"] = pd.to_datetime(
        table["Month"], errors="coerce"
    ).dt.strftime("%b %Y")

    for column in ["Forecast", "Lower Bound", "Upper Bound"]:
        table[column] = pd.to_numeric(
            table[column], errors="coerce"
        ).map(lambda value: format_currency(safe_float(value)))

    display = table[
        ["Month", "Forecast", "Lower Bound", "Upper Bound", "Forecast Horizon"]
    ].copy()

    display.columns = [
        "Month",
        "Forecast",
        "Lower Bound",
        "Upper Bound",
        "Horizon",
    ]

    render_light_table(display)


# ============================================================
# METHOD COMPARISON
# ============================================================

def render_method_comparison(
    comparison: pd.DataFrame,
    selected_method: str,
) -> None:
    if comparison.empty:
        st.info("Forecast comparison is not available.")
        return

    table = comparison.copy()
    table["Method"] = table["Method"].map(method_label)
    for column in ["MAE", "RMSE", "MAPE"]:
        table[column] = pd.to_numeric(table[column], errors="coerce")

    fig = go.Figure(
        go.Bar(
            x=table["Method"],
            y=table["MAPE"],
            text=[
                f"{value:.1f}%"
                if pd.notna(value)
                else "N/A"
                for value in table["MAPE"]
            ],
            textposition="outside",
            marker={"color": "#1597A6"},
        )
    )

    fig.update_yaxes(title="MAPE", ticksuffix="%")
    fig.update_xaxes(title="Forecasting Method")
    fig = style_figure(fig, height=330)

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={"displayModeBar": False},
    )

    display = table[
        ["Method", "MAE", "RMSE", "MAPE", "Backtest Periods"]
    ].copy()

    display["MAE"] = display["MAE"].map(
        lambda value: format_currency(safe_float(value))
    )
    display["RMSE"] = display["RMSE"].map(
        lambda value: format_currency(safe_float(value))
    )
    display["MAPE"] = display["MAPE"].map(
        lambda value: format_percentage(safe_float(value))
    )

    render_light_table(display)

    st.caption(
        f"Current forecast method: {method_label(selected_method)}. "
        "Lower MAPE indicates smaller historical percentage error."
    )


# ============================================================
# RELIABILITY
# ============================================================

def render_reliability(reliability: dict[str, object]) -> None:
    level = str(reliability.get("reliability_level", "N/A"))
    score = safe_float(reliability.get("reliability_score"), 0.0)
    interpretation = str(
        reliability.get(
            "interpretation",
            "Forecast reliability could not be evaluated.",
        )
    )

    method = method_label(str(reliability.get("method", "N/A")))
    mape = safe_float(reliability.get("mape"), 0.0)
    gap = reliability.get("model_gap")
    gap_value = safe_float(gap, float("nan"))

    gap_text = (
        f"{gap_value:.1f} percentage points"
        if pd.notna(gap_value)
        else "N/A"
    )

    st.markdown(
        f"""
        <div class="forecast-insight">
            <div class="forecast-insight-label">Forecast Reliability</div>
            <div class="forecast-insight-title">
                {escape(level)} · {score:.0f}/100
            </div>
            <div class="forecast-insight-text">
                <strong>Method:</strong> {escape(method)}
                &nbsp; · &nbsp;
                <strong>MAPE:</strong> {mape:.1f}%
                &nbsp; · &nbsp;
                <strong>Model gap:</strong> {escape(gap_text)}
                <br><br>
                {escape(interpretation)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# MAIN DASHBOARD
# ============================================================

def render_forecast_dashboard(
    on_back: Callable[[], None] | None = None,
) -> None:
    del on_back

    apply_theme("AQVASTAR | Forecast Intelligence")
    inject_forecast_css()

    render_brand()
    render_navigation("forecast")

    # Same floating Home treatment as the Regional dashboard.
    st.markdown(
        '<a href="?page=home" '
        'target="_self" '
        'class="forecast-floating-home" '
        'aria-label="Back to Home">'
        '<span class="forecast-floating-home-icon">⌂</span>'
        '<span class="forecast-floating-home-text">BACK TO HOME</span>'
        '</a>',
        unsafe_allow_html=True,
    )

    engine = TimeSeriesEngine()

    try:
        sales = engine._sales_data()
        latest_date = (
            pd.to_datetime(sales["posting_date"], errors="coerce").max()
            if not sales.empty
            else None
        )
    except (KeyError, TypeError, ValueError, OSError):
        latest_date = None

    render_header(latest_date)

    (
        periods,
        method_option,
        selected_method,
        window,
        confidence,
        run_forecast,
    ) = render_controls()

    settings = (
        periods,
        method_option,
        selected_method,
        window,
        confidence,
    )

    # A changed setting invalidates old results.
    if st.session_state.get("forecast_settings") != settings:
        st.session_state["forecast_settings"] = settings
        for key in (
            "forecast_result",
            "forecast_comparison",
            "forecast_reliability",
            "forecast_method",
        ):
            st.session_state.pop(key, None)

    # --------------------------------------------------------
    # ONLY RUN THE EXPENSIVE FORECAST WHEN THE USER CLICKS
    # --------------------------------------------------------

    if run_forecast:
        comparison = pd.DataFrame()
        reliability: dict[str, object] = {
            "method": selected_method,
            "mape": float("nan"),
            "backtest_periods": 0,
            "model_gap": float("nan"),
            "reliability_score": 0,
            "reliability_level": "Pending",
            "interpretation": (
                "Forecast reliability could not be fully evaluated."
            ),
        }

        calculation_state = st.empty()
        calculation_state.markdown(
            """
            <div class="forecast-calculating">
                <div class="forecast-calculating-inner">
                    <div class="forecast-calculating-spinner"></div>
                    <div class="forecast-calculating-title">
                        Calculating forecast intelligence
                    </div>
                    <div class="forecast-calculating-note">
                        Evaluating historical patterns, model accuracy and forecast uncertainty
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        try:
            comparison = engine.compare_forecast_methods(
                metric="Revenue",
                window=window,
                min_history=6,
            )
        except (KeyError, TypeError, ValueError, OSError):
            comparison = pd.DataFrame()

        best_method = "moving_average"

        if not comparison.empty:
            try:
                best_method = engine.best_forecast_method(
                    metric="Revenue",
                    window=window,
                    min_history=6,
                )
            except (KeyError, TypeError, ValueError, OSError):
                best_method = "moving_average"

        method = (
            best_method
            if method_option == "Auto"
            else selected_method
        )

        try:
            reliability = engine.forecast_reliability(
                metric="Revenue",
                window=window,
                min_history=6,
            )
        except (KeyError, TypeError, ValueError, OSError):
            pass

        forecast = pd.DataFrame()

        try:
            forecast = engine.forecast_prediction_intervals(
                metric="Revenue",
                periods=periods,
                method=method,
                window=window,
                min_history=6,
                confidence=confidence,
            )
        except (KeyError, TypeError, ValueError, OSError):
            try:
                forecast = engine.forecast_revenue(
                    periods=periods,
                    method=method,
                    window=window,
                ).copy()

                forecast["Lower Bound"] = pd.to_numeric(
                    forecast["Forecast"],
                    errors="coerce",
                )
                forecast["Upper Bound"] = pd.to_numeric(
                    forecast["Forecast"],
                    errors="coerce",
                )
                forecast["Confidence"] = confidence * 100.0
                forecast["Interval Width"] = 0.0
                forecast["Forecast Horizon"] = range(
                    1,
                    len(forecast) + 1,
                )
            except (KeyError, TypeError, ValueError, OSError):
                forecast = pd.DataFrame()

        calculation_state.empty()

        if forecast.empty:
            st.error(
                "The forecast could not be generated from the current sales database."
            )
            return

        st.session_state["forecast_result"] = forecast
        st.session_state["forecast_comparison"] = comparison
        st.session_state["forecast_reliability"] = reliability
        st.session_state["forecast_method"] = method

    # --------------------------------------------------------
    # DO NOT CALCULATE OR SHOW RESULTS UNTIL RUN FORECAST
    # --------------------------------------------------------

    forecast = st.session_state.get("forecast_result")

    if not isinstance(forecast, pd.DataFrame) or forecast.empty:
        st.markdown(
            """
            <div class="forecast-ready">
                <div class="forecast-ready-inner">
                    <div class="forecast-ready-title">
                        Forecast is ready when you are.
                    </div>
                    <div class="forecast-ready-note">
                        Choose your settings above and click
                        <strong>RUN FORECAST</strong> when you want to start.
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    comparison = st.session_state.get(
        "forecast_comparison",
        pd.DataFrame(),
    )
    reliability = st.session_state.get(
        "forecast_reliability",
        {},
    )
    method = str(
        st.session_state.get(
            "forecast_method",
            selected_method,
        )
    )

    render_executive_kpis(forecast, reliability, method)

    render_section(
        "Revenue Forecast",
        "Projected revenue trajectory",
        "Historical monthly revenue is shown alongside the selected forecast and its uncertainty interval.",
    )

    st.markdown(
        '<div class="forecast-card">',
        unsafe_allow_html=True,
    )
    render_forecast_chart(
        engine,
        forecast,
        periods,
        method,
        window,
        confidence,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    col1, col2 = st.columns([1.35, 1])

    with col1:
        render_section(
            "Forecast Output",
            "Upcoming revenue",
            "Monthly projections and the corresponding prediction bounds.",
        )
        render_forecast_table(forecast)

    with col2:
        render_section(
            "Reliability",
            "How much should you trust the projection?",
            "Reliability combines historical forecast error, available backtest history and model agreement.",
        )
        render_reliability(reliability)

    render_section(
        "Model Evaluation",
        "Compare forecasting methods",
        "Walk-forward backtesting compares the supported methods using historical monthly revenue.",
    )

    st.markdown(
        '<div class="forecast-card">',
        unsafe_allow_html=True,
    )

    if isinstance(comparison, pd.DataFrame) and not comparison.empty:
        render_method_comparison(comparison, method)
    else:
        st.info(
            "Model comparison is not available, but the forecast was generated."
        )

    st.markdown("</div>", unsafe_allow_html=True)


def main() -> None:
    """Entry point used by the application router."""
    render_forecast_dashboard()


if __name__ == "__main__":
    main()