"""Plotly chart builders."""

import pandas as pd
import plotly.express as px
from plotly.graph_objects import Figure

from dashboard.theme import AMBER, GAS_COLORS, MUTED, PANEL, TEAL, TEAL_SEQUENTIAL, plotly_layout_defaults


def _layout(chart: Figure, title: str) -> Figure:
    chart.update_layout(title=title, **plotly_layout_defaults())
    return chart


def _yearly_line_chart(totals: pd.DataFrame, title: str) -> Figure:
    chart = px.line(
        totals.sort_values("reporting_year"), x="reporting_year", y="co2e_emissions_mt", markers=True,
        labels={"reporting_year": "Reporting year", "co2e_emissions_mt": "CO₂e emissions (MT)"},
        color_discrete_sequence=[TEAL],
    )
    chart.update_traces(line=dict(width=2.5), marker=dict(size=7))
    chart.update_xaxes(dtick=1)
    return _layout(chart, title)


def emissions_over_time(data: pd.DataFrame) -> Figure:
    totals = data.groupby("reporting_year", as_index=False)["co2e_emissions_mt"].sum()
    return _yearly_line_chart(totals, "Emissions over time")


def facility_trend(data: pd.DataFrame, facility: str) -> Figure:
    """A single facility's emissions across every reporting year it has data for."""
    facility_data = data.loc[data["facility_name"] == facility]
    totals = facility_data.groupby("reporting_year", as_index=False)["co2e_emissions_mt"].sum()
    return _yearly_line_chart(totals, f"{facility} — emissions history")


def top_facilities(data: pd.DataFrame) -> Figure:
    totals = (data.groupby("facility_name", as_index=False)["co2e_emissions_mt"].sum()
              .nlargest(10, "co2e_emissions_mt").sort_values("co2e_emissions_mt"))
    chart = px.bar(
        totals, x="co2e_emissions_mt", y="facility_name", orientation="h", color="co2e_emissions_mt",
        color_continuous_scale=TEAL_SEQUENTIAL,
        labels={"facility_name": "Facility", "co2e_emissions_mt": "CO₂e emissions (MT)"},
    )
    chart.update_layout(coloraxis_showscale=False)
    return _layout(chart, "Top 10 emitting facilities")


def emissions_by_gas(data: pd.DataFrame) -> Figure:
    totals = data.groupby("gas_type", as_index=False)["co2e_emissions_mt"].sum()
    chart = px.pie(
        totals, names="gas_type", values="co2e_emissions_mt", hole=0.35, color="gas_type",
        color_discrete_map=GAS_COLORS,
    )
    chart.update_traces(
        textposition="inside", textinfo="percent+label", marker=dict(line=dict(color=PANEL, width=2))
    )
    return _layout(chart, "Emissions by gas type")


def anomaly_scatter(scatter_data: pd.DataFrame, threshold_pct: float) -> Figure:
    """Emissions level vs. YoY growth; points past the threshold read as amber flags."""
    plot_data = scatter_data.copy()
    plot_data["Status"] = plot_data["YoY Change"].gt(threshold_pct).map(
        {True: "Flagged", False: "Normal"}
    )
    chart = px.scatter(
        plot_data, x="CO₂e emissions (MT)", y="YoY Change", color="Status",
        color_discrete_map={"Flagged": AMBER, "Normal": TEAL},
        hover_data=["Facility", "State", "Reporting year", "Gas type"],
        labels={"CO₂e emissions (MT)": "CO₂e emissions (MT)", "YoY Change": "YoY change (%)"},
    )
    chart.update_traces(marker=dict(size=9, opacity=0.85, line=dict(width=1, color=PANEL)))
    chart.add_hline(
        y=threshold_pct, line_dash="dash", line_color=AMBER, opacity=0.6,
        annotation_text=f"{threshold_pct:.0f}% threshold", annotation_position="top left",
        annotation_font_color=MUTED,
    )
    return _layout(chart, "Emissions vs. year-over-year growth")
