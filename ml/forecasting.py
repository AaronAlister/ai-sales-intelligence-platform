
"""Forecast helpers using the existing TimeSeriesEngine."""
from __future__ import annotations

import pandas as pd


def compare_existing_forecasts(
    metric: str = "Revenue",
) -> pd.DataFrame:
    """Compare forecasting methods using existing engine logic."""

    from engines.forecast_engine import TimeSeriesEngine

    engine = TimeSeriesEngine()
    return engine.compare_forecast_methods(metric=metric)


def get_existing_forecast(
    metric: str = "Revenue",
    periods: int = 3,
) -> pd.DataFrame:
    """Generate forecasts using the existing engine."""

    from engines.forecast_engine import TimeSeriesEngine

    engine = TimeSeriesEngine()

    if metric.strip().lower() == "revenue":
        return engine.forecast_revenue(
            periods=periods,
            method="moving_average",
        )

    # The existing forecast_revenue method forecasts revenue only.
    # Other metrics use the engine's generic forecasting method.
    return engine.moving_average_forecast(
        metric=metric,
        periods=periods,
    )