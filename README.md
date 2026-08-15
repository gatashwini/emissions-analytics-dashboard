# Oil & Gas Emissions Analytics Dashboard

A Streamlit dashboard for exploring oil and gas greenhouse-gas emissions data, styled as a dark, industrial monitoring tool. It ships with a sample CSV, lets you upload your own data, and includes an AI Q&A panel grounded in whatever's currently filtered.

## Live Demo

**[https://emissions-analytics-dashboard.streamlit.app](https://emissions-analytics-dashboard.streamlit.app/)**

The AI Q&A feature requires an `ANTHROPIC_API_KEY` to function. The public live demo doesn't have this configured, so you'll see a graceful fallback message there instead of a live AI response — this is intentional error handling, not a missing feature. See the Setup section below to run it locally with your own key for the full AI Q&A experience.

The app auto-deploys from the `main` branch, so the live link always reflects the latest pushed version.

## Features

- **Dark, control-room themed UI** — custom CSS overrides the default Streamlit theme with a deep charcoal-navy background, bordered "panel" cards, Inter for text, and IBM Plex Mono for numeric readouts. Teal marks nominal/normal states, amber marks flags and alerts.
- **Sidebar filters** for state, facility, and reporting year, plus KPI panels for total CO₂e emissions, total production, and emissions intensity (kg CO₂e / BOE).
- **Plotly charts** — emissions-over-time trend, top-10 emitting facilities, and emissions-by-gas-type breakdown, all styled to match the dark theme.
- **Anomaly detector** — an adjustable 10–100% year-over-year threshold slider, a gas-type filter, an emissions-vs-growth scatter plot (amber points exceed the threshold, teal points don't, with a dashed line marking the cutoff), and a flagged-facilities table with amber severity highlighting scaled to how far each facility exceeded the threshold.
- **Facility drill-down** — pick any currently filtered facility to see its full emissions history (not limited to the sidebar's year range), total emissions, average year-over-year change, a gas-type breakdown, and an amber "Flagged" badge if it's currently in the anomaly table.
- **CSV upload** — upload your own emissions CSV from the sidebar. It's validated (required columns present; year, emissions, and production numeric and non-negative) before use; an invalid file shows exactly what's wrong and the dashboard falls back to the sample data.
- **Raw data export** — a "Raw filtered data" panel shows the current selection as a table with a button to download it as `emissions_filtered_export.csv`.
- **"Ask a question about this data"** — a natural-language Q&A panel powered by Claude (Anthropic API), answered from a summary of the currently filtered selection rather than the full dataset, with a "Save" button to download the answer as a `.txt` file before it's replaced by the next question.
- **In-app Reference Guide** — a collapsible panel below the header explaining what the dashboard shows, a glossary of terms (CO₂e, CH4/N2O, Subpart W, emissions intensity, YoY change, BOE), and numbered usage steps.
- Cached CSV loading with Pandas.
- Modular data, chart, UI, theme, and AI components.

## Project structure

```text
.
├── app.py                   # Streamlit application entry point
├── dashboard/
│   ├── ai.py                  # Claude-powered Q&A over the filtered data
│   ├── charts.py               # Plotly chart builders
│   ├── config.py                # Paths and environment configuration
│   ├── data.py                   # Loading, validation, filtering, metrics, anomaly detection
│   ├── theme.py                   # CSS injection, color tokens, and Plotly theme defaults
│   └── ui.py                       # Sidebar controls, KPI panels, drill-down, reference guide
├── Data/
│   └── ghgrp_oilgas_emissions_sample.csv
├── .env.example              # Environment-variable template
└── requirements.txt
```

## Setup with uv

Install [uv](https://docs.astral.sh/uv/) if it is not already available, then run these commands from the project directory:

```powershell
uv venv
.\.venv\Scripts\Activate.ps1
uv pip install -r requirements.txt
Copy-Item .env.example .env
streamlit run app.py
```

Alternatively, run the app without activating the environment:

```powershell
uv run --with-requirements requirements.txt streamlit run app.py
```

`requirements.txt` pins `streamlit`, `pandas`, `plotly`, `python-dotenv`, and `anthropic` — the commands above install all five.

## API configuration

The dashboard works fully without any API key — filters, charts, the anomaly detector, the facility drill-down, CSV upload, and CSV export only ever touch local data.

The **"Ask a question about this data"** panel calls the Claude API and needs `ANTHROPIC_API_KEY`:

1. Get a key from [console.anthropic.com](https://console.anthropic.com) — this is separate from a claude.ai subscription.
2. Copy `.env.example` to `.env` and set `ANTHROPIC_API_KEY=<your key>`.
3. The Anthropic API is a prepaid/credit system, not a subscription — usage draws down credits you add to the account, so there's no surprise billing.

Without a key set, the Q&A panel shows an inline amber message instead of failing the app.

`EMISSIONS_API_KEY` and `EMISSIONS_API_BASE_URL` are also read from `.env` but are currently unused placeholders for a possible future external emissions-data API.

## CSV format

**Sample data** (`Data/ghgrp_oilgas_emissions_sample.csv`) and **any uploaded file** use the same seven columns:

| Column | Type | Notes |
|---|---|---|
| `facility_name` | text | Unique facility identifier; groups all metrics, charts, and the drill-down |
| `state` | text | Two-letter state code |
| `industry_segment` | text | e.g. "Onshore Production" |
| `reporting_year` | number | e.g. 2019–2023; drives the sidebar year filter and year-over-year anomaly detection |
| `gas_type` | text | `CO2`, `CH4`, or `N2O` — one row per gas per facility per year |
| `co2e_emissions_mt` | number, ≥ 0 | CO₂-equivalent emissions in metric tons |
| `production_boe` | number, ≥ 0 | Repeats across a facility's gas rows for a given year (the dashboard takes the max, not the sum, per facility/year, so it isn't triple-counted) |

**Upload validation** (`dashboard/data.py:validate_uploaded_data`) checks, in order:

1. All seven columns above are present — if any are missing, the error names exactly which ones.
2. `reporting_year` is numeric.
3. `co2e_emissions_mt` and `production_boe` are numeric and non-negative.

A file that fails any check is rejected with a specific error message, and the dashboard keeps using the sample data instead of crashing.

## Design

The UI is built to read like an industrial control-room panel rather than a default Streamlit app: a deep charcoal-navy background, bordered panel cards for metrics and charts, monospace numeric readouts, and a restrained two-color accent system — teal for nominal/normal states, amber for flags and alerts — mirroring how SCADA and gauge dashboards actually use color, rather than a generic purple-gradient dashboard look. The same palette carries through every later addition (the drill-down badge, the scatter plot, the upload/validation messages) so nothing added after the initial pass looks bolted on.
