"""Natural-language Q&A over the current dashboard selection, via the Claude API."""

import os

import pandas as pd

MODEL = "claude-opus-5"


def _summarize_for_context(filtered_data: pd.DataFrame, anomalies: pd.DataFrame) -> str:
    """Build a compact text summary of the current selection for the model's context."""
    totals = filtered_data.groupby("gas_type", as_index=False)["co2e_emissions_mt"].sum()
    yearly = filtered_data.groupby("reporting_year", as_index=False)["co2e_emissions_mt"].sum()
    top_facilities = (
        filtered_data.groupby("facility_name", as_index=False)["co2e_emissions_mt"]
        .sum()
        .nlargest(10, "co2e_emissions_mt")
    )
    lines = [
        f"Facilities in selection: {filtered_data['facility_name'].nunique()}",
        f"States in selection: {', '.join(sorted(filtered_data['state'].dropna().unique()))}",
        f"Reporting years: {int(filtered_data['reporting_year'].min())}-{int(filtered_data['reporting_year'].max())}",
        "",
        "Emissions by gas type (MT CO2e):",
        totals.to_string(index=False),
        "",
        "Total emissions by year (MT CO2e):",
        yearly.to_string(index=False),
        "",
        "Top 10 facilities by cumulative emissions (MT CO2e):",
        top_facilities.to_string(index=False),
    ]
    if anomalies.empty:
        lines += ["", "No year-over-year anomalies flagged at the current threshold."]
    else:
        lines += [
            "",
            f"Year-over-year anomalies flagged: {len(anomalies)}",
            anomalies.to_string(index=False),
        ]
    return "\n".join(lines)


def get_ai_answer(question: str, filtered_data: pd.DataFrame, anomalies: pd.DataFrame) -> dict:
    """Answer a natural-language question about the current data selection.

    Returns {"status": "ok" | "error", "text": str}.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return {
            "status": "error",
            "text": "ANTHROPIC_API_KEY is not set. Add it to your environment to enable Q&A.",
        }

    try:
        import anthropic
    except ImportError:
        return {
            "status": "error",
            "text": "The 'anthropic' package is not installed. Run: pip install anthropic",
        }

    context = _summarize_for_context(filtered_data, anomalies)
    client = anthropic.Anthropic(api_key=api_key)
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=[
                {
                    "type": "text",
                    "text": (
                        "You are an analyst assistant for an oil & gas emissions dashboard. "
                        "Answer the user's question using only the summarized data below. "
                        "Be concise and reference specific numbers where relevant.\n\n" + context
                    ),
                    # Repeat questions against the same filter selection reuse this cached
                    # prefix instead of reprocessing the full data summary each time.
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": question}],
        )
    except anthropic.AuthenticationError:
        return {"status": "error", "text": "ANTHROPIC_API_KEY was rejected. Check that it is valid."}
    except anthropic.RateLimitError:
        return {"status": "error", "text": "Rate limited by the Claude API. Try again shortly."}
    except anthropic.APIConnectionError:
        return {"status": "error", "text": "Could not reach the Claude API. Check your network connection."}
    except anthropic.APIStatusError as exc:
        return {"status": "error", "text": f"Claude API error ({exc.status_code}): {exc.message}"}

    text = next((block.text for block in response.content if block.type == "text"), "")
    return {"status": "ok", "text": text or "No answer was returned."}
