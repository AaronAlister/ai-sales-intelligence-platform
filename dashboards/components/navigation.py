"""
Navigation components for the AQVASTAR Sales Intelligence Platform.
"""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import streamlit as st

from dashboards.components.theme import AQUA, BORDER


def get_project_root() -> Path:
    """Return the project root directory."""

    return Path(__file__).resolve().parents[2]


def get_logo_path() -> Path:
    """Return the absolute path to the AQVASTAR logo."""

    return get_project_root() / "assets" / "aqvastar_logo.png"


def render_brand() -> None:
    """Render the AQVASTAR brand header."""

    logo_path = get_logo_path()

    left_column, right_column = st.columns(
        [4, 1],
        vertical_alignment="center",
    )

    with left_column:
        if logo_path.is_file():
            st.image(
                str(logo_path),
                width=280,
            )
        else:
            st.markdown(
                dedent(
                    """
                    <div style="
                        color: #123B4A;
                        font-size: 1.6rem;
                        font-weight: 800;
                        letter-spacing: -0.03em;
                    ">
                        AQVASTAR
                    </div>
                    """
                ),
                unsafe_allow_html=True,
            )

    with right_column:
        st.markdown(
            dedent(
                f"""
                <div style="
                    display:flex;
                    align-items:center;
                    justify-content:flex-end;
                    gap:8px;
                    color:#123B4A;
                    font-size:0.78rem;
                    font-weight:600;
                    letter-spacing:0.04em;
                    white-space:nowrap;
                ">
                    <span style="
                        width:7px;
                        height:7px;
                        min-width:7px;
                        border-radius:50%;
                        background:{AQUA};
                        display:inline-block;
                    "></span>
                    Intelligence Online
                </div>
                """
            ),
            unsafe_allow_html=True,
        )

    st.markdown(
        dedent(
            f"""
            <div style="
                height:1px;
                background:{BORDER};
                margin-top:1.8rem;
                margin-bottom:1.4rem;
            "></div>
            """
        ),
        unsafe_allow_html=True,
    )


def render_navigation(active_page: str = "home") -> None:
    """
    Render the primary dashboard navigation.

    The active page is rendered as a visibly highlighted pill.
    """

    pages: tuple[tuple[str, str], ...] = (
        ("home", "OVERVIEW"),
        ("sales", "SALES"),
        ("customers", "CUSTOMERS"),
        ("products", "PRODUCTS"),
        ("regions", "REGIONS"),
        ("pricing", "PRICING"),
        ("forecast", "FORECAST"),
    )

    st.markdown(
        dedent(
            """
            <style>
            /* =========================================================
               AQVASTAR PRIMARY NAVIGATION
               ========================================================= */

            /* Keep every navigation cell centered. */
            .st-key-nav_item_home,
            .st-key-nav_item_sales,
            .st-key-nav_item_customers,
            .st-key-nav_item_products,
            .st-key-nav_item_regions,
            .st-key-nav_item_pricing,
            .st-key-nav_item_forecast {
                display: flex !important;
                justify-content: center !important;
                align-items: center !important;
                width: 100% !important;
            }

            /* Inactive navigation buttons. */
            .st-key-nav_item_home button,
            .st-key-nav_item_sales button,
            .st-key-nav_item_customers button,
            .st-key-nav_item_products button,
            .st-key-nav_item_regions button,
            .st-key-nav_item_pricing button,
            .st-key-nav_item_forecast button {
                width: auto !important;
                min-width: 0 !important;
                max-width: max-content !important;
                height: 38px !important;
                min-height: 38px !important;
                padding: 0 0.18rem !important;
                margin: 0 !important;
                border: 1px solid transparent !important;
                border-radius: 999px !important;
                background: transparent !important;
                color: #527080 !important;
                box-shadow: none !important;
                font-size: 0.78rem !important;
                font-weight: 500 !important;
                letter-spacing: 0.075em !important;
                line-height: 1 !important;
                white-space: nowrap !important;
            }

            /* =========================================================
               ACTIVE NAVIGATION

               The active button is deliberately a PRIMARY Streamlit
               button. This avoids relying on Streamlit's generated
               button class names and makes the active state reliable.
               ========================================================= */

            .st-key-nav_item_home button[kind="primary"],
            .st-key-nav_item_sales button[kind="primary"],
            .st-key-nav_item_customers button[kind="primary"],
            .st-key-nav_item_products button[kind="primary"],
            .st-key-nav_item_regions button[kind="primary"],
            .st-key-nav_item_pricing button[kind="primary"],
            .st-key-nav_item_forecast button[kind="primary"] {
                width: auto !important;
                min-width: 0 !important;
                max-width: max-content !important;
                height: 38px !important;
                min-height: 38px !important;
                padding: 0 0.9rem !important;
                margin: 0 !important;

                border: 1px solid #10AFC0 !important;
                border-radius: 999px !important;

                background: #E3F7F9 !important;
                color: #063B49 !important;

                box-shadow:
                    0 4px 12px rgba(6, 59, 73, 0.10) !important;

                font-weight: 750 !important;
                letter-spacing: 0.075em !important;
            }

            .st-key-nav_item_home button[kind="primary"]:hover,
            .st-key-nav_item_sales button[kind="primary"]:hover,
            .st-key-nav_item_customers button[kind="primary"]:hover,
            .st-key-nav_item_products button[kind="primary"]:hover,
            .st-key-nav_item_regions button[kind="primary"]:hover,
            .st-key-nav_item_pricing button[kind="primary"]:hover,
            .st-key-nav_item_forecast button[kind="primary"]:hover {
                border-color: #0B98A8 !important;
                background: #D9F3F5 !important;
                color: #063B49 !important;
            }

            /* Streamlit's button label wrapper. */
            .st-key-nav_item_home button > div,
            .st-key-nav_item_sales button > div,
            .st-key-nav_item_customers button > div,
            .st-key-nav_item_products button > div,
            .st-key-nav_item_regions button > div,
            .st-key-nav_item_pricing button > div,
            .st-key-nav_item_forecast button > div {
                width: auto !important;
                max-width: max-content !important;
                display: inline-flex !important;
                align-items: center !important;
                justify-content: center !important;
                white-space: nowrap !important;
            }

            /* Make the active text itself unmistakable. */
            .st-key-nav_item_home button[kind="primary"] p,
            .st-key-nav_item_sales button[kind="primary"] p,
            .st-key-nav_item_customers button[kind="primary"] p,
            .st-key-nav_item_products button[kind="primary"] p,
            .st-key-nav_item_regions button[kind="primary"] p,
            .st-key-nav_item_pricing button[kind="primary"] p,
            .st-key-nav_item_forecast button[kind="primary"] p {
                color: #063B49 !important;
                font-weight: 750 !important;
            }

            @media (max-width: 900px) {
                .st-key-nav_item_home button,
                .st-key-nav_item_sales button,
                .st-key-nav_item_customers button,
                .st-key-nav_item_products button,
                .st-key-nav_item_regions button,
                .st-key-nav_item_pricing button,
                .st-key-nav_item_forecast button {
                    font-size: 0.68rem !important;
                    letter-spacing: 0.04em !important;
                }

                .st-key-nav_item_home button[kind="primary"],
                .st-key-nav_item_sales button[kind="primary"],
                .st-key-nav_item_customers button[kind="primary"],
                .st-key-nav_item_products button[kind="primary"],
                .st-key-nav_item_regions button[kind="primary"],
                .st-key-nav_item_pricing button[kind="primary"],
                .st-key-nav_item_forecast button[kind="primary"] {
                    padding: 0 0.65rem !important;
                }
            }
            </style>
            """
        ),
        unsafe_allow_html=True,
    )

    columns = st.columns(len(pages), gap="small")

    for column, (page_id, label) in zip(columns, pages):
        with column:
            with st.container(key=f"nav_item_{page_id}"):
                is_active = page_id == active_page

                if st.button(
                    label,
                    key=f"nav_button_{page_id}",
                    type="primary" if is_active else "secondary",
                    use_container_width=False,
                ):
                    st.query_params["page"] = page_id
                    st.rerun()

