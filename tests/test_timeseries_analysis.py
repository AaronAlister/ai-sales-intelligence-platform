import math
from typing import TypedDict

import pandas as pd

from engines.forecast_engine import TimeSeriesEngine


# =========================================================
# TYPE DEFINITIONS
# =========================================================

NumericValue = float | int | str | None


class ForecastReliability(TypedDict):
    """
    Typed structure returned by forecast_reliability().
    """

    metric: str
    method: str
    mape: float
    mae: float
    rmse: float
    backtest_periods: int
    second_best_mape: float
    model_gap: float
    reliability_score: int
    reliability_level: str
    interpretation: str


# =========================================================
# NUMERIC FORMATTING
# =========================================================

def format_currency(
    value: NumericValue,
) -> str:
    """
    Formats monetary values into compact business notation.

    Examples:
        633001.86       -> ₹633.00K
        61829670.42     -> ₹61.83M
        1500000000      -> ₹1.50B

    Already-formatted currency strings are returned unchanged.
    """

    if value is None:
        return "N/A"

    if isinstance(value, str):
        stripped_value = value.strip()

        if stripped_value == "":
            return "N/A"

        if stripped_value.startswith("₹"):
            return stripped_value

        if stripped_value.upper() == "N/A":
            return "N/A"

        try:
            numeric_value = float(
                stripped_value,
            )
        except ValueError:
            return stripped_value

    else:
        numeric_value = float(
            value,
        )

    if math.isnan(numeric_value):
        return "N/A"

    sign = "-" if numeric_value < 0 else ""

    absolute_value = abs(
        numeric_value,
    )

    if absolute_value >= 1_000_000_000:
        return (
            f"{sign}₹"
            f"{absolute_value / 1_000_000_000:.2f}B"
        )

    if absolute_value >= 1_000_000:
        return (
            f"{sign}₹"
            f"{absolute_value / 1_000_000:.2f}M"
        )

    if absolute_value >= 1_000:
        return (
            f"{sign}₹"
            f"{absolute_value / 1_000:.2f}K"
        )

    return (
        f"{sign}₹"
        f"{absolute_value:.2f}"
    )


def format_number(
    value: NumericValue,
) -> str:
    """
    Formats quantities and counts.

    Examples:
        32666.0 -> 32,666
        90443.3 -> 90,443.30
        1810    -> 1,810
    """

    if value is None:
        return "N/A"

    if isinstance(value, str):
        stripped_value = value.strip()

        if stripped_value == "":
            return "N/A"

        if stripped_value.upper() == "N/A":
            return "N/A"

        try:
            numeric_value = float(
                stripped_value,
            )
        except ValueError:
            return stripped_value

    else:
        numeric_value = float(
            value,
        )

    if math.isnan(numeric_value):
        return "N/A"

    if numeric_value.is_integer():
        return f"{int(numeric_value):,}"

    return f"{numeric_value:,.2f}"


def format_percentage(
    value: NumericValue,
) -> str:
    """
    Formats growth percentages with an explicit sign.
    """

    if value is None:
        return "N/A"

    if isinstance(value, str):
        stripped_value = value.strip()

        if stripped_value == "":
            return "N/A"

        if stripped_value.upper() == "N/A":
            return "N/A"

        try:
            numeric_value = float(
                stripped_value.rstrip("%"),
            )
        except ValueError:
            return stripped_value

    else:
        numeric_value = float(
            value,
        )

    if math.isnan(numeric_value):
        return "N/A"

    return f"{numeric_value:+.2f}%"


def format_error_percentage(
    value: NumericValue,
) -> str:
    """
    Formats forecast error percentages.

    Unlike growth percentages, forecast errors do not
    receive a leading '+' sign.
    """

    if value is None:
        return "N/A"

    if isinstance(value, str):
        stripped_value = value.strip()

        if stripped_value == "":
            return "N/A"

        if stripped_value.upper() == "N/A":
            return "N/A"

        try:
            numeric_value = float(
                stripped_value.rstrip("%"),
            )
        except ValueError:
            return stripped_value

    else:
        numeric_value = float(
            value,
        )

    if math.isnan(numeric_value):
        return "N/A"

    return f"{numeric_value:.2f}%"


def format_boolean(
    value: bool | str | None,
) -> str:
    """
    Formats boolean values.
    """

    if value is None:
        return "N/A"

    if isinstance(value, str):
        stripped_value = value.strip()

        if stripped_value.upper() in {
            "YES",
            "TRUE",
        }:
            return "Yes"

        if stripped_value.upper() in {
            "NO",
            "FALSE",
        }:
            return "No"

        return stripped_value

    return "Yes" if value else "No"


# =========================================================
# DATE FORMATTING
# =========================================================

def format_date_column(
    dataframe: pd.DataFrame,
    column: str,
) -> None:
    """
    Formats a date/period column as YYYY-MM-DD.
    """

    if column not in dataframe.columns:
        return

    converted = pd.to_datetime(
        dataframe[column],
        errors="coerce",
    )

    formatted = converted.dt.strftime(
        "%Y-%m-%d",
    )

    dataframe[column] = formatted.fillna(
        "N/A",
    )


# =========================================================
# COLUMN FORMATTERS
# =========================================================

def format_currency_column(
    dataframe: pd.DataFrame,
    column: str,
) -> None:
    """
    Formats a DataFrame column as currency.
    """

    if column not in dataframe.columns:
        return

    values = dataframe[column].tolist()

    dataframe[column] = [
        format_currency(
            value,
        )
        for value in values
    ]


def format_number_column(
    dataframe: pd.DataFrame,
    column: str,
) -> None:
    """
    Formats a DataFrame column as a number.
    """

    if column not in dataframe.columns:
        return

    values = dataframe[column].tolist()

    dataframe[column] = [
        format_number(
            value,
        )
        for value in values
    ]


def format_percentage_column(
    dataframe: pd.DataFrame,
    column: str,
) -> None:
    """
    Formats a DataFrame column as a growth percentage.
    """

    if column not in dataframe.columns:
        return

    values = dataframe[column].tolist()

    dataframe[column] = [
        format_percentage(
            value,
        )
        for value in values
    ]


def format_error_percentage_column(
    dataframe: pd.DataFrame,
    column: str,
) -> None:
    """
    Formats a DataFrame column as a forecast error percentage.
    """

    if column not in dataframe.columns:
        return

    values = dataframe[column].tolist()

    dataframe[column] = [
        format_error_percentage(
            value,
        )
        for value in values
    ]


def format_boolean_column(
    dataframe: pd.DataFrame,
    column: str,
) -> None:
    """
    Formats a DataFrame column as Yes/No.
    """

    if column not in dataframe.columns:
        return

    values = dataframe[column].tolist()

    dataframe[column] = [
        format_boolean(
            value,
        )
        for value in values
    ]


# =========================================================
# DATAFRAME DISPLAY FORMATTING
# =========================================================

def format_timeseries_output(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Creates a presentation-friendly copy of a
    Time-Series DataFrame.

    The original DataFrame is never modified.
    """

    result = dataframe.copy()

    # -----------------------------------------------------
    # DATE COLUMNS
    # -----------------------------------------------------

    date_columns = [
        "Date",
        "Week",
        "Month",
        "Quarter",
        "Year",
    ]

    for column in date_columns:
        format_date_column(
            result,
            column,
        )

    # -----------------------------------------------------
    # CURRENCY COLUMNS
    # -----------------------------------------------------

    currency_columns = [
        "Revenue",
        "Average Order Value",
        "Previous Revenue",
        "Previous Average Order Value",
        "Rolling Revenue",
        "Rolling AOV",
        "Revenue Rolling",
        "AOV Rolling",
        "Rolling Average Order Value",
        "Forecast",
        "Actual",
        "Predicted",
        "Absolute Error",
        "MAE",
        "RMSE",
    ]

    for column in currency_columns:
        format_currency_column(
            result,
            column,
        )

    # -----------------------------------------------------
    # NUMBER COLUMNS
    # -----------------------------------------------------

    number_columns = [
        "Quantity",
        "Orders",
        "Products",
        "Customers",
        "Previous Quantity",
        "Previous Orders",
        "Rolling Quantity",
        "Rolling Orders",
        "Rolling Periods",
        "Backtest Periods",
    ]

    for column in number_columns:
        format_number_column(
            result,
            column,
        )

    # -----------------------------------------------------
    # GROWTH PERCENTAGES
    # -----------------------------------------------------

    percentage_columns = [
        "Revenue Growth %",
        "Quantity Growth %",
        "Order Growth %",
        "AOV Growth %",
        "Growth %",
    ]

    for column in percentage_columns:
        format_percentage_column(
            result,
            column,
        )

    # -----------------------------------------------------
    # FORECAST ERROR PERCENTAGES
    # -----------------------------------------------------

    forecast_percentage_columns = [
        "Percentage Error",
        "MAPE",
    ]

    for column in forecast_percentage_columns:
        format_error_percentage_column(
            result,
            column,
        )

    # -----------------------------------------------------
    # BOOLEAN COLUMNS
    # -----------------------------------------------------

    boolean_columns = [
        "Period Complete",
        "Previous Period Complete",
        "Comparable",
        "Rolling Complete",
    ]

    for column in boolean_columns:
        format_boolean_column(
            result,
            column,
        )

    return result


# =========================================================
# OUTPUT HELPERS
# =========================================================

def print_section(
    title: str,
    dataframe: pd.DataFrame,
    rows: int | None = None,
) -> None:
    """
    Prints a formatted Time-Series DataFrame.
    """

    print()
    print("=" * 78)
    print(title)
    print("=" * 78)

    display_data = dataframe.copy()

    if rows is not None:
        display_data = display_data.head(
            rows,
        )

    formatted = format_timeseries_output(
        display_data,
    )

    print(
        formatted.to_string(
            index=False,
        )
    )


def print_rolling_section(
    title: str,
    dataframe: pd.DataFrame,
    rows: int | None = None,
) -> None:
    """
    Prints a formatted rolling or forecasting DataFrame.
    """

    print()
    print("=" * 78)
    print(title)
    print("=" * 78)

    display_data = dataframe.copy()

    if rows is not None:
        display_data = display_data.head(
            rows,
        )

    formatted = format_timeseries_output(
        display_data,
    )

    print(
        formatted.to_string(
            index=False,
        )
    )


# =========================================================
# FORECAST RELIABILITY DISPLAY
# =========================================================

def print_forecast_reliability(
    reliability: ForecastReliability,
) -> None:
    """
    Prints forecast reliability in a readable
    business-facing format.

    The TypedDict guarantees that Pylance knows
    the type of every field.
    """

    print()
    print("=" * 78)
    print("FORECAST RELIABILITY")
    print("=" * 78)

    print(
        f"Metric:              "
        f"{reliability['metric']}"
    )

    print(
        f"Best Method:         "
        f"{reliability['method']}"
    )

    print(
        f"MAPE:                "
        f"{reliability['mape']:.2f}%"
    )

    print(
        f"MAE:                 "
        f"{format_currency(reliability['mae'])}"
    )

    print(
        f"RMSE:                "
        f"{format_currency(reliability['rmse'])}"
    )

    print(
        f"Backtest Periods:    "
        f"{reliability['backtest_periods']}"
    )

    print(
        f"Model MAPE Gap:      "
        f"{reliability['model_gap']:.2f}%"
    )

    print(
        f"Reliability Score:   "
        f"{reliability['reliability_score']}/100"
    )

    print(
        f"Reliability Level:   "
        f"{reliability['reliability_level']}"
    )

    print(
        "Interpretation:      "
        f"{reliability['interpretation']}"
    )


# =========================================================
# MAIN TEST RUNNER
# =========================================================

def main() -> None:
    """
    Executes all Time-Series Engine analyses.
    """

    engine = TimeSeriesEngine()

    # =====================================================
    # BASIC TIME AGGREGATION
    # =====================================================

    daily = engine.daily_sales()

    print_section(
        "DAILY SALES",
        daily,
        rows=10,
    )

    weekly = engine.weekly_sales()

    print_section(
        "WEEKLY SALES",
        weekly,
        rows=10,
    )

    monthly = engine.monthly_sales()

    print_section(
        "MONTHLY SALES",
        monthly,
    )

    quarterly = engine.quarterly_sales()

    print_section(
        "QUARTERLY SALES",
        quarterly,
    )

    yearly = engine.yearly_sales()

    print_section(
        "YEARLY SALES",
        yearly,
    )

    # =====================================================
    # MONTH-OVER-MONTH
    # =====================================================

    mom = engine.month_over_month_growth()

    print_section(
        "MONTH-OVER-MONTH GROWTH",
        mom,
    )

    # =====================================================
    # QUARTER-OVER-QUARTER
    # =====================================================

    qoq = engine.quarter_over_quarter_growth()

    print_section(
        "QUARTER-OVER-QUARTER GROWTH",
        qoq,
    )

    # =====================================================
    # YEAR-OVER-YEAR
    # =====================================================

    yoy = engine.year_over_year_growth()

    print_section(
        "YEAR-OVER-YEAR GROWTH - VALIDATED",
        yoy,
    )

    # =====================================================
    # MONTHLY YEAR-OVER-YEAR
    # =====================================================

    monthly_yoy = (
        engine.monthly_year_over_year_growth()
    )

    print_section(
        "MONTHLY YEAR-OVER-YEAR GROWTH",
        monthly_yoy,
    )

    # =====================================================
    # REVENUE GROWTH
    # =====================================================

    revenue_growth = (
        engine.revenue_growth_rate(
            frequency="monthly",
        )
    )

    print_section(
        "REVENUE GROWTH RATE - MONTHLY",
        revenue_growth,
    )

    # =====================================================
    # QUANTITY GROWTH
    # =====================================================

    quantity_growth = (
        engine.quantity_growth_rate(
            frequency="monthly",
        )
    )

    print_section(
        "QUANTITY GROWTH RATE - MONTHLY",
        quantity_growth,
    )

    # =====================================================
    # ORDER GROWTH
    # =====================================================

    order_growth = (
        engine.order_growth_rate(
            frequency="monthly",
        )
    )

    print_section(
        "ORDER GROWTH RATE - MONTHLY",
        order_growth,
    )

    # =====================================================
    # AOV GROWTH
    # =====================================================

    aov_growth = (
        engine.aov_growth_rate(
            frequency="monthly",
        )
    )

    print_section(
        "AOV GROWTH - MONTHLY",
        aov_growth,
    )

    # =====================================================
    # TREND ANALYSIS
    # =====================================================

    trend = engine.trend_analysis(
        frequency="monthly",
    )

    print_section(
        "MONTHLY TREND ANALYSIS",
        trend,
    )

    # =====================================================
    # OVERALL BUSINESS TREND
    # =====================================================

    overall_trend = engine.overall_trend(
        frequency="monthly",
    )

    print_section(
        "OVERALL MONTHLY BUSINESS TREND",
        overall_trend,
    )

    # =====================================================
    # SUSTAINED TREND ANALYSIS
    # =====================================================

    sustained_trend = (
        engine.sustained_trend_analysis(
            frequency="monthly",
            window=3,
        )
    )

    print_section(
        "3-PERIOD SUSTAINED TREND ANALYSIS",
        sustained_trend,
    )

    # =====================================================
    # 3-MONTH ROLLING
    # =====================================================

    rolling_3 = engine.rolling_3_month()

    print_rolling_section(
        "3-MONTH ROLLING ANALYSIS",
        rolling_3,
    )

    # =====================================================
    # 6-MONTH ROLLING
    # =====================================================

    rolling_6 = engine.rolling_6_month()

    print_rolling_section(
        "6-MONTH ROLLING ANALYSIS",
        rolling_6,
    )

    # =====================================================
    # 12-MONTH ROLLING
    # =====================================================

    rolling_12 = engine.rolling_12_month()

    print_rolling_section(
        "12-MONTH ROLLING ANALYSIS",
        rolling_12,
    )

    # =====================================================
    # VALID ROLLING WINDOWS
    # =====================================================

    valid_3 = rolling_3[
        rolling_3[
            "Rolling Complete"
        ].astype(bool)
    ].copy()

    valid_6 = rolling_6[
        rolling_6[
            "Rolling Complete"
        ].astype(bool)
    ].copy()

    valid_12 = rolling_12[
        rolling_12[
            "Rolling Complete"
        ].astype(bool)
    ].copy()

    print_rolling_section(
        "VALID 3-MONTH ROLLING WINDOWS",
        valid_3,
        rows=5,
    )

    print_rolling_section(
        "VALID 6-MONTH ROLLING WINDOWS",
        valid_6,
        rows=5,
    )

    print_rolling_section(
        "VALID 12-MONTH ROLLING WINDOWS",
        valid_12,
        rows=5,
    )

    # =====================================================
    # PARTIAL PERIOD CHECK
    # =====================================================

    partial_periods = monthly[
        ~monthly[
            "Period Complete"
        ].astype(bool)
    ].copy()

    print_section(
        "PARTIAL PERIOD CHECK",
        partial_periods,
    )

    # =====================================================
    # SEASONALITY
    # =====================================================

    monthly_seasonality = (
        engine.monthly_seasonality()
    )

    print_section(
        "MONTHLY SEASONALITY",
        monthly_seasonality,
    )

    # =====================================================
    # SEASONALITY SUMMARY
    # =====================================================

    seasonality_summary = (
        engine.seasonality_summary()
    )

    print_section(
        "SEASONALITY SUMMARY",
        seasonality_summary,
    )

    # =====================================================
    # QUARTERLY SEASONALITY
    # =====================================================

    quarterly_seasonality = (
        engine.quarterly_seasonality()
    )

    print_section(
        "QUARTERLY SEASONALITY",
        quarterly_seasonality,
    )

    # =====================================================
    # MOVING AVERAGE FORECAST
    # =====================================================

    revenue_forecast = (
        engine.forecast_revenue(
            periods=3,
            method="moving_average",
            window=3,
        )
    )

    print_rolling_section(
        "3-MONTH REVENUE FORECAST",
        revenue_forecast,
    )

    # =====================================================
    # NAIVE FORECAST
    # =====================================================

    naive_forecast = (
        engine.forecast_revenue(
            periods=3,
            method="naive",
        )
    )

    print_rolling_section(
        "3-MONTH NAIVE REVENUE FORECAST",
        naive_forecast,
    )

    # =====================================================
    # LINEAR TREND FORECAST
    # =====================================================

    trend_forecast = (
        engine.forecast_revenue(
            periods=3,
            method="linear_trend",
        )
    )

    print_rolling_section(
        "3-MONTH LINEAR TREND FORECAST",
        trend_forecast,
    )

    # =====================================================
    # FORECAST BACKTESTING
    # =====================================================

    forecast_backtest = (
        engine.forecast_backtest(
            metric="Revenue",
            method="moving_average",
            window=3,
            min_history=6,
        )
    )

    print()
    print("=" * 78)
    print("FORECAST BACKTEST VALIDATION")
    print("=" * 78)

    print(
        f"Backtest periods: "
        f"{len(forecast_backtest)}"
    )

    if not forecast_backtest.empty:
        first_backtest_month = (
            forecast_backtest[
                "Month"
            ].min()
        )

        last_backtest_month = (
            forecast_backtest[
                "Month"
            ].max()
        )

        print(
            "First backtest month: "
            f"{first_backtest_month}"
        )

        print(
            "Last backtest month: "
            f"{last_backtest_month}"
        )

    print_rolling_section(
        "REVENUE FORECAST BACKTEST",
        forecast_backtest,
    )

    # =====================================================
    # FORECAST ACCURACY
    # =====================================================

    forecast_accuracy = (
        engine.forecast_accuracy(
            metric="Revenue",
            method="moving_average",
            window=3,
            min_history=6,
        )
    )

    print_rolling_section(
        "REVENUE FORECAST ACCURACY",
        forecast_accuracy,
    )

    # =====================================================
    # FORECAST METHOD COMPARISON
    # =====================================================

    forecast_comparison = (
        engine.compare_forecast_methods(
            metric="Revenue",
            window=3,
            min_history=6,
        )
    )

    print_rolling_section(
        "FORECAST METHOD COMPARISON",
        forecast_comparison,
    )

    # =====================================================
    # BEST FORECAST METHOD
    # =====================================================

    best_method = (
        engine.best_forecast_method(
            metric="Revenue",
            window=3,
            min_history=6,
        )
    )

    print()
    print("=" * 78)
    print("BEST FORECAST METHOD")
    print("=" * 78)

    print(
        best_method
    )

    # =====================================================
    # FORECAST RELIABILITY
    # =====================================================

    raw_reliability = (
        engine.forecast_reliability(
            metric="Revenue",
            window=3,
            min_history=6,
        )
    )

    # -----------------------------------------------------
    # Convert the engine result into the strongly typed
    # structure expected by the test display layer.
    #
    # This is where the previous Pylance problem is removed.
    # -----------------------------------------------------

    forecast_reliability: ForecastReliability = {
        "metric": str(
            raw_reliability.get(
                "metric",
                "N/A",
            )
        ),
        "method": str(
            raw_reliability.get(
                "method",
                "N/A",
            )
        ),
        "mape": _safe_float(
            raw_reliability.get(
                "mape",
            )
        ),
        "mae": _safe_float(
            raw_reliability.get(
                "mae",
            )
        ),
        "rmse": _safe_float(
            raw_reliability.get(
                "rmse",
            )
        ),
        "backtest_periods": _safe_int(
            raw_reliability.get(
                "backtest_periods",
            )
        ),
        "second_best_mape": _safe_float(
            raw_reliability.get(
                "second_best_mape",
            )
        ),
        "model_gap": _safe_float(
            raw_reliability.get(
                "model_gap",
            )
        ),
        "reliability_score": _safe_int(
            raw_reliability.get(
                "reliability_score",
            )
        ),
        "reliability_level": str(
            raw_reliability.get(
                "reliability_level",
                "N/A",
            )
        ),
        "interpretation": str(
            raw_reliability.get(
                "interpretation",
                "N/A",
            )
        ),
    }

    print_forecast_reliability(
        forecast_reliability,
    )

    # =====================================================
    # FORECAST PREDICTION INTERVALS (UPDATED)
    # =====================================================

    prediction_intervals = (
        engine.forecast_prediction_intervals(
            metric="Revenue",
            periods=3,
            method="linear_trend",
            window=3,
            min_history=6,
            confidence=0.95,
        )
    )

    print()
    print("=" * 78)
    print("FORECAST PREDICTION INTERVALS")
    print("=" * 78)

    print(
        "Confidence Level:   95%"
    )

    print(
        "Method:              linear_trend"
    )

    print()

    interval_display = (
        prediction_intervals[
            [
                "Month",
                "Forecast",
                "Lower Bound",
                "Upper Bound",
                "Forecast Horizon",
            ]
        ].copy()
    )

    format_date_column(
        interval_display,
        "Month",
    )

    format_currency_column(
        interval_display,
        "Forecast",
    )

    format_currency_column(
        interval_display,
        "Lower Bound",
    )

    format_currency_column(
        interval_display,
        "Upper Bound",
    )

    format_number_column(
        interval_display,
        "Forecast Horizon",
    )

    print(
        interval_display.to_string(
            index=False,
        )
    )

    # -----------------------------------------------------
    # Validate that uncertainty increases with horizon
    # -----------------------------------------------------

    interval_widths = (
        prediction_intervals[
            "Interval Width"
        ]
        .astype(float)
        .tolist()
    )

    if len(interval_widths) >= 2:
        assert (
            interval_widths[1]
            > interval_widths[0]
        ), (
            "Prediction interval should widen "
            "for the second forecast horizon."
        )

    if len(interval_widths) >= 3:
        assert (
            interval_widths[2]
            > interval_widths[1]
        ), (
            "Prediction interval should widen "
            "for the third forecast horizon."
        )

    print()
    print(
        "Prediction interval validation: PASS"
    )

    # =====================================================
    # FORECASTING EDGE-CASE VALIDATION
    # =====================================================

    print()
    print("=" * 78)
    print("FORECASTING EDGE-CASE VALIDATION")
    print("=" * 78)

    # -----------------------------------------------------
    # Invalid forecast periods
    # -----------------------------------------------------

    try:
        engine.forecast_revenue(
            periods=0,
            method="linear_trend",
        )

        raise AssertionError(
            "periods=0 should raise ValueError."
        )

    except ValueError:
        print(
            "Invalid forecast periods: PASS"
        )

    # -----------------------------------------------------
    # Invalid forecasting method
    # -----------------------------------------------------

    try:
        engine.forecast_revenue(
            periods=3,
            method="invalid_method",
        )

        raise AssertionError(
            "Invalid method should raise ValueError."
        )

    except ValueError:
        print(
            "Invalid forecasting method: PASS"
        )

    # -----------------------------------------------------
    # Invalid moving-average window
    # -----------------------------------------------------

    try:
        engine.forecast_revenue(
            periods=3,
            method="moving_average",
            window=0,
        )

        raise AssertionError(
            "window=0 should raise ValueError."
        )

    except ValueError:
        print(
            "Invalid forecast window: PASS"
        )

    # -----------------------------------------------------
    # Invalid prediction-interval confidence
    # -----------------------------------------------------

    try:
        engine.forecast_prediction_intervals(
            metric="Revenue",
            periods=3,
            method="linear_trend",
            confidence=0.0,
        )

        raise AssertionError(
            "confidence=0 should raise ValueError."
        )

    except ValueError:
        print(
            "Invalid confidence level: PASS"
        )

    # -----------------------------------------------------
    # Confidence above 100%
    # -----------------------------------------------------

    try:
        engine.forecast_prediction_intervals(
            metric="Revenue",
            periods=3,
            method="linear_trend",
            confidence=1.01,
        )

        raise AssertionError(
            "confidence > 1 should raise ValueError."
        )

    except ValueError:
        print(
            "Confidence above 100%: PASS"
        )

    # -----------------------------------------------------
    # Invalid minimum history
    # -----------------------------------------------------

    try:
        engine.forecast_prediction_intervals(
            metric="Revenue",
            periods=3,
            method="linear_trend",
            min_history=0,
        )

        raise AssertionError(
            "min_history=0 should raise ValueError."
        )

    except ValueError:
        print(
            "Invalid minimum history: PASS"
        )

    # -----------------------------------------------------
    # Prediction interval column validation
    # -----------------------------------------------------

    interval_columns = {
        "Forecast",
        "Lower Bound",
        "Upper Bound",
        "Confidence",
        "Interval Width",
        "Forecast Horizon",
    }

    missing_interval_columns = (
        interval_columns
        - set(prediction_intervals.columns)
    )

    assert not missing_interval_columns, (
        "Prediction interval output is missing "
        f"columns: {', '.join(sorted(missing_interval_columns))}"
    )

    print(
        "Prediction interval columns: PASS"
    )

    # -----------------------------------------------------
    # Forecast values must be numeric
    # -----------------------------------------------------

    forecast_values = pd.to_numeric(
        prediction_intervals["Forecast"],
        errors="coerce",
    )

    lower_values = pd.to_numeric(
        prediction_intervals["Lower Bound"],
        errors="coerce",
    )

    upper_values = pd.to_numeric(
        prediction_intervals["Upper Bound"],
        errors="coerce",
    )

    assert not forecast_values.isna().any(), (
        "Forecast contains invalid values."
    )

    assert not lower_values.isna().any(), (
        "Lower Bound contains invalid values."
    )

    assert not upper_values.isna().any(), (
        "Upper Bound contains invalid values."
    )

    print(
        "Prediction interval numeric values: PASS"
    )

    # -----------------------------------------------------
    # Lower bound must not exceed forecast
    # -----------------------------------------------------

    assert (
        lower_values <= forecast_values
    ).all(), (
        "Lower Bound cannot exceed Forecast."
    )

    print(
        "Lower bound validation: PASS"
    )

    # -----------------------------------------------------
    # Upper bound must not be below forecast
    # -----------------------------------------------------

    assert (
        upper_values >= forecast_values
    ).all(), (
        "Upper Bound cannot be below Forecast."
    )

    print(
        "Upper bound validation: PASS"
    )

    # -----------------------------------------------------
    # Horizon must increase sequentially
    # -----------------------------------------------------

    horizon_values = (
        prediction_intervals[
            "Forecast Horizon"
        ]
        .tolist()
    )

    expected_horizons = list(
        range(
            1,
            len(prediction_intervals) + 1,
        )
    )

    assert (
        horizon_values
        == expected_horizons
    ), (
        "Forecast horizons must increase "
        "sequentially from 1."
    )

    print(
        "Forecast horizon sequencing: PASS"
    )

    # -----------------------------------------------------
    # Interval width must increase with horizon
    # -----------------------------------------------------

    interval_widths = (
        pd.to_numeric(
            prediction_intervals[
                "Interval Width"
            ],
            errors="coerce",
        )
        .tolist()
    )

    assert not any(
        pd.isna(width)
        for width in interval_widths
    ), (
        "Interval Width contains invalid values."
    )

    for index in range(
        1,
        len(interval_widths),
    ):
        assert (
            interval_widths[index]
            > interval_widths[index - 1]
        ), (
            "Prediction interval width must "
            "increase with forecast horizon."
        )

    print(
        "Horizon-aware interval growth: PASS"
    )

    # -----------------------------------------------------
    # Revenue lower bounds cannot be negative
    # -----------------------------------------------------

    assert (
        lower_values >= 0.0
    ).all(), (
        "Revenue prediction lower bounds "
        "cannot be negative."
    )

    print(
        "Non-negative revenue lower bound: PASS"
    )

    print()
    print(
        "Forecasting edge-case validation: PASS"
    )

    # =====================================================
    # SUMMARY
    # =====================================================

    print()
    print("=" * 78)
    print("TIME-SERIES ENGINE TEST SUMMARY")
    print("=" * 78)

    print(
        f"Daily periods:       "
        f"{len(daily):,}"
    )

    print(
        f"Weekly periods:      "
        f"{len(weekly):,}"
    )

    print(
        f"Monthly periods:     "
        f"{len(monthly):,}"
    )

    print(
        f"Quarterly periods:   "
        f"{len(quarterly):,}"
    )

    print(
        f"Yearly periods:      "
        f"{len(yearly):,}"
    )

    print(
        f"Valid 3M windows:    "
        f"{len(valid_3):,}"
    )

    print(
        f"Valid 6M windows:    "
        f"{len(valid_6):,}"
    )

    print(
        f"Valid 12M windows:   "
        f"{len(valid_12):,}"
    )

    print(
        f"Partial periods:     "
        f"{len(partial_periods):,}"
    )

    print()
    print(
        "Time-Series analysis completed successfully."
    )


# =========================================================
# SAFE TYPE CONVERSION HELPERS
# =========================================================

def _safe_float(
    value: object,
) -> float:
    """
    Safely converts an unknown value to float.

    This function is intentionally typed with object
    so that Pylance can validate every conversion.
    """

    if value is None:
        return float("nan")

    if isinstance(value, bool):
        return float(value)

    if isinstance(value, int | float):
        return float(value)

    if isinstance(value, str):
        stripped_value = value.strip()

        if stripped_value == "":
            return float("nan")

        if stripped_value.upper() == "N/A":
            return float("nan")

        try:
            return float(
                stripped_value.rstrip("%"),
            )
        except ValueError:
            return float("nan")

    return float("nan")


def _safe_int(
    value: object,
) -> int:
    """
    Safely converts an unknown value to int.

    This prevents Pylance from treating dictionary
    values as arbitrary objects.
    """

    if value is None:
        return 0

    if isinstance(value, bool):
        return int(value)

    if isinstance(value, int):
        return value

    if isinstance(value, float):
        if math.isnan(value):
            return 0

        return int(value)

    if isinstance(value, str):
        stripped_value = value.strip()

        if stripped_value == "":
            return 0

        if stripped_value.upper() == "N/A":
            return 0

        try:
            return int(
                float(stripped_value)
            )
        except ValueError:
            return 0

    return 0


if __name__ == "__main__":
    main()