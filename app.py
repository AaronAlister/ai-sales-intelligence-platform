"""AQVASTAR Sales Intelligence Platform application router."""

from __future__ import annotations

import importlib
from collections.abc import Callable
from types import ModuleType
from typing import cast

import streamlit as st


def get_page() -> str:
    """Return the requested dashboard page."""

    page_value = st.query_params.get("page", "home")
    return page_value.lower() if isinstance(page_value, str) else "home"


def load_dashboard(page: str) -> Callable[[], None] | None:
    """Dynamically load a dashboard's main function."""

    dashboard_modules: dict[str, str] = {
        "home": "dashboards.home",
        "sales": "dashboards.sales_performance_dashboard",
        "customers": "dashboards.customer_dashboard",
        "products": "dashboards.product_dashboard",
        "regions": "dashboards.regional_dashboard",
        "pricing": "dashboards.pricing_dashboard",
        "trends": "dashboards.timeseries_dashboard",
        "forecast": "dashboards.forecast_dashboard",
        "ai": "dashboards.ai_dashboard",
    }

    module_name = dashboard_modules.get(page)
    if module_name is None:
        return None

    try:
        module: ModuleType = importlib.import_module(module_name)
    except ModuleNotFoundError:
        return None

    main_function = getattr(module, "main", None)
    if not callable(main_function):
        return None

    return cast(Callable[[], None], main_function)


def render_unavailable_page(page: str) -> None:
    """Render a temporary page for dashboards that do not exist yet."""

    st.markdown(
        f"""
        <div style="margin-top:4rem;padding:3rem;background:#DDF5F7;border:1px solid #D5E4E7;border-radius:20px;text-align:center;">
            <div style="color:#10AFC0;font-size:0.7rem;font-weight:800;letter-spacing:0.16em;text-transform:uppercase;margin-bottom:1rem;">AQVASTAR INTELLIGENCE</div>
            <div style="color:#063B49;font-size:2rem;font-weight:800;letter-spacing:-0.035em;margin-bottom:0.8rem;">{page.title()} Intelligence</div>
            <div style="color:#607782;font-size:1rem;">This dashboard is currently under development.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    """Route the application to the requested dashboard."""

    page = get_page()
    dashboard_main = load_dashboard(page)

    if dashboard_main is not None:
        dashboard_main()
        return

    render_unavailable_page(page)


if __name__ == "__main__":
    main()
