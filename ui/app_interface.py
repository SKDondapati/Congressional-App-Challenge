import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from backtest.engine import calculate_stats, run_simulation
from data.data_manager import (clean_price_data, download_market_data,
                               download_market_data_multi)
from strategies.benchmark import buy_hold_strategy
from strategies.ml_predictor import ml_predictor_strategy
from strategies.moving_average import moving_average_strategy
from ui.components import (display_metrics, plot_drawdown, plot_equity_curve,
                           plot_inflation_vs_sp500,
                           render_beginner_explanation,
                           render_educational_footer, render_investing_guide,
                           render_quant_metrics, render_resource_library,
                           render_risk_scatter, render_shock_card,
                           render_ticker_discovery, simulate_1000_from_date)

st.set_page_config(page_title="QuantLit - Algorithmic Literacy Lab", layout="wide")

# --- Sidebar ---
st.sidebar.title("QuantLit")
st.sidebar.markdown("### Navigation")

# Main navigation
page = st.sidebar.radio("Go to", ["Backtest Simulator", "Investing Guide", "Resources"])

# Only show mode selection if on Backtest Simulator
if page == "Backtest Simulator":
    mode = st.sidebar.radio("Dashboard View", ["Beginner Mode", "Quant Mode"])

    st.sidebar.markdown("### Strategy Settings")
    # Replace raw text input with a categorized discovery UI to help beginners
    ticker = render_ticker_discovery(default_ticker="AAPL")
    # Beginner-friendly options
    beginner_jargon = False
    # Default plotting palette (used in Quant Mode and as fallback)
    palette = {"primary": "#1f77b4", "benchmark": "gray", "stress": "#d62728"}
    if mode == "Beginner Mode":
        beginner_jargon = st.sidebar.checkbox(
            "Beginner tooltips (translate jargon)", value=True
        )
        # Accessibility & polish options
        st.sidebar.markdown("### Accessibility & Display")
        high_contrast = st.sidebar.checkbox("High contrast display", value=False)
        color_blind = st.sidebar.checkbox("Color-blind friendly palette", value=False)
        language = st.sidebar.selectbox("Language", ["English", "Spanish"], index=0)

        # Build a palette dict for plots
        if high_contrast:
            palette = {
                "primary": "#000000",
                "benchmark": "#666666",
                "stress": "#ff0000",
            }
        elif color_blind:
            palette = {
                "primary": "#0072B2",
                "benchmark": "#E69F00",
                "stress": "#D55E00",
            }
        else:
            palette = {"primary": "#1f77b4", "benchmark": "gray", "stress": "#d62728"}
    start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2020-01-01"))
    end_date = st.sidebar.date_input("End Date", pd.to_datetime("2023-12-31"))

    strategy_choice = st.sidebar.selectbox(
        "Select Strategy",
        ["Moving Average (20/50)", "ML Predictor", "Buy & Hold", "Compare All"],
    )

    if mode == "Quant Mode":
        short_window = (
            st.sidebar.slider("Short MA Window", 5, 50, 20)
            if strategy_choice in ["Moving Average (20/50)", "Compare All"]
            else 20
        )
        long_window = (
            st.sidebar.slider("Long MA Window", 20, 200, 50)
            if strategy_choice in ["Moving Average (20/50)", "Compare All"]
            else 50
        )
    else:
        short_window = 20
        long_window = 50

    run_btn = st.sidebar.button("Run Backtest", width="stretch")

# --- Main Panel ---
if page == "Backtest Simulator":
    if mode == "Beginner Mode":
        st.title("QuantLit")
        st.caption("Learn how investing works without risking real money.")
    else:
        st.title("QuantLit: Algorithmic Literacy Lab")
        st.caption("Test trading strategies on real historical data.")

    if run_btn:
        with st.spinner(f"Loading data for {ticker}..."):
            # Support single ticker or baskets (list or comma-separated)
            if isinstance(ticker, (list, tuple)):
                raw = download_market_data_multi(
                    ticker,
                    start_date.strftime("%Y-%m-%d"),
                    end_date.strftime("%Y-%m-%d"),
                )
            elif isinstance(ticker, str) and "," in ticker:
                raw = download_market_data_multi(
                    ticker,
                    start_date.strftime("%Y-%m-%d"),
                    end_date.strftime("%Y-%m-%d"),
                )
            else:
                raw = download_market_data(
                    ticker,
                    start_date.strftime("%Y-%m-%d"),
                    end_date.strftime("%Y-%m-%d"),
                )
            if raw is None or raw.empty:
                st.error(
                    "No data found for that ticker. Please check the symbol and dates."
                )
                st.stop()
            data = clean_price_data(raw)
            if mode == "Beginner Mode":
                st.success(f"Loaded {len(data)} days of data for {ticker}.")
            else:
                st.success(f"Loaded {len(data)} trading days.")

        if strategy_choice == "Compare All":
            strategies = {
                "Moving Average": (
                    moving_average_strategy,
                    {"short_window": short_window, "long_window": long_window},
                ),
                "ML Predictor": (
                    ml_predictor_strategy,
                    {"lookback": 5, "test_size": 0.2},
                ),
                "Buy & Hold": (buy_hold_strategy, {}),
            }
            results_dict = {}
            for name, (func, kwargs) in strategies.items():
                with st.spinner(f"Running {name}..."):
                    signals = func(data, **kwargs) if kwargs else func(data)
                    sim = run_simulation(data, signals)
                    stats = calculate_stats(sim)
                    results_dict[name] = (sim, stats)

            if mode == "Beginner Mode":
                st.subheader("How did each strategy perform?")
                render_beginner_explanation(
                    results_dict, ticker, show_tooltips=beginner_jargon
                )
            else:
                st.subheader("Strategy Comparison")
                cols = st.columns(len(results_dict))
                for i, (name, (sim, stats)) in enumerate(results_dict.items()):
                    with cols[i]:
                        st.markdown(f"**{name}**")
                        display_metrics(stats)
                        render_shock_card(stats, name)

            st.subheader("Portfolio Value Over Time")
            fig = go.Figure()
            for name, (sim, _) in results_dict.items():
                fig.add_trace(
                    go.Scatter(x=sim.index, y=sim["portfolio_value"], name=name)
                )
            fig.add_trace(
                go.Scatter(
                    x=sim.index,
                    y=sim["buy_hold_value"],
                    name="Buy & Hold Benchmark",
                    line=dict(dash="dash", color="gray"),
                )
            )
            fig.update_layout(
                title="Portfolio Value Comparison",
                xaxis_title="Date",
                yaxis_title="Value ($)",
            )
            # show the comparison chart
            st.plotly_chart(fig, width="stretch")

            if mode == "Quant Mode":
                render_educational_footer()
                # Extra Quant visuals
                st.subheader("Quant Mode: Risk Metrics")
                render_risk_scatter(results_dict)
                st.subheader("Inflation vs Market")
                plot_inflation_vs_sp500(
                    start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
                )
                # Interactive 'What If' crisis slider
                st.subheader("What If? Crisis Time Machine")
                crisis_map = {
                    "2008 Lehman Collapse": "2008-09-15",
                    "COVID Crash 2020": "2020-03-16",
                    "Dotcom 2000 Peak": "2000-03-10",
                }
                crisis_choice = st.selectbox(
                    "Pick a historical crisis", list(crisis_map.keys())
                )
                crisis_date = pd.to_datetime(crisis_map[crisis_choice])
                # If we have single-series data, simulate $1000
                if "close" in data.columns:
                    sim_ser = simulate_1000_from_date(data, crisis_date)
                    if sim_ser is not None:
                        st.markdown(
                            f"If you invested $1,000 on {crisis_date.date()}, here's what would have happened:"
                        )
                        fig = go.Figure()
                        fig.add_trace(
                            go.Scatter(
                                x=sim_ser.index,
                                y=sim_ser.values,
                                name="$1,000 Investment",
                            )
                        )
                        fig.update_layout(
                            title="Crisis Time Machine: $1,000 Invested",
                            xaxis_title="Date",
                            yaxis_title="Value ($)",
                        )
                        st.plotly_chart(fig, width="stretch")
                    else:
                        st.info(
                            "Selected crisis date is outside the available data range for this ticker/basket."
                        )

        else:
            if strategy_choice == "Moving Average (20/50)":
                func = moving_average_strategy
                kwargs = {"short_window": short_window, "long_window": long_window}
                name = f"MA ({short_window}/{long_window})"
            elif strategy_choice == "ML Predictor":
                func = ml_predictor_strategy
                kwargs = {"lookback": 5, "test_size": 0.2}
                name = "ML Predictor"
            else:
                func = buy_hold_strategy
                kwargs = {}
                name = "Buy & Hold"

            with st.spinner(f"Running {name}..."):
                signals = func(data, **kwargs) if kwargs else func(data)
                results = run_simulation(data, signals)
                stats = calculate_stats(results)

            if mode == "Beginner Mode":
                st.subheader(f"Your results using {name}")
                render_beginner_explanation(
                    {name: (results, stats)}, ticker, show_tooltips=beginner_jargon
                )
            else:
                st.subheader(f"{name} Results")
                display_metrics(stats)
                render_shock_card(stats, name)

            col1, col2 = st.columns(2)
            with col1:
                plot_equity_curve(results, name, palette=palette)
            with col2:
                plot_drawdown(results, palette=palette)

            if mode == "Quant Mode":
                render_educational_footer()

    else:
        if mode == "Beginner Mode":
            st.info("Click 'Run Backtest' to see how different strategies perform.")
            st.markdown("""
            ### What is this?
            - You pick a stock and a strategy
            - The app shows you what would have happened if you invested
            - No real money involved
            - Great for learning how the stock market works
            
            ### Where to start?
            1. Type a stock ticker (AAPL, TSLA, SPY)
            2. Pick a date range
            3. Choose a strategy or compare them all
            4. Click Run Backtest
            """)
        else:
            st.info("Configure your strategy in the sidebar and click Run Backtest.")
            st.markdown("""
            ### Quick Start
            1. Enter a stock ticker
            2. Pick a date range
            3. Choose a strategy or compare all
            4. Click Run Backtest
            """)

elif page == "Investing Guide":
    render_investing_guide()

elif page == "Resources":
    render_resource_library()
