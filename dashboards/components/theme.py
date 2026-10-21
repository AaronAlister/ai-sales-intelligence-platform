"""
AQVASTAR dashboard theme and global styling.

Provides:
- Global AQVASTAR theme
- Color system
- Navigation styling
- KPI cards
- Alternating light/dark dashboard sections
- Chart cards
- Business insight cards
"""

from __future__ import annotations

import streamlit as st


# ============================================================
# AQVASTAR COLOR SYSTEM
# ============================================================

DEEP_OCEAN = "#063B49"
OCEAN = "#075C6B"
AQUA = "#10AFC0"
AQUA_LIGHT = "#DDF5F7"

WHITE = "#FFFFFF"
SURFACE = "#F5F8F8"
SURFACE_DARK = "#0C1820"

TEXT = "#102027"
MUTED = "#607782"
BORDER = "#D5E4E7"

# Additional shades used by dashboard sections
OCEAN_SOFT = "#0A5361"
AQUA_PALE = "#EFFBFC"
DARK_BORDER = "#146A78"
DARK_MUTED = "#C9E4E8"


# ============================================================
# GLOBAL THEME
# ============================================================

def apply_theme(page_title: str) -> None:
    """
    Apply the AQVASTAR Streamlit theme and global CSS.

    Args:
        page_title: Browser/page title displayed by Streamlit.
    """

    st.set_page_config(
        page_title=page_title,
        page_icon="assets/aqvastar_logo.png",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    st.markdown(
        f"""
        <style>

        /* ==================================================
           GLOBAL
        ================================================== */

        #MainMenu {{
            visibility: hidden;
        }}

        footer {{
            visibility: hidden;
        }}

        header {{
            visibility: hidden;
        }}

        .stApp {{
            background:
                radial-gradient(
                    circle at 85% 5%,
                    rgba(16, 175, 192, 0.08),
                    transparent 28%
                ),
                {SURFACE};
            color: {TEXT};
        }}

        .block-container {{
            max-width: 1440px;
            padding-top: 2.5rem;
            padding-bottom: 4rem;
            padding-left: 5.5rem;
            padding-right: 5.5rem;
        }}

        /* ==================================================
           STREAMLIT ELEMENT SPACING
        ================================================== */

        [data-testid="stVerticalBlock"] {{
            gap: 0.5rem;
        }}

        /* ==================================================
           BUTTON RESET (for non‑navigation buttons)
        ================================================== */

        .stButton > button {{
            border: none;
            background: transparent;
            color: {MUTED};
            font-size: 0.72rem;
            font-weight: 600;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            padding: 0.45rem 0.25rem;
            border-radius: 0;
        }}

        .stButton > button:hover {{
            color: {OCEAN};
            border: none;
            background: transparent;
        }}

        .stButton > button:focus {{
            box-shadow: none;
            border: none;
        }}

        /* ==================================================
           DASHBOARD NAVIGATION BUTTONS
           (applied to buttons inside st.columns)
        ================================================== */

        div[data-testid="stHorizontalBlock"] .stButton > button {{
            border: none !important;
            background: transparent !important;
            box-shadow: none !important;
            color: {MUTED} !important;
            font-size: 0.78rem !important;
            font-weight: 650 !important;
            letter-spacing: 0.08em !important;
            padding: 0.45rem 0.25rem !important;
            text-transform: none !important;
        }}

        div[data-testid="stHorizontalBlock"] .stButton > button:hover {{
            color: #075C6B !important;
            background: transparent !important;
        }}

        div[data-testid="stHorizontalBlock"] .stButton > button:focus {{
            border: none !important;
            box-shadow: none !important;
        }}

        /* ==================================================
           KPI CARDS
        ================================================== */

        .aq-kpi-card {{
            background: {WHITE};
            border: 1px solid {BORDER};
            border-radius: 14px;
            padding: 1.35rem 1.4rem;
            min-height: 135px;
            box-shadow: 0 8px 30px rgba(6, 59, 73, 0.045);
        }}

        .aq-kpi-label {{
            color: {MUTED};
            font-size: 0.68rem;
            font-weight: 700;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            margin-bottom: 0.7rem;
        }}

        .aq-kpi-value {{
            color: {DEEP_OCEAN};
            font-size: 1.8rem;
            font-weight: 750;
            letter-spacing: -0.03em;
        }}

        .aq-kpi-description {{
            color: {MUTED};
            font-size: 0.72rem;
            margin-top: 0.45rem;
        }}

        /* ==================================================
           DASHBOARD SECTION SYSTEM
           
           Sections alternate between:
           LIGHT AQUA
           DARK OCEAN
           LIGHT AQUA
           DARK OCEAN
        ================================================== */

        .aq-section {{
            width: 100%;
            box-sizing: border-box;
            border-radius: 24px;
            padding: 2rem 2rem 2.15rem 2rem;
            margin: 2.2rem 0;
            position: relative;
            overflow: hidden;
        }}

        /* -----------------------------------------------
           Decorative aquatic rings
        ----------------------------------------------- */

        .aq-section::before {{
            content: "";
            position: absolute;
            width: 220px;
            height: 220px;
            border: 1px solid rgba(16, 175, 192, 0.12);
            border-radius: 50%;
            right: -90px;
            top: -120px;
            pointer-events: none;
        }}

        .aq-section::after {{
            content: "";
            position: absolute;
            width: 155px;
            height: 155px;
            border: 1px solid rgba(16, 175, 192, 0.10);
            border-radius: 50%;
            right: -58px;
            top: -86px;
            pointer-events: none;
        }}

        /* ==================================================
           LIGHT SECTION
        ================================================== */

        .aq-section-light {{
            background:
                radial-gradient(
                    circle at 95% 0%,
                    rgba(16, 175, 192, 0.10),
                    transparent 260px
                ),
                {AQUA_LIGHT};

            border: 1px solid #CFE9EC;

            box-shadow:
                0 14px 36px rgba(6, 59, 73, 0.065);
        }}

        /* ==================================================
           DARK SECTION
        ================================================== */

        .aq-section-dark {{
            background:
                radial-gradient(
                    circle at 95% 0%,
                    rgba(16, 175, 192, 0.20),
                    transparent 280px
                ),
                {DEEP_OCEAN};

            border: 1px solid {DARK_BORDER};

            box-shadow:
                0 18px 40px rgba(6, 59, 73, 0.15);
        }}

        /* ==================================================
           SECTION HEADER
        ================================================== */

        .aq-section-header {{
            position: relative;
            z-index: 2;
            margin-bottom: 0.3rem;
        }}

        .aq-section-kicker {{
            color: {AQUA};
            font-size: 0.7rem;
            font-weight: 800;
            letter-spacing: 0.18em;
            line-height: 1.2;
            text-transform: uppercase;
            margin-bottom: 0.55rem;
        }}

        .aq-section-title {{
            color: {TEXT};
            font-size: 1.65rem;
            line-height: 1.15;
            font-weight: 800;
            letter-spacing: -0.035em;
            margin: 0;
        }}

        .aq-section-description {{
            color: {MUTED};
            font-size: 0.94rem;
            line-height: 1.55;
            margin-top: 0.55rem;
            margin-bottom: 0;
            max-width: 850px;
        }}

        /* -----------------------------------------------
           Dark section typography
        ----------------------------------------------- */

        .aq-section-dark .aq-section-title {{
            color: {WHITE};
        }}

        .aq-section-dark .aq-section-description {{
            color: {DARK_MUTED};
        }}

        /* ==================================================
           CHART GRID
        ================================================== */

        .aq-chart-grid {{
            position: relative;
            z-index: 2;
            margin-top: 1.5rem;
        }}

        /* ==================================================
           CHART CARD
        ================================================== */

        .aq-chart-card {{
            background: {WHITE};
            border: 1px solid {BORDER};
            border-radius: 18px;
            padding: 1.2rem 1.2rem 1.05rem 1.2rem;
            box-sizing: border-box;
            min-height: 100%;
            box-shadow:
                0 8px 24px rgba(6, 59, 73, 0.055);
        }}

        .aq-chart-card-title {{
            color: {TEXT};
            font-size: 0.98rem;
            font-weight: 750;
            line-height: 1.3;
            margin-bottom: 0.3rem;
        }}

        .aq-chart-card-description {{
            color: {MUTED};
            font-size: 0.79rem;
            line-height: 1.45;
            margin-bottom: 0.7rem;
        }}

        /* ==================================================
           CHART CARD INSIDE DARK SECTION
        ================================================== */

        .aq-section-dark .aq-chart-card {{
            border-color: #D5E4E7;
            box-shadow:
                0 10px 26px rgba(0, 0, 0, 0.13);
        }}

        /* ==================================================
           BUSINESS INSIGHT
        ================================================== */

        .aq-insight {{
            margin-top: 0.8rem;
            padding: 0.75rem 0.85rem;
            border-radius: 12px;
            background: {AQUA_PALE};
            border-left: 3px solid {AQUA};
        }}

        .aq-insight-label {{
            color: {AQUA};
            font-size: 0.63rem;
            font-weight: 800;
            letter-spacing: 0.15em;
            line-height: 1.2;
            text-transform: uppercase;
            margin-bottom: 0.25rem;
        }}

        .aq-insight-text {{
            color: {TEXT};
            font-size: 0.78rem;
            line-height: 1.5;
            margin: 0;
        }}

        /* ==================================================
           DARK SECTION INSIGHT
        ================================================== */

        .aq-section-dark .aq-insight {{
            background: #F0FAFB;
        }}

        /* ==================================================
           TABLE CONTAINER
        ================================================== */

        .aq-table-container {{
            position: relative;
            z-index: 2;
            background: rgba(3, 31, 39, 0.40);
            border: 1px solid rgba(255, 255, 255, 0.09);
            border-top: 2px solid {AQUA};
            border-radius: 16px;
            overflow: hidden;
            margin-top: 1.4rem;
        }}

        /* ==================================================
           WHITE CONTENT CARD
        ================================================== */

        .aq-content-card {{
            background: {WHITE};
            border: 1px solid {BORDER};
            border-radius: 18px;
            padding: 1.35rem;
            box-sizing: border-box;
            box-shadow:
                0 8px 26px rgba(6, 59, 73, 0.05);
        }}

        /* ==================================================
           SMALL SECTION LABEL
        ================================================== */

        .aq-label {{
            color: {AQUA};
            font-size: 0.68rem;
            font-weight: 800;
            letter-spacing: 0.16em;
            text-transform: uppercase;
        }}

        /* ==================================================
           SECTION SPACING
        ================================================== */

        .aq-section-gap {{
            height: 0.15rem;
        }}

        /* ==================================================
           SELECTBOX
        ================================================== */

        .stSelectbox label {{
            color: {MUTED};
            font-size: 0.78rem;
            font-weight: 600;
        }}

        .stSelectbox [data-baseweb="select"] > div {{
            border-color: {BORDER};
            border-radius: 10px;
        }}

        /* ==================================================
           DATAFRAME
        ================================================== */

        [data-testid="stDataFrame"] {{
            border-radius: 14px;
            overflow: hidden;
        }}

        /* ==================================================
           PLOTLY
        ================================================== */

        .js-plotly-plot {{
            border-radius: 12px;
            overflow: hidden;
        }}

        /* ==================================================
           SCROLLBAR
        ================================================== */

        ::-webkit-scrollbar {{
            width: 7px;
            height: 7px;
        }}

        ::-webkit-scrollbar-track {{
            background: {SURFACE};
        }}

        ::-webkit-scrollbar-thumb {{
            background: {BORDER};
            border-radius: 10px;
        }}

        ::-webkit-scrollbar-thumb:hover {{
            background: #B7D2D7;
        }}

        /* ==================================================
           HOMEPAGE MODULE NAVIGATION
           (for the clickable cards on the home page)
        ================================================== */

        .aq-module-link {{
            display: block;
            text-decoration: none !important;
            color: inherit !important;
            width: 100%;
        }}

        .aq-module-link:hover {{
            text-decoration: none !important;
            color: inherit !important;
        }}

        .aq-module-card {{
            cursor: pointer;
            transition:
                transform 180ms ease,
                box-shadow 180ms ease;
        }}

        .aq-module-link:hover .aq-module-card {{
            transform: translateY(-3px);
            box-shadow: 0 18px 40px rgba(6, 59, 73, 0.12);
        }}

        .aq-module-link:active .aq-module-card {{
            transform: translateY(-1px);
        }}

        /* ==================================================
           MOBILE / SMALL SCREEN
        ================================================== */

        @media (max-width: 900px) {{

            .block-container {{
                padding-left: 1.25rem;
                padding-right: 1.25rem;
            }}

            .aq-section {{
                padding: 1.5rem;
                border-radius: 18px;
            }}

            .aq-section-title {{
                font-size: 1.4rem;
            }}

        }}

        </style>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# SECTION HEADER
# ============================================================

def render_section_header(
    kicker: str,
    title: str,
    description: str,
    dark: bool = False,
) -> None:
    """
    Render a standalone AQVASTAR section header.

    This is intended to establish the visual identity of a
    dashboard section.

    Args:
        kicker: Small uppercase section label.
        title: Main section heading.
        description: Supporting explanation.
        dark: Whether to use the dark ocean variant.
    """

    section_variant = (
        "aq-section-dark"
        if dark
        else "aq-section-light"
    )

    st.markdown(
        f"""
        <div class="aq-section {section_variant}">
            <div class="aq-section-header">
                <div class="aq-section-kicker">
                    {kicker}
                </div>

                <div class="aq-section-title">
                    {title}
                </div>

                <div class="aq-section-description">
                    {description}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# SECTION OPEN / CLOSE HELPERS
# ============================================================

def render_section_start(
    dark: bool = False,
) -> None:
    """
    Render the opening container for a dashboard section.

    This helper is useful when the section must contain actual
    Streamlit components such as charts, tables, or metrics.

    Args:
        dark: Whether to use the dark ocean variant.
    """

    section_variant = (
        "aq-section-dark"
        if dark
        else "aq-section-light"
    )

    st.markdown(
        f"""
        <div class="aq-section {section_variant}">
        """,
        unsafe_allow_html=True,
    )


def render_section_end() -> None:
    """Close a dashboard section container."""

    st.markdown(
        """
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# CHART CARD HEADER
# ============================================================

def render_chart_header(
    title: str,
    description: str,
) -> None:
    """
    Render the title and description for an individual chart card.

    Args:
        title: Chart title.
        description: Short explanation of the chart.
    """

    st.markdown(
        f"""
        <div class="aq-chart-card-title">
            {title}
        </div>

        <div class="aq-chart-card-description">
            {description}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# BUSINESS INSIGHT
# ============================================================

def render_insight(
    text: str,
) -> None:
    """
    Render a business insight underneath a chart.

    Args:
        text: Business interpretation of the visualization.
    """

    st.markdown(
        f"""
        <div class="aq-insight">
            <div class="aq-insight-label">
                Business Insight
            </div>

            <p class="aq-insight-text">
                {text}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# CONTENT CARD
# ============================================================

def render_content_card_start() -> None:
    """Open a white AQVASTAR content card."""

    st.markdown(
        """
        <div class="aq-content-card">
        """,
        unsafe_allow_html=True,
    )


def render_content_card_end() -> None:
    """Close a white AQVASTAR content card."""

    st.markdown(
        """
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# TABLE CONTAINER
# ============================================================

def render_table_container_start() -> None:
    """Open a dark table container."""

    st.markdown(
        """
        <div class="aq-table-container">
        """,
        unsafe_allow_html=True,
    )


def render_table_container_end() -> None:
    """Close a dark table container."""

    st.markdown(
        """
        </div>
        """,
        unsafe_allow_html=True,
    )