import streamlit as st

from ui.charts import (
    plot_drawdown,
    plot_equity_curve,
    plot_inflation_vs_sp500,
    render_risk_scatter,
    simulate_1000_from_date,
)
from ui.education import render_investing_guide, render_resource_library


def display_metrics(stats, show_tooltips=False):
    labels = {
        "Total Return": "Investment performance, excluding deposits.",
        "Total Contributed": "Initial balance plus monthly deposits.",
        "Sharpe Ratio": "Return relative to daily variability.",
        "Max Drawdown": "Largest peak-to-trough performance loss.",
        "Final Value": "Account value at the end of the simulation.",
    }

    def label_text(label):
        if show_tooltips and label in labels:
            return f'<span title="{labels[label]}">{label}</span>'
        return label

    columns = st.columns(6)
    values = [
        ("Total Return", _format_percent(stats.get("total_return"))),
        ("Total Contributed", f"${stats.get('total_contributions', 0):,.2f}"),
        ("Max Drawdown", _format_percent(stats.get("max_drawdown"))),
        ("Final Value", f"${stats.get('final_value', 0):,.2f}"),
        (
            "Annualized Volatility",
            _format_percent(stats.get("annualized_volatility")),
        ),
        ("Sharpe Ratio", _format_number(stats.get("sharpe_ratio"))),
    ]
    for column, (label, value) in zip(columns, values):
        column.markdown(label_text(label), unsafe_allow_html=show_tooltips)
        column.write(value)


def _format_percent(value):
    return f"{value:.2%}" if value is not None else "N/A"


def _format_number(value):
    return f"{value:.2f}" if value is not None else "N/A"


def render_shock_card(stats, strategy_name):
    drawdown_value = stats.get("max_drawdown")
    if drawdown_value is None:
        st.info(f"{strategy_name} has no valid drawdown result for this period.")
        return
    drawdown = float(drawdown_value)
    if drawdown < -0.20:
        recovery = -drawdown / (1 + drawdown)
        st.error(f"{strategy_name} had a historical drawdown of {drawdown:.2%}.")
        st.write(f"A {recovery:.2%} gain would be needed to recover from that loss.")
    elif drawdown < -0.10:
        st.warning(f"{strategy_name} had a historical drawdown of {drawdown:.2%}.")


def render_concept_card(
    title,
    value=None,
    simple="",
    example="",
    quant="",
    calculation=None,
    so_what=None,
    key=None,
):
    heading = f"{title} — {value}" if value is not None else title
    st.markdown(f"### {heading}")
    with st.expander("Explain this"):
        st.markdown("**Simple**")
        st.write(simple)
        st.markdown("**Example**")
        st.write(example)
        st.markdown("**Quant**")
        st.write(quant)

        if calculation:
            base_key = f"show_calc_{key or title.replace(' ', '_')[:40]}"
            used_keys = st.session_state.get("_used_widget_keys", [])
            widget_key = base_key
            number = 1
            while widget_key in used_keys:
                widget_key = f"{base_key}_{number}"
                number += 1
            used_keys.append(widget_key)
            st.session_state["_used_widget_keys"] = used_keys
            if st.checkbox("Show calculation", key=widget_key):
                st.code(calculation)

        st.markdown("**Why it matters**")
        st.write(so_what or "Use this metric with the other results and assumptions.")


def render_educational_footer():
    st.divider()
    st.subheader("Algorithmic Literacy Takeaways")
    st.markdown(
        "- Compare returns with risk measures such as drawdown.\n"
        "- Machine-learning signals can be wrong.\n"
        "- A historical backtest does not predict future performance.\n"
        "- This app is a simulation, not financial advice."
    )
    st.caption("Built by students for the Congressional App Challenge")


def render_beginner_explanation(results_dict, ticker, show_tooltips=True):
    st.markdown(f"### Beginner Summary for {ticker}")
    st.write("Compare the ending balance with the amount contributed.")
    if show_tooltips:
        st.caption(
            "Investment return and drawdown exclude deposits; the account value includes them."
        )

    for name, (_, stats) in results_dict.items():
        st.markdown(f"**{name}**")
        st.write(f"Final value: ${stats.get('final_value', 0):,.2f}")
        st.write(f"Total contributed: ${stats.get('total_contributions', 0):,.2f}")
        st.write(
            "Investment return, excluding deposits: "
            + _format_percent(stats.get("total_return"))
        )
        st.write(
            "Maximum drawdown: " + _format_percent(stats.get("max_drawdown"))
        )


def render_quant_metrics(stats):
    st.markdown("### Quant Metrics")
    display_metrics(stats)
    st.write(
        "Sharpe and volatility use daily investment returns. Drawdown excludes deposits. Undefined metrics are shown as N/A."
    )


def render_ticker_discovery(default_ticker="AAPL"):
    st.sidebar.markdown("### Ticker Discovery")
    pick_mode = st.sidebar.radio(
        "Pick by", ["Category", "Risk Bucket", "Manual"], index=0
    )
    categories = {
        "The Market Average": ["VOO", "SPY", "VTI"],
        "Tech Giants": ["AAPL", "MSFT", "GOOGL"],
        "Everyday Brands": ["WMT", "KO", "PG"],
    }
    risk_buckets = {
        "Slow & Steady": ["VOO", "VTI"],
        "Balanced": ["VTI", "SPY"],
        "High Growth": ["QQQ", "TSLA", "ARKK"],
    }

    if pick_mode == "Category":
        category = st.sidebar.selectbox("Category", list(categories))
        ticker = st.sidebar.selectbox("Pick an example", categories[category])
    elif pick_mode == "Risk Bucket":
        bucket = st.sidebar.selectbox("Risk Profile", list(risk_buckets))
        full_basket = st.sidebar.checkbox("Use full basket", value=True)
        if full_basket:
            ticker = ",".join(risk_buckets[bucket])
        else:
            ticker = st.sidebar.selectbox(
                "Representative ETF/Stock", risk_buckets[bucket]
            )
    else:
        ticker = st.sidebar.text_input("Stock Ticker", value=default_ticker)

    with st.sidebar.expander("Why these choices?"):
        st.write("A basket can spread company-specific risk, but it can still lose value.")
    return ticker


__all__ = [
    "display_metrics",
    "plot_drawdown",
    "plot_equity_curve",
    "plot_inflation_vs_sp500",
    "render_beginner_explanation",
    "render_educational_footer",
    "render_investing_guide",
    "render_quant_metrics",
    "render_resource_library",
    "render_risk_scatter",
    "render_shock_card",
    "render_ticker_discovery",
    "simulate_1000_from_date",
]