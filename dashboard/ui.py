"""Streamlit UI components."""

import pandas as pd
import streamlit as st

from dashboard.theme import GAS_COLORS, MUTED


def _format(value: float, suffix: str) -> str:
    if value >= 1_000_000:
        return f"{value / 1_000_000:,.2f}M{suffix}"
    if value >= 1_000:
        return f"{value / 1_000:,.1f}K{suffix}"
    return f"{value:,.0f}{suffix}"


def render_data_uploader():
    """Render the optional CSV upload control at the top of the sidebar."""
    with st.sidebar:
        st.markdown('<div class="sidebar-kicker">Data source</div>', unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "Upload your own emissions CSV (optional)", type="csv"
        )
        st.caption(
            "Expected columns: facility_name, state, industry_segment, reporting_year, "
            "gas_type, co2e_emissions_mt, production_boe"
        )
        st.markdown('<hr class="section-divider" />', unsafe_allow_html=True)
    return uploaded_file


def render_reference_guide() -> None:
    """Render the collapsible Reference Guide shown below the dashboard header."""
    with st.expander("Reference Guide", expanded=False):
        st.markdown("##### What this dashboard shows")
        st.markdown(
            "<span style='color:var(--muted);'>Reported greenhouse-gas emissions, production, "
            "and operational intensity for oil &amp; gas facilities, modeled on the EPA's "
            "Greenhouse Gas Reporting Program (GHGRP).</span>",
            unsafe_allow_html=True,
        )

        st.markdown("##### Key terms")
        terms = [
            ("CO₂e", "Carbon dioxide equivalent — the standard unit combining CO2, CH4, and N2O by warming impact."),
            ("CH4 / N2O", "Methane and nitrous oxide, tracked separately due to higher warming potential than CO2."),
            ("Subpart W", "EPA GHGRP reporting category for petroleum and natural gas systems."),
            ("Emissions intensity", "CO2e per unit of production (kg CO2e / BOE), for comparing efficiency across facility sizes."),
            ("YoY Change", "Year-over-year percent change in emissions, used to flag anomalies."),
            ("BOE", "Barrels of Oil Equivalent — the standard unit combining oil and gas production."),
        ]
        left_column, right_column = st.columns(2)
        half = (len(terms) + 1) // 2
        for column, subset in ((left_column, terms[:half]), (right_column, terms[half:])):
            with column:
                for term, definition in subset:
                    st.markdown(
                        f"<div style='margin-bottom:12px;'>"
                        f"<span style='color:var(--text);font-weight:600;'>{term}</span><br/>"
                        f"<span style='color:var(--muted);font-size:0.88rem;'>{definition}</span>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )

        st.markdown("##### How to use this dashboard")
        st.markdown(
            "<ol style='color:var(--muted);padding-left:20px;margin:0;'>"
            "<li>Filter by state, facility, and reporting year in the sidebar.</li>"
            "<li>Adjust the anomaly threshold slider to flag more or fewer year-over-year increases.</li>"
            "<li>Narrow the Facility filter to a single facility to see its metrics and trends in isolation.</li>"
            "<li>Ask the AI Q&amp;A box a question grounded in the current filtered selection.</li>"
            "<li>Optionally upload your own CSV matching the expected column format.</li>"
            "</ol>",
            unsafe_allow_html=True,
        )

        st.markdown(
            "<div style='color:var(--muted);font-size:0.82rem;margin-top:14px;'>"
            "Data source: sample data modeled on EPA GHGRP Subpart W reporting structure."
            "</div>",
            unsafe_allow_html=True,
        )


def render_filters(data: pd.DataFrame) -> dict[str, object]:
    """Render sidebar controls and return their selected values."""
    with st.sidebar:
        st.markdown('<div class="sidebar-kicker">Dashboard controls</div>', unsafe_allow_html=True)
        st.header("Filters")
        st.caption("Refine the dashboard selection.")
        states = sorted(data["state"].dropna().unique())
        selected_states = st.multiselect("State", states, default=states)
        facilities = sorted(data.loc[data["state"].isin(selected_states), "facility_name"].unique())
        selected_facilities = st.multiselect("Facility", facilities, default=facilities)
        years = st.slider(
            "Reporting year", int(data["reporting_year"].min()), int(data["reporting_year"].max()),
            (int(data["reporting_year"].min()), int(data["reporting_year"].max())), step=1,
            help="Choose an inclusive reporting-year range.",
        )
        st.markdown('<hr class="section-divider" />', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-kicker">Threshold monitor</div>', unsafe_allow_html=True)
        st.subheader("Anomaly detector")
        anomaly_threshold = st.slider(
            "Anomaly threshold (% YoY increase)", 10, 100, 30, step=5
        )
        anomaly_gas_type = st.selectbox(
            "Gas type for anomalies", ["All", "CO2", "CH4", "N2O"]
        )
        st.markdown('<hr class="section-divider" />', unsafe_allow_html=True)
        st.caption("Sample data modeled on EPA GHGRP Subpart W reporting structure.")
    return {
        "states": selected_states,
        "facilities": selected_facilities,
        "years": years,
        "anomaly_threshold": anomaly_threshold,
        "anomaly_gas_type": anomaly_gas_type,
    }


def _metric_panel(label: str, value: str) -> str:
    return (
        '<div class="metric-panel">'
        f'<div class="metric-label">{label}</div>'
        f'<div class="metric-value">{value}</div>'
        "</div>"
    )


def render_metrics(metrics: dict[str, float]) -> None:
    """Render dashboard KPIs as bordered panel readouts."""
    emissions, production, intensity = st.columns(3)
    with emissions:
        st.markdown(
            _metric_panel("Total CO₂e emissions", _format(metrics["emissions"], " MT")),
            unsafe_allow_html=True,
        )
    with production:
        st.markdown(
            _metric_panel("Total production", _format(metrics["production"], " BOE")),
            unsafe_allow_html=True,
        )
    with intensity:
        st.markdown(
            _metric_panel("Emissions intensity", f"{metrics['intensity']:,.2f} kg CO₂e / BOE"),
            unsafe_allow_html=True,
        )


def render_facility_drilldown(facility: str, summary: dict, trend_chart, is_flagged: bool) -> None:
    """Render the bordered facility drill-down panel: trend chart, key stats, gas breakdown."""
    with st.container(border=True):
        title_column, badge_column = st.columns([5, 1])
        with title_column:
            st.markdown(f"##### {facility}")
        if is_flagged:
            with badge_column:
                st.markdown(
                    '<div class="badge-amber">⚠ Flagged</div>',
                    unsafe_allow_html=True,
                )

        st.plotly_chart(trend_chart, use_container_width=True)

        avg_yoy = summary["avg_yoy_change"]
        avg_yoy_text = f"{avg_yoy:+.1f}%" if pd.notna(avg_yoy) else "N/A"

        stat_column1, stat_column2 = st.columns(2)
        with stat_column1:
            st.markdown(
                _metric_panel("Total emissions (all years)", _format(summary["total_emissions"], " MT")),
                unsafe_allow_html=True,
            )
        with stat_column2:
            st.markdown(_metric_panel("Average YoY change", avg_yoy_text), unsafe_allow_html=True)

        st.markdown(
            '<div class="metric-label" style="margin-top:16px;">Gas-type breakdown</div>',
            unsafe_allow_html=True,
        )
        breakdown_html = "".join(
            "<div style='display:flex;justify-content:space-between;padding:4px 0;"
            "border-bottom:1px solid var(--border);'>"
            f"<span style='color:var(--text);'>"
            f"<span style='display:inline-block;width:9px;height:9px;border-radius:2px;"
            f"background:{GAS_COLORS.get(row.gas_type, MUTED)};margin-right:8px;'></span>{row.gas_type}"
            "</span>"
            f"<span style='font-family:var(--mono);color:var(--muted);'>{row.share_pct:.0f}%</span>"
            "</div>"
            for row in summary["gas_breakdown"].itertuples()
        )
        st.markdown(breakdown_html, unsafe_allow_html=True)
