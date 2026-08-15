"""Streamlit entry point for the Oil & Gas Emissions Analytics dashboard."""

import pandas as pd
import streamlit as st
from pandas.io.formats.style import Styler

from dashboard.ai import get_ai_answer
from dashboard.charts import (
    anomaly_scatter,
    emissions_by_gas,
    emissions_over_time,
    facility_trend,
    top_facilities,
)
from dashboard.data import (
    clean_data,
    detect_year_over_year_anomalies,
    facility_summary,
    filter_data,
    load_data,
    summarize_data,
    validate_uploaded_data,
    year_over_year_scatter_data,
)
from dashboard.theme import dashboard_header, inject_theme, section_divider
from dashboard.ui import (
    render_data_uploader,
    render_facility_drilldown,
    render_filters,
    render_metrics,
    render_reference_guide,
)


def style_anomaly_table(anomalies: pd.DataFrame) -> Styler:
    """Flag YoY-change cells with an amber alert wash, scaled by severity."""

    panel_rgb = (27, 35, 44)  # --panel
    amber_rgb = (232, 163, 61)  # --amber

    def yoy_alert(values: pd.Series) -> list[str]:
        low, high = values.min(), values.max()
        span = high - low
        styles = []
        for value in values:
            intensity = (value - low) / span if span else 0.6
            red = int(panel_rgb[0] + (amber_rgb[0] - panel_rgb[0]) * intensity)
            green = int(panel_rgb[1] + (amber_rgb[1] - panel_rgb[1]) * intensity)
            blue = int(panel_rgb[2] + (amber_rgb[2] - panel_rgb[2]) * intensity)
            text_color = "#12181F" if intensity >= 0.55 else "#E8A33D"
            styles.append(
                f"background-color: rgb({red}, {green}, {blue}); color: {text_color}; "
                f"font-weight: 600; font-family: 'IBM Plex Mono', monospace;"
            )
        return styles

    return (
        anomalies.style.format({"CO₂e emissions (MT)": "{:.1f}", "YoY Change": "{:.1f}%"})
        .apply(yoy_alert, subset=["YoY Change"])
        .set_properties(
            subset=["CO₂e emissions (MT)"],
            **{"font-family": "'IBM Plex Mono', monospace"},
        )
    )


st.set_page_config(
    page_title="Oil & Gas Emissions Analytics",
    page_icon="⛽",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_theme()
dashboard_header(
    "Oil & Gas Emissions Analytics",
    "Explore reported greenhouse-gas emissions, production, and operational intensity.",
)
render_reference_guide()

uploaded_file = render_data_uploader()
if uploaded_file is None:
    data = load_data()
else:
    uploaded_raw = pd.read_csv(uploaded_file)
    validation_errors = validate_uploaded_data(uploaded_raw)
    if validation_errors:
        st.error(
            "Uploaded CSV is invalid — using the sample dataset instead:\n\n"
            + "\n".join(f"- {message}" for message in validation_errors)
        )
        data = load_data()
    else:
        data = clean_data(uploaded_raw)
        st.success(f"Using uploaded data: {len(data):,} rows, {data['facility_name'].nunique():,} facilities")

filters = render_filters(data)
filtered_data = filter_data(
    data,
    states=filters["states"],
    facilities=filters["facilities"],
    years=filters["years"],
)

if filtered_data.empty:
    st.info("No records match the current filters. Adjust the sidebar selection to continue.")
    st.stop()

anomalies = detect_year_over_year_anomalies(
    data,
    states=filters["states"],
    facilities=filters["facilities"],
    years=filters["years"],
    gas_type=filters["anomaly_gas_type"],
    threshold=filters["anomaly_threshold"] / 100,
)

render_metrics(summarize_data(filtered_data))
section_divider()

st.plotly_chart(emissions_over_time(filtered_data), use_container_width=True)
st.caption("Total CO₂e emissions reported each year for the current selection.")

facilities_column, gas_column = st.columns(2)
with facilities_column:
    st.plotly_chart(top_facilities(filtered_data), use_container_width=True)
    st.caption("Facilities with the largest cumulative CO₂e emissions.")

with gas_column:
    st.plotly_chart(emissions_by_gas(filtered_data), use_container_width=True)
    st.caption("Share of CO₂e emissions attributable to CO₂, CH₄, and N₂O.")

section_divider()
st.subheader("Facility drill-down")
drilldown_options = [""] + sorted(filtered_data["facility_name"].unique())
selected_facility = st.selectbox(
    "Select a facility for detailed view",
    options=drilldown_options,
    format_func=lambda name: "Select a facility..." if name == "" else name,
)
if selected_facility:
    flagged_facilities = set(anomalies["Facility"]) if not anomalies.empty else set()
    render_facility_drilldown(
        selected_facility,
        facility_summary(data, selected_facility),
        facility_trend(data, selected_facility),
        is_flagged=selected_facility in flagged_facilities,
    )

section_divider()
with st.expander("Raw filtered data", expanded=False):
    st.dataframe(filtered_data, use_container_width=True, hide_index=True)
    st.download_button(
        "Download filtered data as CSV",
        data=filtered_data.to_csv(index=False).encode("utf-8"),
        file_name="emissions_filtered_export.csv",
        mime="text/csv",
    )

section_divider()
st.subheader("Year-over-year emissions anomalies")
scatter_data = year_over_year_scatter_data(
    data,
    states=filters["states"],
    facilities=filters["facilities"],
    years=filters["years"],
    gas_type=filters["anomaly_gas_type"],
)
if scatter_data.empty:
    st.caption("Not enough consecutive-year data in the current selection to plot growth.")
else:
    st.plotly_chart(
        anomaly_scatter(scatter_data, filters["anomaly_threshold"]), use_container_width=True
    )
    st.caption("Each point is one facility-year. Amber points exceed the anomaly threshold.")

selected_facility_count = len(filters["facilities"])
flagged_facility_count = anomalies["Facility"].nunique()
if anomalies.empty:
    st.success(
        f"No facilities exceeded the {filters['anomaly_threshold']}% year-over-year increase threshold."
    )
else:
    st.caption(f"{flagged_facility_count} facilities flagged out of {selected_facility_count}.")
    st.dataframe(
        style_anomaly_table(anomalies),
        use_container_width=True,
        hide_index=True,
    )
st.caption("Flags consecutive reporting years where facility emissions exceed the selected YoY increase threshold.")

section_divider()
with st.container(border=True):
    st.subheader("Ask a question about this data")
    question = st.text_input(
        "Question",
        placeholder="e.g. Which facility had the largest year-over-year increase?",
        label_visibility="collapsed",
    )
    if question:
        with st.spinner("Thinking..."):
            answer = get_ai_answer(question, filtered_data, anomalies)
        error_class = " is-error" if answer["status"] == "error" else ""
        answer_column, action_column = st.columns([5, 1])
        with answer_column:
            st.markdown(
                f'<div class="qa-answer{error_class}">{answer["text"]}</div>',
                unsafe_allow_html=True,
            )
        with action_column:
            st.download_button(
                "Save",
                data=answer["text"],
                file_name="ai_answer.txt",
                mime="text/plain",
                use_container_width=True,
            )
