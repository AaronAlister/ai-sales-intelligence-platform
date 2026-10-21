"""
AQVASTAR Sales Intelligence Platform.

Executive dashboard entry point.
"""

from __future__ import annotations

from textwrap import dedent

import streamlit as st

from dashboards.components.navigation import (
    render_brand,
    render_navigation,
)
from dashboards.components.theme import (
    AQUA,
    DEEP_OCEAN,
    OCEAN,
    SURFACE_DARK,
    apply_theme,
)

import hashlib
import tempfile
from pathlib import Path
from typing import Any

import pandas as pd

from database.db import get_connection
from database.etl_pipeline import (
    _incoming_business_key,
    _load_existing_record_counts,
    upload_excel,
)
from database.preprocessing import preprocess_data
from database.queries import SalesQueries
from database.validation import validate_data


# ============================================================
# HERO
# ============================================================


def render_hero() -> None:
    """Render the executive dashboard hero section."""

    hero_html = (
        '<section style="'
        "position:relative;"
        "overflow:hidden;"
        "min-height:410px;"
        "padding:3.8rem 3.6rem;"
        "margin-bottom:2.8rem;"
        "border-radius:18px;"
        f"background:"
        f"radial-gradient(circle at 88% 20%,"
        f"rgba(16,175,192,0.65),transparent 30%),"
        f"linear-gradient(120deg,"
        f"{DEEP_OCEAN} 0%,{OCEAN} 58%,#117F8D 100%);"
        "box-shadow:0 20px 60px rgba(6,59,73,0.16);"
        '">'

        '<div style="'
        "position:absolute;"
        "width:340px;"
        "height:340px;"
        "right:-70px;"
        "bottom:-190px;"
        "border:1px solid rgba(255,255,255,0.22);"
        "border-radius:50%;"
        '"></div>'

        '<div style="'
        "position:absolute;"
        "width:480px;"
        "height:480px;"
        "right:-140px;"
        "bottom:-260px;"
        "border:1px solid rgba(255,255,255,0.12);"
        "border-radius:50%;"
        '"></div>'

        '<div style="'
        "position:relative;"
        "max-width:720px;"
        "color:white;"
        '">'

        '<div style="'
        f"color:{AQUA};"
        "font-size:0.72rem;"
        "font-weight:800;"
        "letter-spacing:0.16em;"
        "text-transform:uppercase;"
        "margin-bottom:1.4rem;"
        '">'
        "Sales Intelligence Platform"
        "</div>"

        '<div style="'
        "font-size:clamp(3rem,5vw,5.4rem);"
        "line-height:0.92;"
        "font-weight:800;"
        "letter-spacing:-0.055em;"
        "margin-bottom:1.7rem;"
        '">'
        "Understand<br>"
        "What Drives<br>"
        "Your Business"
        "</div>"

        '<div style="'
        "max-width:560px;"
        "color:rgba(255,255,255,0.72);"
        "font-size:1rem;"
        "line-height:1.65;"
        '">'
        "A unified intelligence layer for revenue, "
        "customers, products, regions, pricing and "
        "business trends."
        "</div>"

        "</div>"
        "</section>"
    )

    st.markdown(
        hero_html,
        unsafe_allow_html=True,
    )



# ============================================================
# ASK AQVASTAR
# ============================================================


def _select_aqvastar_question(question: str) -> None:
    """Place a suggested question in the input."""
    st.session_state["aqvastar_question"] = question


def render_ask_aqvastar() -> None:
    """Render the Ask AQVASTAR entry point."""

    st.markdown(
        dedent(
            """
            <style>
            .st-key-aqvastar_ask_panel {
                margin: 0.2rem 0 2.8rem 0;
                padding: 1.5rem 1.6rem 1.35rem;
                border: 1px solid #CFE7EA;
                border-radius: 22px;
                background: linear-gradient(
                    135deg, #FFFFFF 0%, #F2FAFB 100%
                );
                box-shadow: 0 10px 28px rgba(6, 59, 73, 0.05);
            }

            .aqv-ask-eyebrow {
                color: #078C9B;
                font-size: 0.72rem;
                font-weight: 800;
                letter-spacing: 0.13em;
                text-transform: uppercase;
                margin-bottom: 0.45rem;
            }

            .aqv-ask-title {
                color: #073F4A;
                font-size: 1.55rem;
                line-height: 1.25;
                font-weight: 780;
                letter-spacing: -0.025em;
                margin: 0;
            }

            .aqv-ask-copy {
                color: #607985;
                font-size: 0.94rem;
                margin-top: 0.4rem;
                margin-bottom: 0.9rem;
            }

            .st-key-aqvastar_ask_panel
            [data-testid="stTextInput"] input {
                border-color: #CFE1E5;
                border-radius: 11px;
                min-height: 2.8rem;
            }

            .st-key-aqvastar_ask_panel
            [data-testid="stFormSubmitButton"] button {
                background: #0AA7B5;
                color: #FFFFFF;
                border: 1px solid #0AA7B5;
                border-radius: 11px;
                min-height: 2.8rem;
                font-weight: 650;
            }

            .st-key-aqvastar_ask_panel
            [data-testid="stFormSubmitButton"] button:hover {
                background: #087F8C;
                border-color: #087F8C;
                color: #FFFFFF;
            }

            .aqv-suggestions-heading {
                display: flex;
                align-items: center;
                gap: 0.65rem;
                margin: 1.45rem 0 0.8rem;
                padding-bottom: 0.65rem;
                border-bottom: 1px solid #DCECEF;
            }

            .aqv-suggestions-badge {
                display: inline-flex;
                align-items: center;
                gap: 0.4rem;
                padding: 0.35rem 0.65rem;
                border: 1px solid #BFE5E9;
                border-radius: 7px;
                background: #E4F7F8;
                color: #087F8C;
                font-size: 0.72rem;
                font-weight: 800;
                letter-spacing: 0.08em;
                text-transform: uppercase;
            }

            .aqv-suggestions-help {
                color: #71858C;
                font-size: 0.82rem;
            }

            /* Each suggestion has its own keyed card wrapper. */
            [class*="st-key-aqv_suggestion_card_"] {
                box-sizing: border-box !important;
                min-height: 4.25rem;
                padding: 0.35rem 0.75rem !important;
                border: 1px solid #C9E2E6 !important;
                border-radius: 12px !important;
                background: #FFFFFF !important;
                box-shadow: 0 3px 10px rgba(6, 59, 73, 0.06) !important;
                transition: background 150ms ease, border-color 150ms ease,
                    box-shadow 150ms ease, transform 150ms ease;
            }

            [class*="st-key-aqv_suggestion_card_"] [data-testid="stButton"] {
                width: 100%;
            }

            [class*="st-key-aqv_suggestion_card_"] [data-testid="stButton"] button {
                width: 100% !important;
                min-height: 3.2rem !important;
                padding: 0.45rem 0.35rem !important;
                justify-content: flex-start !important;
                text-align: left !important;
                white-space: normal !important;
                background: transparent !important;
                color: #245260 !important;
                border: none !important;
                box-shadow: none !important;
            }

            [class*="st-key-aqv_suggestion_card_"] [data-testid="stButton"] button p {
                width: 100%;
                margin: 0 !important;
                text-align: left !important;
                white-space: normal !important;
                line-height: 1.4 !important;
            }

            [class*="st-key-aqv_suggestion_card_"]:hover {
                background: #F1FBFC !important;
                border-color: #62C5CF !important;
                box-shadow: 0 6px 16px rgba(6, 125, 140, 0.12) !important;
                transform: translateY(-1px);
            }

            [class*="st-key-aqv_suggestion_card_"]:hover
            [data-testid="stButton"] button {
                color: #075B68 !important;
            }

            /* Continue the answer inside the Ask AQVASTAR panel. */
            .st-key-aqvastar_answer_card {
                width: 100% !important;
                max-width: 100% !important;
                margin: 1.1rem 0 0 !important;
                padding: 1.2rem 0 0.35rem !important;
                box-sizing: border-box !important;
                border: none !important;
                border-top: 1px solid #DCECEF !important;
                border-radius: 0 !important;
                background: transparent !important;
                box-shadow: none !important;
                overflow-wrap: anywhere;
            }

            .aqv-answer-header {
                margin-bottom: 1.25rem;
                padding-bottom: 1rem;
                border-bottom: 1px solid #DCECEF;
            }

            .aqv-answer-kicker {
                display: inline-block;
                margin-bottom: 0.6rem;
                padding: 0.35rem 0.65rem;
                border: 1px solid #BFE5E9;
                border-radius: 7px;
                background: #E4F7F8;
                color: #087F8C;
                font-size: 0.72rem;
                font-weight: 800;
                letter-spacing: 0.09em;
            }

            .aqv-answer-title {
                margin: 0 !important;
                color: #073F4A !important;
                font-size: 1.6rem !important;
                font-weight: 760 !important;
            }

            .aqv-answer-subtitle {
                margin: 0.4rem 0 0;
                color: #607985;
                font-size: 0.9rem;
            }

            .st-key-aqvastar_answer_card [data-testid="stDataFrame"] {
                max-width: 100%;
            }

            .st-key-aqvastar_answer_card [data-testid="stAlert"] {
                margin-top: 0.75rem;
                border: 1px solid #E8D59A;
                border-radius: 10px;
                background: #FFF8E5;
                color: #654F16;
            }

            .st-key-aqvastar_answer_card [data-testid="stAlert"] p {
                color: #654F16 !important;
            }
            </style>
            """
        ),
        unsafe_allow_html=True,
    )

    with st.container(key="aqvastar_ask_panel", border=False):
        st.markdown(
            '<div class="aqv-ask-eyebrow">'
            'AI-POWERED SALES INTELLIGENCE</div>'
            '<div class="aqv-ask-title">'
            '✦ Ask AQVASTAR</div>'
            '<div class="aqv-ask-copy">'
            'Ask a question about your sales data and find out '
            'what to investigate next.</div>',
            unsafe_allow_html=True,
        )

        with st.form(
            "aqvastar_question_form",
            clear_on_submit=False,
        ):
            input_col, button_col = st.columns(
                [5, 1.25],
                gap="small",
            )

            with input_col:
                question = st.text_input(
                    "Ask a question",
                    key="aqvastar_question",
                    placeholder=(
                        "e.g. Which products drove the change "
                        "in revenue?"
                    ),
                    label_visibility="collapsed",
                )

            with button_col:
                submitted = st.form_submit_button(
                    "Ask AQVASTAR  →",
                    use_container_width=True,
                )

        st.markdown(
            '<div class="aqv-suggestions-heading">'
            '<span class="aqv-suggestions-badge">✦ Try asking</span>'
            '<span class="aqv-suggestions-help">'
            'Choose a question to get started</span>'
            '</div>',
            unsafe_allow_html=True,
        )

        suggestions = [
            "Why did sales change this month?",
            "Which products generate the most revenue?",
            "Which customers have reduced their purchases?",
            "How are discounts affecting sales?",
        ]

        for row_start in (0, 2):
            suggestion_cols = st.columns(2, gap="medium")

            for offset, (col, suggested_question) in enumerate(zip(
                suggestion_cols,
                suggestions[row_start:row_start + 2],
            )):
                suggestion_index = row_start + offset
                with col:
                    with st.container(
                        key=f"aqv_suggestion_card_{suggestion_index}",
                        border=False,
                    ):
                        st.button(
                            suggested_question,
                            key=f"aqvastar_suggestion_{suggestion_index}",
                            use_container_width=True,
                            on_click=_select_aqvastar_question,
                            args=(suggested_question,),
                            type="tertiary",
                        )

        if submitted:
            if question.strip():
                st.session_state.pop("aqvastar_answer_result", None)
                st.session_state.pop("aqvastar_answer_error", None)

                try:
                    from ai.aqvastar_assistant import answer_question

                    with st.spinner("Analyzing your sales data..."):
                        st.session_state["aqvastar_answer_result"] = (
                            answer_question(question.strip())
                        )
                except (RuntimeError, ValueError, FileNotFoundError) as exc:
                    st.session_state["aqvastar_answer_error"] = str(exc)
                except Exception as exc:
                    error_message = str(exc)
                    normalized_error = error_message.upper()

                    if "503" in error_message or "UNAVAILABLE" in normalized_error:
                        st.session_state["aqvastar_answer_error"] = (
                            "Gemini is experiencing high demand. "
                            "Please wait a moment and try again."
                        )
                    elif (
                        "429" in error_message
                        or "RESOURCE_EXHAUSTED" in normalized_error
                    ):
                        st.session_state["aqvastar_answer_error"] = (
                            "The Gemini API usage limit has been reached. "
                            "Please try again later or check your API quota."
                        )
                    else:
                        st.session_state["aqvastar_answer_error"] = (
                            "AQVASTAR couldn't generate an answer. "
                            "Please try again. If the issue persists, "
                            "check the terminal for the error details."
                        )
                        print(f"AQVASTAR Gemini error: {error_message}")
            else:
                st.warning(
                    "Enter a question or choose one of the suggestions."
                )

        answer_error = st.session_state.get("aqvastar_answer_error")
        answer_result = st.session_state.get("aqvastar_answer_result")

        # Keep both successful answers and errors inside one bounded response card.
        if answer_error or answer_result:
            with st.container(key="aqvastar_answer_card", border=False):
                st.markdown(
                    """
                    <div class="aqv-answer-header">
                        <div class="aqv-answer-kicker">✦ AQVASTAR ANALYSIS</div>
                        <h2 class="aqv-answer-title">Your sales insights</h2>
                        <p class="aqv-answer-subtitle">
                            Findings based on your sales data, with supporting
                            evidence and recommended next steps.
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if answer_error:
                    st.warning(answer_error, icon="⚠️")
                elif answer_result:
                    st.markdown(answer_result.get("answer", "No answer was returned."))

                    display_evidence = answer_result.get("display_evidence", {})
                    evidence_table = display_evidence.get("table")

                    if isinstance(evidence_table, pd.DataFrame):
                        if not evidence_table.empty:
                            st.markdown(
                                f"**{display_evidence.get('title', 'Supporting data')}**"
                            )
                            st.dataframe(
                                evidence_table,
                                use_container_width=True,
                                hide_index=True,
                            )
                        else:
                            st.caption(
                                "No matching rows were found for this comparison."
                            )

                    data_notes = answer_result.get("data_notes", [])
                    if data_notes:
                        with st.expander("About this analysis"):
                            for note in data_notes:
                                st.markdown(f"- {note}")

# ============================================================
# SECTION HEADING
# ============================================================


def render_section_heading() -> None:
    """Render the intelligence section heading."""

    heading_html = (
        '<div style="'
        "margin-bottom:1.5rem;"
        "padding-left:0.15rem;"
        '">'

        '<div style="'
        f"color:{SURFACE_DARK};"
        "font-size:2rem;"
        "font-weight:750;"
        "letter-spacing:-0.035em;"
        "line-height:1.15;"
        '">'
        "Business intelligence, without the noise."
        "</div>"

        "</div>"
    )

    st.markdown(
        heading_html,
        unsafe_allow_html=True,
    )


# ============================================================
# ICONS
# ============================================================


def render_sales_icon() -> str:
    """Return the sales performance icon SVG."""

    return (
        '<svg width="42" height="42" viewBox="0 0 48 48" '
        'fill="none" xmlns="http://www.w3.org/2000/svg">'
        '<path d="M8 34H40" '
        'stroke="#10AFC0" stroke-width="2.2" '
        'stroke-linecap="round"/>'
        '<rect x="11" y="24" width="6" height="10" rx="1.5" '
        'stroke="#10AFC0" stroke-width="2.2"/>'
        '<rect x="21" y="18" width="6" height="16" rx="1.5" '
        'stroke="#10AFC0" stroke-width="2.2"/>'
        '<rect x="31" y="11" width="6" height="23" rx="1.5" '
        'stroke="#10AFC0" stroke-width="2.2"/>'
        '</svg>'
    )


def render_customer_icon() -> str:
    """Return the customer icon SVG."""

    return (
        '<svg width="42" height="42" viewBox="0 0 48 48" '
        'fill="none" xmlns="http://www.w3.org/2000/svg">'
        '<circle cx="19" cy="18" r="6" '
        'stroke="#10AFC0" stroke-width="2.2"/>'
        '<circle cx="31" cy="20" r="5" '
        'stroke="#10AFC0" stroke-width="2.2"/>'
        '<path d="M8.5 35C9.8 28.8 14.1 26 19 26'
        'C23.9 26 28.2 28.8 29.5 35" '
        'stroke="#10AFC0" stroke-width="2.2" '
        'stroke-linecap="round"/>'
        '<path d="M27.5 29C29 27.1 31.2 26.2 33.5 26.2'
        'C37.2 26.2 40 28.6 40.5 33" '
        'stroke="#10AFC0" stroke-width="2.2" '
        'stroke-linecap="round"/>'
        "</svg>"
    )


def render_product_icon() -> str:
    """Return the product icon SVG."""

    return (
        '<svg width="42" height="42" viewBox="0 0 48 48" '
        'fill="none" xmlns="http://www.w3.org/2000/svg">'
        '<path d="M24 7L38 15V32L24 41L10 32V15L24 7Z" '
        'stroke="white" stroke-width="2.2" '
        'stroke-linejoin="round"/>'
        '<path d="M10 15L24 23L38 15" '
        'stroke="white" stroke-width="2.2" '
        'stroke-linejoin="round"/>'
        '<path d="M24 23V41" '
        'stroke="white" stroke-width="2.2"/>'
        "</svg>"
    )


def render_region_icon() -> str:
    """Return the regional icon SVG."""

    return (
        '<svg width="42" height="42" viewBox="0 0 48 48" '
        'fill="none" xmlns="http://www.w3.org/2000/svg">'
        '<circle cx="24" cy="24" r="16" '
        'stroke="white" stroke-width="2.2"/>'
        '<path d="M8 24H40" '
        'stroke="white" stroke-width="2.2"/>'
        '<path d="M24 8C19.8 12.4 18 17.7 18 24'
        'C18 30.3 19.8 35.6 24 40" '
        'stroke="white" stroke-width="2.2"/>'
        '<path d="M24 8C28.2 12.4 30 17.7 30 24'
        'C30 30.3 28.2 35.6 24 40" '
        'stroke="white" stroke-width="2.2"/>'
        "</svg>"
    )


def render_pricing_icon() -> str:
    """Return the pricing icon SVG."""

    return (
        '<svg width="42" height="42" viewBox="0 0 48 48" '
        'fill="none" xmlns="http://www.w3.org/2000/svg">'
        '<path d="M9 20L27 8H40V21L22 39L9 26V20Z" '
        'stroke="#10AFC0" stroke-width="2.2" '
        'stroke-linejoin="round"/>'
        '<circle cx="34" cy="15" r="2.5" '
        'fill="#10AFC0"/>'
        "</svg>"
    )


# ============================================================
# DECORATIVE GRAPHICS
# ============================================================


def render_customer_graphic() -> str:
    """Return the decorative customer illustration."""

    return (
        '<div style="'
        "position:absolute;"
        "right:0.9rem;"
        "bottom:0.2rem;"
        "width:150px;"
        "height:115px;"
        "opacity:0.92;"
        "pointer-events:none;"
        '">'

        '<svg width="150" height="115" '
        'viewBox="0 0 150 115" '
        'fill="none" '
        'xmlns="http://www.w3.org/2000/svg">'

        '<circle cx="80" cy="34" r="17" '
        'fill="rgba(16,175,192,0.13)" '
        'stroke="rgba(16,175,192,0.28)" '
        'stroke-width="1.5"/>'

        '<circle cx="47" cy="48" r="12" '
        'fill="rgba(16,175,192,0.09)"/>'

        '<circle cx="113" cy="48" r="12" '
        'fill="rgba(16,175,192,0.09)"/>'

        '<path d="M53 103C54 76 65 61 80 61'
        'C95 61 106 76 107 103Z" '
        'fill="rgba(16,175,192,0.13)"/>'

        '<path d="M25 101C26 82 35 70 47 70'
        'C55 70 62 75 66 84" '
        'fill="rgba(16,175,192,0.09)"/>'

        '<path d="M94 84C98 75 105 70 113 70'
        'C125 70 134 82 135 101" '
        'fill="rgba(16,175,192,0.09)"/>'

        "</svg>"
        "</div>"
    )


def render_product_graphic() -> str:
    """Return the decorative product wave graphic."""

    return (
        '<div style="'
        "position:absolute;"
        "right:-0.2rem;"
        "bottom:0;"
        "width:62%;"
        "height:42%;"
        "opacity:0.72;"
        "pointer-events:none;"
        '">'

        '<svg width="100%" height="100%" '
        'viewBox="0 0 360 150" '
        'preserveAspectRatio="none" '
        'fill="none" '
        'xmlns="http://www.w3.org/2000/svg">'

        '<path d="M0 145C55 128 72 134 110 116'
        'C155 95 177 104 211 83'
        'C252 58 281 69 360 18" '
        'stroke="rgba(91,224,235,0.50)" '
        'stroke-width="2"/>'

        '<path d="M0 150C55 138 80 140 118 126'
        'C157 111 184 112 218 95'
        'C260 74 292 82 360 38" '
        'stroke="rgba(255,255,255,0.30)" '
        'stroke-width="1.5"/>'

        '<path d="M30 150C77 143 100 145 137 133'
        'C175 121 202 121 238 105'
        'C279 87 310 91 360 58" '
        'stroke="rgba(91,224,235,0.26)" '
        'stroke-width="1.2"/>'

        "</svg>"
        "</div>"
    )


def render_region_graphic() -> str:
    """Return the decorative regional trend graphic."""

    return (
        '<div style="'
        "position:absolute;"
        "right:0.8rem;"
        "bottom:0.2rem;"
        "width:66%;"
        "height:35%;"
        "opacity:0.72;"
        "pointer-events:none;"
        '">'

        '<svg width="100%" height="100%" '
        'viewBox="0 0 420 130" '
        'fill="none" '
        'xmlns="http://www.w3.org/2000/svg">'

        '<path d="M10 105C42 88 55 101 78 89'
        'C101 77 113 93 137 81'
        'C164 68 180 88 205 73'
        'C230 59 249 78 272 62'
        'C298 44 315 63 337 51'
        'C360 38 378 56 407 37" '
        'stroke="rgba(16,175,192,0.82)" '
        'stroke-width="1.8" '
        'stroke-dasharray="3 5"/>'

        '<circle cx="78" cy="89" r="3" fill="#10AFC0"/>'
        '<circle cx="137" cy="81" r="3" fill="#10AFC0"/>'
        '<circle cx="205" cy="73" r="3" fill="#10AFC0"/>'
        '<circle cx="272" cy="62" r="3" fill="#10AFC0"/>'
        '<circle cx="337" cy="51" r="3" fill="#10AFC0"/>'

        "</svg>"
        "</div>"
    )


def render_pricing_graphic() -> str:
    """Return the decorative pricing chart."""

    bars = (
        '<rect x="8" y="88" width="10" height="8" rx="2" '
        'fill="rgba(16,175,192,0.10)"/>'
        '<rect x="25" y="82" width="10" height="14" rx="2" '
        'fill="rgba(16,175,192,0.12)"/>'
        '<rect x="42" y="76" width="10" height="20" rx="2" '
        'fill="rgba(16,175,192,0.15)"/>'
        '<rect x="59" y="79" width="10" height="17" rx="2" '
        'fill="rgba(16,175,192,0.17)"/>'
        '<rect x="76" y="67" width="10" height="29" rx="2" '
        'fill="rgba(16,175,192,0.20)"/>'
        '<rect x="93" y="57" width="10" height="39" rx="2" '
        'fill="rgba(16,175,192,0.23)"/>'
        '<rect x="110" y="45" width="10" height="51" rx="2" '
        'fill="rgba(16,175,192,0.27)"/>'
        '<rect x="127" y="29" width="10" height="67" rx="2" '
        'fill="rgba(16,175,192,0.31)"/>'
    )

    return (
        '<div style="'
        "position:absolute;"
        "right:0.8rem;"
        "bottom:0.45rem;"
        "width:145px;"
        "height:100px;"
        "opacity:0.9;"
        "pointer-events:none;"
        '">'

        '<svg width="145" height="100" '
        'viewBox="0 0 145 100" '
        'fill="none" '
        'xmlns="http://www.w3.org/2000/svg">'

        f"{bars}"

        "</svg>"
        "</div>"
    )


def render_sales_graphic() -> str:
    """Return the decorative sales growth graphic."""

    return (
        '<div style="'
        "position:absolute;"
        "right:0;"
        "bottom:0;"
        "width:62%;"
        "height:62%;"
        "pointer-events:none;"
        '">'

        '<svg width="100%" height="100%" '
        'viewBox="0 0 500 300" '
        'preserveAspectRatio="none" '
        'fill="none" '
        'xmlns="http://www.w3.org/2000/svg">'

        '<defs>'
        '<linearGradient id="salesFill" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0%" stop-color="#10AFC0" stop-opacity="0.25"/>'
        '<stop offset="100%" stop-color="#10AFC0" stop-opacity="0"/>'
        "</linearGradient>"
        "</defs>"

        '<path d="M0 300C50 270 80 288 120 258'
        'C160 228 180 245 220 207'
        'C258 170 286 188 320 150'
        'C358 108 385 135 414 87'
        'C445 45 470 65 500 18L500 300Z" '
        'fill="url(#salesFill)"/>'

        '<path d="M0 270C50 240 80 258 120 228'
        'C160 198 180 215 220 177'
        'C258 140 286 158 320 120'
        'C358 78 385 105 414 57'
        'C445 15 470 35 500 0" '
        'stroke="#10AFC0" stroke-width="2.8" fill="none"/>'

        '<circle cx="414" cy="57" r="4" fill="#10AFC0"/>'
        '<circle cx="500" cy="0" r="6" fill="#10AFC0"/>'

        "</svg>"
        "</div>"
    )


# ============================================================
# BENTO GRID
# ============================================================


def render_bento_cards() -> None:
    """Render the six core intelligence modules."""

    cards_html = (
        '<style>'
        '.aq-home-grid {'
        'display:grid;'
        'grid-template-columns:repeat(3,minmax(0,1fr));'
        'grid-template-rows:240px 240px;'
        'gap:18px;'
        'margin-bottom:3rem;'
        'width:100%;'
        '}'
        '.aq-home-link {'
        'display:block;'
        'height:100%;'
        'min-height:0;'
        'text-decoration:none;'
        'color:inherit;'
        '}'
        '.aq-home-card {'
        'box-sizing:border-box;'
        'height:100%;'
        'min-height:0;'
        '}'
        '@media (max-width:900px) {'
        '.aq-home-grid {'
        'grid-template-columns:1fr;'
        'grid-template-rows:auto;'
        '}'
        '.aq-home-link { min-height:240px; }'
        '}'
        '</style>'

        '<div class="aq-home-grid">'

        # SALES
        '<a href="?page=sales" target="_self" class="aq-home-link aq-module-link">'
        '<div class="aq-home-card" style="position:relative;overflow:hidden;'
        'padding:1.65rem;border-radius:20px;'
        f'background:{DEEP_OCEAN};'
        'box-shadow:0 16px 40px rgba(6,59,73,0.14);">'
        '<div style="position:relative;z-index:3;padding-right:72px;">'
        f'<div style="color:{AQUA};font-size:0.68rem;font-weight:800;letter-spacing:0.17em;text-transform:uppercase;margin-bottom:1.8rem;">Revenue</div>'
        '<div style="color:white;font-size:1.48rem;font-weight:800;letter-spacing:-0.035em;line-height:1.15;margin-bottom:0.9rem;">Sales<br>Performance</div>'
        '<div style="max-width:300px;color:rgba(255,255,255,0.78);font-size:0.94rem;line-height:1.55;">Track revenue, sales velocity and the factors driving business performance.</div>'
        '</div>'
        '<div style="position:absolute;top:1.55rem;right:1.55rem;width:52px;height:52px;display:flex;align-items:center;justify-content:center;border-radius:15px;background:rgba(255,255,255,0.11);z-index:4;">'
        f'{render_sales_icon()}'
        '</div>'
        f'{render_sales_graphic()}'
        '<div style="position:absolute;width:280px;height:280px;right:-110px;bottom:-180px;border:1px solid rgba(255,255,255,0.14);border-radius:50%;pointer-events:none;"></div>'
        '</div></a>'

        # CUSTOMERS
        '<a href="?page=customers" target="_self" class="aq-home-link aq-module-link">'
        '<div class="aq-home-card" style="position:relative;overflow:hidden;padding:1.65rem;border-radius:20px;background:#FFFFFF;border:1px solid rgba(13,61,75,0.06);box-shadow:0 12px 30px rgba(6,59,73,0.07);">'
        '<div style="position:relative;z-index:3;padding-right:72px;">'
        f'<div style="color:{AQUA};font-size:0.68rem;font-weight:800;letter-spacing:0.17em;text-transform:uppercase;margin-bottom:1.8rem;">Customers</div>'
        f'<div style="color:{SURFACE_DARK};font-size:1.48rem;font-weight:800;letter-spacing:-0.035em;line-height:1.15;margin-bottom:0.9rem;">Customer<br>Intelligence</div>'
        '<div style="max-width:290px;color:#527080;font-size:0.94rem;line-height:1.55;">Understand customer value, retention and buying behaviour.</div>'
        '</div>'
        '<div style="position:absolute;top:1.55rem;right:1.55rem;width:52px;height:52px;display:flex;align-items:center;justify-content:center;border-radius:15px;background:rgba(16,175,192,0.08);z-index:4;">'
        f'{render_customer_icon()}'
        '</div>'
        f'{render_customer_graphic()}'
        '</div></a>'

        # PRODUCTS
        '<a href="?page=products" target="_self" class="aq-home-link aq-module-link">'
        '<div class="aq-home-card" style="position:relative;overflow:hidden;padding:1.65rem;border-radius:20px;'
        f'background:{OCEAN};'
        'box-shadow:0 12px 30px rgba(6,59,73,0.12);">'
        '<div style="position:relative;z-index:3;padding-right:72px;">'
        '<div style="color:white;font-size:0.68rem;font-weight:800;letter-spacing:0.17em;text-transform:uppercase;margin-bottom:1.8rem;">Products</div>'
        '<div style="color:white;font-size:1.48rem;font-weight:800;letter-spacing:-0.035em;line-height:1.15;margin-bottom:0.9rem;">Product<br>Performance</div>'
        '<div style="max-width:300px;color:rgba(255,255,255,0.78);font-size:0.94rem;line-height:1.55;">Identify products that create growth and products that need attention.</div>'
        '</div>'
        '<div style="position:absolute;top:1.55rem;right:1.55rem;width:52px;height:52px;display:flex;align-items:center;justify-content:center;border-radius:15px;background:rgba(255,255,255,0.11);z-index:4;">'
        f'{render_product_icon()}'
        '</div>'
        f'{render_product_graphic()}'
        '</div></a>'

        # REGIONS
        '<a href="?page=regions" target="_self" class="aq-home-link aq-module-link">'
        '<div class="aq-home-card" style="position:relative;overflow:hidden;padding:1.65rem;border-radius:20px;'
        f'background:{OCEAN};'
        'box-shadow:0 12px 30px rgba(6,59,73,0.12);">'
        '<div style="position:relative;z-index:3;padding-right:72px;">'
        '<div style="color:white;font-size:0.68rem;font-weight:800;letter-spacing:0.17em;text-transform:uppercase;margin-bottom:1.8rem;">Regions</div>'
        '<div style="color:white;font-size:1.48rem;font-weight:800;letter-spacing:-0.035em;line-height:1.15;margin-bottom:0.9rem;">Regional<br>Intelligence</div>'
        '<div style="max-width:300px;color:rgba(255,255,255,0.78);font-size:0.94rem;line-height:1.55;">Compare territories and uncover where demand is strongest.</div>'
        '</div>'
        '<div style="position:absolute;top:1.55rem;right:1.55rem;width:52px;height:52px;display:flex;align-items:center;justify-content:center;border-radius:15px;background:rgba(255,255,255,0.11);z-index:4;">'
        f'{render_region_icon()}'
        '</div>'
        f'{render_region_graphic()}'
        '</div></a>'

        # PRICING
        '<a href="?page=pricing" target="_self" class="aq-home-link aq-module-link">'
        '<div class="aq-home-card" style="position:relative;overflow:hidden;padding:1.65rem;border-radius:20px;background:#FFFFFF;border:1px solid rgba(13,61,75,0.06);box-shadow:0 12px 30px rgba(6,59,73,0.07);">'
        '<div style="position:relative;z-index:3;padding-right:72px;">'
        f'<div style="color:{AQUA};font-size:0.68rem;font-weight:800;letter-spacing:0.17em;text-transform:uppercase;margin-bottom:1.8rem;">Pricing</div>'
        f'<div style="color:{SURFACE_DARK};font-size:1.48rem;font-weight:800;letter-spacing:-0.035em;line-height:1.15;margin-bottom:0.9rem;">Pricing<br>Intelligence</div>'
        '<div style="max-width:280px;color:#527080;font-size:0.94rem;line-height:1.55;">Measure discounts, price effectiveness and revenue impact.</div>'
        '</div>'
        '<div style="position:absolute;top:1.55rem;right:1.55rem;width:52px;height:52px;display:flex;align-items:center;justify-content:center;border-radius:15px;background:rgba(16,175,192,0.08);z-index:4;">'
        f'{render_pricing_icon()}'
        '</div>'
        f'{render_pricing_graphic()}'
        '</div></a>'

        # FORECAST
        '<a href="?page=forecast" target="_self" class="aq-home-link aq-module-link">'
        '<div class="aq-home-card" style="position:relative;overflow:hidden;padding:1.65rem;border-radius:20px;'
        f'background:{DEEP_OCEAN};'
        'box-shadow:0 12px 30px rgba(6,59,73,0.12);">'
        '<div style="position:relative;z-index:3;padding-right:72px;">'
        f'<div style="color:{AQUA};font-size:0.68rem;font-weight:800;letter-spacing:0.17em;text-transform:uppercase;margin-bottom:1.8rem;">Forecast</div>'
        '<div style="color:white;font-size:1.48rem;font-weight:800;letter-spacing:-0.035em;line-height:1.15;margin-bottom:0.9rem;">Revenue<br>Forecast</div>'
        '<div style="max-width:300px;color:rgba(255,255,255,0.78);font-size:0.94rem;line-height:1.55;">Look ahead with projected revenue, demand and business trends.</div>'
        '</div>'
        '<div style="position:absolute;top:1.55rem;right:1.55rem;width:52px;height:52px;display:flex;align-items:center;justify-content:center;border-radius:15px;background:rgba(255,255,255,0.11);z-index:4;">'
        '<svg width="27" height="27" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">'
        f'<path d="M4 18L9 13L13 16L20 7" stroke="{AQUA}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
        f'<path d="M16 7H20V11" stroke="{AQUA}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
        '</svg>'
        '</div>'
        '<div style="position:absolute;right:1.5rem;bottom:1.35rem;width:62%;height:64px;opacity:0.8;">'
        f'<svg width="100%" height="100%" viewBox="0 0 260 70" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">'
        f'<path d="M0 58 C28 55, 42 45, 62 48 S96 36, 116 39 S148 25, 168 30 S201 13, 220 19 S245 8, 260 4" stroke="{AQUA}" stroke-width="2.2" fill="none"/>'
        '<path d="M0 60 C28 57, 42 47, 62 50 S96 38, 116 41 S148 27, 168 32 S201 15, 220 21 S245 10, 260 6" stroke="rgba(255,255,255,0.18)" stroke-width="1" fill="none"/>'
        '</svg></div>'
        '</div></a>'

        '</div>'
    )

    st.markdown(cards_html, unsafe_allow_html=True)


# ============================================================
# DATA UPLOAD
# ============================================================


def _format_upload_number(value: int | float) -> str:
    """Format upload statistics."""

    return f"{value:,.0f}"


def _format_upload_size(size_bytes: int) -> str:
    """Format file size."""

    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"

    return f"{size_bytes / (1024 * 1024):.2f} MB"


def _get_file_hash(uploaded_file: Any) -> str:
    """Calculate SHA-256 for the selected file."""

    sha = hashlib.sha256()
    uploaded_file.seek(0)

    while chunk := uploaded_file.read(8192):
        sha.update(chunk)

    uploaded_file.seek(0)
    return sha.hexdigest()


def _save_temp_upload(uploaded_file: Any) -> Path:
    """Save the selected Streamlit file temporarily."""

    suffix = Path(uploaded_file.name).suffix or ".xlsx"

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temporary_file:
        temporary_file.write(uploaded_file.getvalue())
        return Path(temporary_file.name)


def _preview_upload(file_path: Path) -> dict[str, Any]:
    """Analyze an uploaded Excel file without modifying the database."""

    try:
        temp = pd.read_excel(file_path, header=None)
        header_row: int | None = None

        for row_index, (_, row) in enumerate(temp.iterrows()):
            values = [str(value).strip() for value in row.tolist()]
            if "Item Code" in values:
                header_row = row_index
                break

        if header_row is None:
            return {"success": False, "message": "Could not find the ERP header row."}

        df = pd.read_excel(file_path, header=header_row)
        df = df.dropna(how="all")
        df.columns = df.columns.astype(str).str.strip()

        valid, validation_report = validate_data(df, header_row)
        if not valid:
            return {
                "success": False,
                "message": "The uploaded file contains validation errors.",
                "validation_report": validation_report,
            }

        clean_df, cleaning_report, data_quality_summary, report_path = preprocess_data(df)

        return {
            "success": True,
            "rows_read": len(df),
            "clean_df": clean_df,
            "rows_after_preprocessing": len(clean_df),
            "rows_removed": len(df) - len(clean_df),
            "cleaning_report": cleaning_report,
            "data_quality_summary": data_quality_summary,
            "report_path": report_path,
        }

    except Exception as exc:
        return {"success": False, "message": str(exc)}


def _get_existing_record_count(clean_df: pd.DataFrame) -> tuple[int, int]:
    """Compare uploaded records against existing database records."""

    conn = get_connection()

    try:
        cursor = conn.cursor()
        existing_counts = _load_existing_record_counts(cursor)
        existing_records = 0

        for _, row in clean_df.iterrows():
            business_key = _incoming_business_key(row)
            if existing_counts[business_key] > 0:
                existing_counts[business_key] -= 1
                existing_records += 1

        return existing_records, len(clean_df) - existing_records

    finally:
        conn.close()


def _clear_upload_state() -> None:
    """Clear temporary upload preview state."""

    st.session_state.pop("home_upload_preview", None)
    st.session_state.pop("home_upload_preview_key", None)
    st.session_state.pop("home_upload_hash", None)


def render_data_upload() -> None:
    """Render the data overview and upload workflow as one unified panel."""

    st.markdown(
        dedent(
            """
            <style>
            /* =====================================================
               AQVASTAR DATA OVERVIEW
               ===================================================== */

            .st-key-aq_upload_panel {
                margin: 0.4rem 0 2.8rem 0;
                padding: 1.55rem 1.55rem 1.4rem 1.55rem;
                border: 1px solid #CFE7EA !important;
                border-radius: 24px !important;
                background:
                    radial-gradient(
                        circle at 92% 0%,
                        rgba(16, 175, 192, 0.07),
                        transparent 28%
                    ),
                    linear-gradient(
                        135deg,
                        #F5FBFC 0%,
                        #F8FCFD 55%,
                        #F1FAFB 100%
                    ) !important;
                box-shadow: 0 18px 45px rgba(6, 59, 73, 0.08);
            }

            .aq-upload-eyebrow {
                color: #0C9CAE;
                font-size: 0.64rem;
                font-weight: 850;
                letter-spacing: 0.16em;
                text-transform: uppercase;
                margin-bottom: 0.42rem;
            }

            .aq-upload-heading {
                color: #063B49;
                font-size: clamp(1.55rem, 2.3vw, 2.05rem);
                font-weight: 850;
                letter-spacing: -0.045em;
                line-height: 1.08;
                margin: 0 0 0.38rem 0;
            }

            .aq-upload-subheading {
                color: #527080;
                font-size: 0.82rem;
                line-height: 1.5;
                margin: 0 0 1.05rem 0;
            }

            /* Small metric boxes inside the main panel. */
            .aq-upload-stat {
                min-height: 105px;
                box-sizing: border-box;
                padding: 1rem 1.05rem;
                border-radius: 16px;
                border: 1px solid #D7EAED;
                background: rgba(255, 255, 255, 0.72);
                box-shadow: 0 5px 18px rgba(6, 59, 73, 0.035);
            }

            .aq-upload-stat:nth-child(1) {
                background: linear-gradient(
                    135deg,
                    #F0FBF8 0%,
                    #F8FCFC 100%
                );
            }

            .aq-upload-stat-label {
                color: #607782;
                font-size: 0.59rem;
                font-weight: 850;
                letter-spacing: 0.105em;
                text-transform: uppercase;
                margin-bottom: 0.38rem;
            }

            .aq-upload-stat-value {
                color: #063B49;
                font-size: 1.42rem;
                font-weight: 850;
                letter-spacing: -0.035em;
                line-height: 1.05;
                white-space: nowrap;
            }

            .aq-upload-stat-note {
                color: #6B818A;
                font-size: 0.67rem;
                margin-top: 0.36rem;
            }

            /* =====================================================
               CLEAN UPLOAD ROW
               Keep Streamlit's native horizontal columns.
               Only control vertical centering and spacing.
               ===================================================== */

            .aq-upload-zone {
                margin-top: 0.85rem;
                min-height: 72px;
                box-sizing: border-box;
            }

            .aq-upload-zone-title {
                color: #063B49;
                font-size: 0.98rem;
                font-weight: 850;
                letter-spacing: -0.025em;
                line-height: 1.2;
                margin: 0 0 0.28rem 0;
            }

            .aq-upload-zone-text {
                color: #607782;
                font-size: 0.70rem;
                line-height: 1.35;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
                margin: 0;
            }

            .aq-upload-icon {
                width: 48px;
                height: 48px;
                border-radius: 14px;
                display: flex;
                align-items: center;
                justify-content: center;
                background: #E7F8FA;
                border: 1px solid #CBECEF;
                box-sizing: border-box;
                margin: 0 auto;
            }

            .aq-upload-icon svg {
                width: 25px;
                height: 25px;
                display: block;
            }

            /* One horizontal row. Do NOT turn this into CSS grid. */
            /* Grid, not flex: column widths are fixed by the
               PARENT's grid-template-columns, not by each
               column's own flex-basis. Streamlit re-asserts an
               inline !important flex-basis/width on the column
               divs on every layout pass, which beats an external
               !important flex rule on those same divs. It has no
               such claim on the container's grid tracks, so this
               is what actually holds the layout in place. The
               inter-column spacing lives here too, as column-gap
               — Streamlit also forces padding: 0 !important
               inline on the column divs, which silently ate any
               spacing set via their padding. */
            .st-key-aq_upload_zone [data-testid="stHorizontalBlock"] {
                display: grid !important;
                grid-template-columns: 48px minmax(0, 1fr) auto !important;
                align-items: center !important;
                width: 100% !important;
                min-height: 92px !important;
                column-gap: 0.75rem !important;
                row-gap: 0 !important;
            }

            .st-key-aq_upload_zone [data-testid="column"] {
                display: flex !important;
                align-items: center !important;
                min-height: 72px !important;
                height: auto !important;
                padding: 0 !important;
                margin: 0 !important;
                box-sizing: border-box !important;
            }

            .st-key-aq_upload_zone [data-testid="column"] > div {
                width: 100% !important;
                display: flex !important;
                align-items: center !important;
                min-height: 72px !important;
                margin: 0 !important;
                padding: 0 !important;
                box-sizing: border-box !important;
            }

            /* Per-column spacing now comes entirely from the
               container's column-gap above, not from padding on
               these divs — Streamlit forces padding: 0 !important
               inline on them, which ate any gap set here before.
               justify-content still controls how each cell's own
               content sits inside its track. */
            .st-key-aq_upload_zone [data-testid="column"]:nth-child(1) {
                justify-content: center !important;
                flex: 0 0 48px !important;
                width: 48px !important;
            }

            .st-key-aq_upload_zone [data-testid="column"]:nth-child(2) {
                justify-content: flex-start !important;
                flex: 1 1 auto !important;
                width: auto !important;
                min-width: 0 !important;
            }

            /* Right side (3rd column) - Updated for perfect vertical alignment */
            .st-key-aq_upload_zone [data-testid="column"]:nth-child(3) {
                justify-content: center !important;
                align-items: center !important;
                display: flex !important;
                flex-direction: column !important;
                flex: 0 0 auto !important;
                width: auto !important;
                height: 100% !important;
            }

            /* Center the vertical block and prevent it from stretching */
            .st-key-aq_upload_zone [data-testid="column"]:nth-child(3) [data-testid="stVerticalBlock"] {
                display: flex !important;
                flex-direction: column !important;
                align-items: center !important;
                justify-content: center !important;
                gap: 0.4rem !important;
                width: auto !important;
                height: auto !important; /* Changed to auto to prevent stretching */
            }

            /* Remove Streamlit's default element margins to fix the "too high / too low" gap */
            .st-key-aq_upload_zone [data-testid="column"]:nth-child(3) [data-testid="stVerticalBlock"] > div {
                margin: 0 !important;
                padding: 0 !important;
            }

            .aq-upload-copy {
                width: 100%;
                display: flex;
                flex-direction: column;
                justify-content: center;
                margin: 0 !important;
            }

            .aq-upload-helper-wrap {
                width: auto;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0 !important;
                padding: 0 !important;
            }

            .aq-upload-helper {
                color: #71858D;
                font-size: 0.64rem;
                line-height: 1.35;
                margin: 0 !important;
                text-align: center;
                white-space: nowrap;
            }

            .st-key-aq_upload_zone .stMarkdown,
            .st-key-aq_upload_zone .stMarkdown > div {
                width: 100% !important;
                margin: 0 !important;
                padding: 0 !important;
            }

            /* =====================================================
               STREAMLIT UPLOADER
               ===================================================== */


               Compact, clean and teal. The native dark button is
               explicitly overridden across Streamlit button variants.
               ===================================================== */

            .st-key-aq_upload_zone div[data-testid="stFileUploader"] {
                width: 100% !important;
                margin: 0 !important;
                padding: 0 !important;
            }

            .st-key-aq_upload_zone div[data-testid="stFileUploader"] section {
                width: 100% !important;
                min-height: 52px !important;
                height: 52px !important;
                margin: 0 !important;
                padding: 0 !important;
                border: 0 !important;
                background: transparent !important;
                box-shadow: none !important;
            }

            .st-key-aq_upload_zone div[data-testid="stFileUploaderDropzone"] {
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                width: 100% !important;
                min-height: 52px !important;
                height: 52px !important;
                box-sizing: border-box !important;
                padding: 0 !important;
                border: 0 !important;
                border-radius: 0 !important;
                background: transparent !important;
                box-shadow: none !important;
            }

            .st-key-aq_upload_zone div[data-testid="stFileUploaderDropzone"] > div {
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                width: 100% !important;
                background: transparent !important;
            }

            /* Remove the native instructional text. */
            .st-key-aq_upload_zone
            div[data-testid="stFileUploaderDropzoneInstructions"],
            .st-key-aq_upload_zone
            div[data-testid="stFileUploaderDropzone"] small,
            .st-key-aq_upload_zone
            div[data-testid="stFileUploaderDropzone"] label {
                display: none !important;
            }

            /* Robustly target Streamlit's native Browse/Upload button. */
            .st-key-aq_upload_zone div[data-testid="stFileUploader"] button,
            .st-key-aq_upload_zone div[data-testid="stFileUploaderDropzone"] button,
            .st-key-aq_upload_zone button[data-testid="stBaseButton-secondary"],
            .st-key-aq_upload_zone button[kind="secondary"] {
                position: static !important;
                transform: none !important;
                display: inline-flex !important;
                align-items: center !important;
                justify-content: center !important;
                min-width: 145px !important;
                width: 145px !important;
                height: 42px !important;
                min-height: 42px !important;
                margin: 0 !important;
                padding: 0 1rem !important;
                border-radius: 10px !important;
                border: 1px solid #10AFC0 !important;
                background: #10AFC0 !important;
                background-color: #10AFC0 !important;
                color: #FFFFFF !important;
                font-size: 0.78rem !important;
                font-weight: 800 !important;
                line-height: 1 !important;
                box-shadow: 0 6px 16px rgba(16, 175, 192, 0.16) !important;
                opacity: 1 !important;
            }

            .st-key-aq_upload_zone div[data-testid="stFileUploader"] button:hover,
            .st-key-aq_upload_zone div[data-testid="stFileUploaderDropzone"] button:hover,
            .st-key-aq_upload_zone button[data-testid="stBaseButton-secondary"]:hover {
                background: #0B98A8 !important;
                background-color: #0B98A8 !important;
                border-color: #0B98A8 !important;
                color: #FFFFFF !important;
            }

            .st-key-aq_upload_zone div[data-testid="stFileUploader"] button *,
            .st-key-aq_upload_zone div[data-testid="stFileUploaderDropzone"] button *,
            .st-key-aq_upload_zone button[data-testid="stBaseButton-secondary"] * {
                color: #FFFFFF !important;
                fill: none !important;
                stroke: #FFFFFF !important;
            }

            .st-key-aq_upload_zone
            div[data-testid="stFileUploader"] button svg,
            .st-key-aq_upload_zone
            div[data-testid="stFileUploaderDropzone"] button svg {
                color: #FFFFFF !important;
                fill: none !important;
                stroke: #FFFFFF !important;
            }

            .aq-upload-helper {
                color: #71858D;
                font-size: 0.64rem;
                line-height: 1.35;
                margin: 0 !important;
                text-align: center;
                white-space: nowrap;
            }

            /* Unified inner upload card. */
            .st-key-aq_upload_zone {
                margin-top: 0.85rem;
                padding: 0.45rem 0.85rem !important;
                border: 1.5px dashed #9DDDE3 !important;
                border-radius: 16px !important;
                background: rgba(255, 255, 255, 0.62) !important;
                box-shadow: none !important;
                box-sizing: border-box !important;
            }

            @media (max-width: 900px) {
                .st-key-aq_upload_zone {
                    padding: 0.65rem 0.8rem !important;
                }

                .st-key-aq_upload_zone [data-testid="stHorizontalBlock"] {
                    display: flex !important;
                    flex-wrap: wrap !important;
                    align-items: center !important;
                    gap: 0.5rem !important;
                }

                .st-key-aq_upload_zone [data-testid="column"] {
                    height: auto !important;
                    min-height: 54px !important;
                }

                .st-key-aq_upload_zone [data-testid="column"] > div {
                    min-height: 54px !important;
                }

                .aq-upload-icon-wrap,
                .aq-upload-copy,
                .aq-upload-helper-wrap {
                    height: auto;
                    min-height: 54px;
                }

                .aq-upload-helper-wrap {
                    border-left: 0;
                    padding-left: 0;
                }

                .aq-upload-zone-text,
                .aq-upload-helper {
                    white-space: normal;
                }

                .st-key-aq_upload_zone div[data-testid="stFileUploader"] button,
                .st-key-aq_upload_zone div[data-testid="stFileUploaderDropzone"] button {
                    min-width: 125px !important;
                    width: 125px !important;
                }
            }

            /* Uploaded file row. */
            .aq-upload-file {
                margin-top: 0.75rem;
                padding: 0.72rem 0.9rem;
                border-radius: 13px;
                background: #EFFBFC;
                border: 1px solid #D8F0F2;
            }

            .aq-upload-file-name {
                color: #063B49;
                font-size: 0.82rem;
                font-weight: 800;
            }

            .aq-upload-file-meta {
                color: #607782;
                font-size: 0.67rem;
                margin-top: 0.18rem;
            }

            .aq-upload-analysis-title,
            .aq-upload-history-title {
                color: #063B49;
                font-size: 0.70rem;
                font-weight: 850;
                letter-spacing: 0.105em;
                text-transform: uppercase;
                margin: 1rem 0 0.45rem;
            }

            .aq-upload-analysis-card {
                padding: 0.72rem 0.9rem;
                border: 1px solid #D5E4E7;
                border-radius: 13px;
                background: #FFFFFF;
            }

            .aq-upload-analysis-label {
                color: #607782;
                font-size: 0.59rem;
                font-weight: 850;
                letter-spacing: 0.08em;
                text-transform: uppercase;
            }

            .aq-upload-analysis-value {
                color: #063B49;
                font-size: 1.15rem;
                font-weight: 850;
                margin-top: 0.18rem;
            }

            /* Keep Streamlit messages visually aligned with the panel. */
            .st-key-aq_upload_panel .stAlert {
                border-radius: 12px !important;
            }

            @media (max-width: 900px) {
                .st-key-aq_upload_panel {
                    padding: 1.1rem;
                }

                .aq-upload-stat {
                    min-height: 92px;
                }

                .aq-upload-zone {
                    padding: 0.85rem;
                }
            }
            </style>
            """
        ),
        unsafe_allow_html=True,
    )

    summary = SalesQueries.get_dataset_summary()
    last_date = str(summary["last_date"]) if summary["last_date"] else "No data"

    # One large container. Every data-management element belongs to it.
    with st.container(border=True, key="aq_upload_panel"):
        st.markdown(
            dedent(
                """
                <div class="aq-upload-eyebrow">Data Overview</div>
                <div class="aq-upload-heading">Keep Your Intelligence Up to Date</div>
                <div class="aq-upload-subheading">
                    Upload the latest sales register to update your business intelligence.
                </div>
                """
            ),
            unsafe_allow_html=True,
        )

        # Three small cards inside the large overview panel.
        stat_columns = st.columns(3, gap="medium")

        stat_items = (
            (
                "Total Records",
                _format_upload_number(summary["total_records"]),
                "Sales records in database",
            ),
            (
                "Total Uploads",
                _format_upload_number(summary["total_uploads"]),
                "Files uploaded so far",
            ),
            (
                "Data Through",
                last_date,
                "Latest data available",
            ),
        )

        for column, (label, value, note) in zip(stat_columns, stat_items):
            with column:
                st.markdown(
                    dedent(
                        f"""
                        <div class="aq-upload-stat">
                            <div class="aq-upload-stat-label">{label}</div>
                            <div class="aq-upload-stat-value">{value}</div>
                            <div class="aq-upload-stat-note">{note}</div>
                        </div>
                        """
                    ),
                    unsafe_allow_html=True,
                )

        # Upload section: a real Streamlit container keeps every
        # element inside the same visual card. This avoids the
        # layout-breaking behavior caused by wrapping Streamlit
        # widgets inside raw HTML divs.
        with st.container(border=False, key="aq_upload_zone"):
            # Changed from 4 columns to 3 columns to match the CSS grid
            upload_columns = st.columns(
                [0.62, 3.05, 3.6],
                gap="small",
            )

            with upload_columns[0]:
                st.markdown(
                    '''
                    <div class="aq-upload-icon">
                        <svg width="25" height="25" viewBox="0 0 24 24"
                             fill="none"
                             xmlns="http://www.w3.org/2000/svg">
                            <path d="M12 16V4"
                                  stroke="#10AFC0"
                                  stroke-width="2"
                                  stroke-linecap="round"/>
                            <path d="M7 9L12 4L17 9"
                                  stroke="#10AFC0"
                                  stroke-width="2"
                                  stroke-linecap="round"
                                  stroke-linejoin="round"/>
                            <path d="M5 14V18.5C5 19.3284 5.67157 20 6.5 20H17.5C18.3284 20 19 19.3284 19 18.5V14"
                                  stroke="#10AFC0"
                                  stroke-width="2"
                                  stroke-linecap="round"/>
                        </svg>
                    </div>
                    ''',
                    unsafe_allow_html=True,
                )

            with upload_columns[1]:
                st.markdown(
                    '''
                    <div class="aq-upload-copy">
                        <div class="aq-upload-zone-title">
                            Add Sales Register
                        </div>
                        <div class="aq-upload-zone-text">
                            Excel files only · XLSX / XLS · Existing records are protected
                        </div>
                    </div>
                    ''',
                    unsafe_allow_html=True,
                )

            with upload_columns[2]:
                uploaded_file = st.file_uploader(
                    "Sales register file",
                    type=["xlsx", "xls"],
                    label_visibility="collapsed",
                    key="home_sales_uploader",
                    help="Upload an Excel sales register.",
                )

                st.markdown(
                    '''
                    <div class="aq-upload-helper-wrap">
                        <div class="aq-upload-helper">
                            Drag and drop your file here or click to browse
                        </div>
                    </div>
                    ''',
                    unsafe_allow_html=True,
                )



        if uploaded_file is None:
            return

        file_hash = _get_file_hash(uploaded_file)

        st.markdown(
            dedent(
                f"""
                <div class="aq-upload-file">
                    <div class="aq-upload-file-name">
                        {uploaded_file.name}
                    </div>
                    <div class="aq-upload-file-meta">
                        {_format_upload_size(uploaded_file.size)}
                        · SHA-256: {file_hash[:16]}...
                    </div>
                </div>
                """
            ),
            unsafe_allow_html=True,
        )

        preview_key = f"home_upload_{file_hash}"

        if st.session_state.get("home_upload_preview_key") != preview_key:
            temporary_path = _save_temp_upload(uploaded_file)

            try:
                with st.spinner("Analyzing your sales data..."):
                    preview = _preview_upload(temporary_path)
            finally:
                try:
                    temporary_path.unlink()
                except OSError:
                    pass

            st.session_state["home_upload_preview_key"] = preview_key
            st.session_state["home_upload_preview"] = preview
            st.session_state["home_upload_hash"] = file_hash

        preview = st.session_state.get("home_upload_preview")

        if not isinstance(preview, dict):
            return

        if not preview.get("success"):
            st.error(
                preview.get(
                    "message",
                    "Unable to analyze the uploaded file.",
                )
            )

            validation_report = preview.get("validation_report", [])

            if validation_report:
                st.dataframe(
                    pd.DataFrame(validation_report),
                    use_container_width=True,
                    hide_index=True,
                )

            return

        clean_df = preview["clean_df"]
        existing_records, new_records = _get_existing_record_count(clean_df)

        st.markdown(
            '<div class="aq-upload-analysis-title">Upload Analysis</div>',
            unsafe_allow_html=True,
        )

        analysis_columns = st.columns(3, gap="small")

        analysis_items = [
            ("Records Found", len(clean_df)),
            ("Already Existing", existing_records),
            ("New Records", new_records),
        ]

        for column, (label, value) in zip(
            analysis_columns,
            analysis_items,
        ):
            with column:
                st.markdown(
                    dedent(
                        f"""
                        <div class="aq-upload-analysis-card">
                            <div class="aq-upload-analysis-label">
                                {label}
                            </div>
                            <div class="aq-upload-analysis-value">
                                {_format_upload_number(value)}
                            </div>
                        </div>
                        """
                    ),
                    unsafe_allow_html=True,
                )

        if new_records == 0:
            st.warning(
                "No new records were found. Your existing data will not be changed."
            )
        elif existing_records > 0:
            st.info(
                f"{existing_records:,} existing records will be skipped and "
                f"{new_records:,} new records will be added."
            )
        else:
            st.success(
                f"All {new_records:,} records are new and ready to add."
            )

        if new_records > 0 and st.button(
            f"ADD {new_records:,} NEW RECORDS",
            type="primary",
            use_container_width=True,
            key="home_confirm_upload",
        ):
            temporary_path = _save_temp_upload(uploaded_file)

            try:
                with st.spinner("Adding new sales records..."):
                    result = upload_excel(temporary_path)
            finally:
                try:
                    temporary_path.unlink()
                except OSError:
                    pass

            if result.get("success"):
                _clear_upload_state()
                st.success(
                    result.get(
                        "message",
                        "Upload completed successfully.",
                    )
                )
                st.rerun()

            elif result.get("stage") == "duplicate_file":
                st.warning(
                    "This exact file has already been uploaded. "
                    "No records were added."
                )

            else:
                st.error(
                    result.get(
                        "message",
                        "The upload could not be completed.",
                    )
                )

        history = SalesQueries.get_upload_history(limit=5)

        if history:
            st.markdown(
                '<div class="aq-upload-history-title">Recent Uploads</div>',
                unsafe_allow_html=True,
            )

            history_df = pd.DataFrame(history).rename(
                columns={
                    "upload_timestamp": "Date",
                    "file_name": "File",
                    "rows_inserted": "New",
                    "rows_skipped": "Existing",
                    "status": "Status",
                }
            )

            history_columns = [
                "Date",
                "File",
                "New",
                "Existing",
                "Status",
            ]

            available_columns = [
                column
                for column in history_columns
                if column in history_df.columns
            ]

            st.dataframe(
                history_df[available_columns],
                use_container_width=True,
                hide_index=True,
            )


# ============================================================
# MAIN
# ============================================================


def main() -> None:
    """Render the AQVASTAR home dashboard."""

    apply_theme("AQVASTAR | Sales Intelligence")

    render_brand()
    render_navigation("home")
    render_hero()
    render_data_upload()
    render_ask_aqvastar()
    render_section_heading()
    render_bento_cards()


if __name__ == "__main__":
    main()
    