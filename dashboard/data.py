"""Data loading, filtering, and metric calculations."""

import pandas as pd
import streamlit as st

from dashboard.config import DATA_PATH


REQUIRED_COLUMNS = [
    "facility_name",
    "state",
    "industry_segment",
    "reporting_year",
    "gas_type",
    "co2e_emissions_mt",
    "production_boe",
]


def clean_data(data: pd.DataFrame) -> pd.DataFrame:
    """Coerce numeric columns and drop rows missing key identifiers."""
    data = data.copy()
    for column in ("reporting_year", "co2e_emissions_mt", "production_boe"):
        data[column] = pd.to_numeric(data[column], errors="coerce")
    return data.dropna(subset=["facility_name", "state", "reporting_year"])


@st.cache_data(show_spinner="Loading emissions data...")
def load_data() -> pd.DataFrame:
    """Read and clean the local GHGRP sample data."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Data file not found: {DATA_PATH}")

    return clean_data(pd.read_csv(DATA_PATH))


def validate_uploaded_data(data: pd.DataFrame) -> list[str]:
    """Return validation error messages for an uploaded CSV; an empty list means it's usable."""
    missing = [column for column in REQUIRED_COLUMNS if column not in data.columns]
    if missing:
        return [f"Missing required columns: {', '.join(missing)}"]

    errors = []
    if pd.to_numeric(data["reporting_year"], errors="coerce").isna().any():
        errors.append("Column 'reporting_year' must be numeric.")
    for column in ("co2e_emissions_mt", "production_boe"):
        numeric = pd.to_numeric(data[column], errors="coerce")
        if numeric.isna().any():
            errors.append(f"Column '{column}' must be numeric.")
        elif (numeric < 0).any():
            errors.append(f"Column '{column}' must be non-negative.")
    return errors


def filter_data(
    data: pd.DataFrame,
    states: list[str],
    facilities: list[str],
    years: tuple[int, int],
) -> pd.DataFrame:
    """Apply sidebar selections to the data."""
    return data.loc[
        data["state"].isin(states)
        & data["facility_name"].isin(facilities)
        & data["reporting_year"].between(*years)
    ].copy()


def summarize_data(data: pd.DataFrame) -> dict[str, float]:
    """Calculate headline metrics without duplicating gas-level production rows."""
    production = (
        data.groupby(["facility_name", "reporting_year"], as_index=False)["production_boe"]
        .max()["production_boe"]
        .sum()
    )
    emissions = data["co2e_emissions_mt"].sum()
    return {
        "emissions": emissions,
        "production": production,
        "intensity": (emissions * 1_000 / production) if production else 0,
    }


def facility_summary(data: pd.DataFrame, facility: str) -> dict:
    """Full-history stats for a single facility, independent of the sidebar year filter."""
    facility_data = data.loc[data["facility_name"] == facility]
    total_emissions = facility_data["co2e_emissions_mt"].sum()

    yearly = (
        facility_data.groupby("reporting_year", as_index=False)["co2e_emissions_mt"]
        .sum()
        .sort_values("reporting_year")
    )
    yearly["yoy_change"] = yearly["co2e_emissions_mt"].pct_change() * 100

    gas_breakdown = (
        facility_data.groupby("gas_type", as_index=False)["co2e_emissions_mt"]
        .sum()
        .sort_values("co2e_emissions_mt", ascending=False)
    )
    gas_breakdown["share_pct"] = (
        gas_breakdown["co2e_emissions_mt"] / total_emissions * 100 if total_emissions else 0
    )

    return {
        "total_emissions": total_emissions,
        "avg_yoy_change": yearly["yoy_change"].mean(skipna=True),
        "gas_breakdown": gas_breakdown,
        "yearly": yearly,
    }


_ANOMALY_COLUMNS = {
    "facility_name": "Facility",
    "state": "State",
    "gas_type": "Gas type",
    "reporting_year": "Reporting year",
    "co2e_emissions_mt": "CO₂e emissions (MT)",
    "year_over_year_increase": "YoY Change",
}
_ANOMALY_COLUMN_ORDER = ["Facility", "State", "Reporting year", "CO₂e emissions (MT)", "Gas type", "YoY Change"]


def _year_over_year_changes(
    data: pd.DataFrame,
    states: list[str],
    facilities: list[str],
    years: tuple[int, int],
    gas_type: str = "All",
) -> pd.DataFrame:
    """Per facility/gas/year emissions with year-over-year % change, before any threshold filter.

    Calculation occurs before applying the selected year window so a selected
    first year can still be compared with its preceding reporting year. Rows
    without a valid consecutive prior year are dropped.
    """
    selected = data.loc[
        data["state"].isin(states) & data["facility_name"].isin(facilities)
    ].copy()
    if gas_type == "All":
        selected["gas_type"] = "All"
    else:
        selected = selected.loc[selected["gas_type"] == gas_type]
    annual = (
        selected.groupby(["facility_name", "state", "gas_type", "reporting_year"], as_index=False)[
            "co2e_emissions_mt"
        ]
        .sum()
        .sort_values(["facility_name", "state", "gas_type", "reporting_year"])
    )
    group_keys = ["facility_name", "state", "gas_type"]
    annual["prior_year"] = annual.groupby(group_keys)["reporting_year"].shift()
    annual["prior_emissions"] = annual.groupby(group_keys)["co2e_emissions_mt"].shift()
    annual["year_over_year_increase"] = (
        annual["co2e_emissions_mt"] / annual["prior_emissions"] - 1
    ) * 100
    return annual.loc[
        annual["reporting_year"].between(*years)
        & annual["prior_year"].eq(annual["reporting_year"] - 1)
        & annual["prior_emissions"].gt(0)
    ].copy()


def year_over_year_scatter_data(
    data: pd.DataFrame,
    states: list[str],
    facilities: list[str],
    years: tuple[int, int],
    gas_type: str = "All",
) -> pd.DataFrame:
    """Every consecutive-year facility/gas emissions point with its YoY % change.

    Unlike ``detect_year_over_year_anomalies``, this is not filtered by threshold —
    it's the full population the anomaly scatter plot draws from.
    """
    changes = _year_over_year_changes(data, states, facilities, years, gas_type)
    return changes.rename(columns=_ANOMALY_COLUMNS)[_ANOMALY_COLUMN_ORDER]


def detect_year_over_year_anomalies(
    data: pd.DataFrame,
    states: list[str],
    facilities: list[str],
    years: tuple[int, int],
    gas_type: str = "All",
    threshold: float = 0.30,
) -> pd.DataFrame:
    """Return consecutive-year facility/gas emissions increases above ``threshold``."""
    changes = _year_over_year_changes(data, states, facilities, years, gas_type)
    anomalies = changes.loc[changes["year_over_year_increase"].gt(threshold * 100)].copy()
    return (
        anomalies.rename(columns=_ANOMALY_COLUMNS)[_ANOMALY_COLUMN_ORDER]
        .sort_values("YoY Change", ascending=False)
    )
