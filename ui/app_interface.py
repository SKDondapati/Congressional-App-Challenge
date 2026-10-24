import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from backtest.engine import calculate_stats, run_simulation
from analysis.comparison import compare_results, largest_drawdown_strategies
from data.data_manager import (
    MarketDataError,
    clean_price_data,
    download_market_data,
    download_market_data_multi,
)
from strategies.benchmark import buy_hold_strategy
from strategies.ml_predictor import ml_predictor_strategy
from strategies.moving_average import moving_average_strategy
from ui.charts import (
    plot_drawdown,
    plot_equity_curve,
    plot_inflation_vs_sp500,
    render_risk_scatter,
    simulate_1000_from_date,
)
from ui.components import (
    display_metrics,
    render_beginner_explanation,
    render_educational_footer,
    render_quant_metrics,
    render_shock_card,
    render_ticker_discovery,
)
from ui.education import render_investing_guide, render_resource_library
from ui.explain_mode import show_metric_explainers
from ui.i18n import t
from ui.lab_page import render_lab_page
from ui.experiment import ExperimentConfig

st.set_page_config(page_title="QuantLit - Algorithmic Literacy Lab", layout="wide")


def generate_insights(stats, results=None, starting_amount=None):
    """Return 2-3 short 'What did I learn?' bullets derived from stats/results."""
    insights = []
    if not stats:
        return insights

    fv = stats.get("final_value")
    sv = starting_amount
    tr = stats.get("total_return")
    md = stats.get("max_drawdown")
    sr = stats.get("sharpe_ratio")

    if fv is not None and stats.get("total_contributions") is not None:
        contributed = stats["total_contributions"]
        insights.append(
            f"The account ended at ${fv:,.2f} after ${contributed:,.2f} was contributed."
        )

    # 2: return vs drawdown
    if tr is not None and md is not None:
        insights.append(
            f"Time-weighted investment return, excluding deposits, was {tr:.2%}; worst drawdown was {md:.2%}."
        )

    # 3: Sharpe or volatility hint
    if sr is not None:
        insights.append(
            f"Sharpe ratio was {sr:.2f}; it summarizes return relative to daily variability, but does not decide which investment is right for you."
        )
    else:
        insights.append("Sharpe ratio was not defined for this return series.")

    # limit to 3 insights
    return insights[:3]


def safe_rerun():
    # Compatibility wrapper for streamlit rerun across versions
    try:
        if hasattr(st, "experimental_rerun"):
            st.experimental_rerun()
        elif hasattr(st, "rerun"):
            st.rerun()
    except Exception:
        # If rerun isn't available, do nothing
        return


@st.cache_data(ttl=3600, show_spinner=False)
def load_market_data(ticker, start_date, end_date):
    if "," in ticker:
        raw = download_market_data_multi(ticker, start_date, end_date)
    else:
        raw = download_market_data(ticker, start_date, end_date)
    return clean_price_data(raw)

# --- Sidebar ---
st.sidebar.title("QuantLit")
st.sidebar.markdown("### Navigation")

# Main navigation
page = st.sidebar.radio(
    "Go to",
    ["Prediction Lab", "Backtest Simulator", "Investing Guide", "Methodology", "Resources"],
)

# Only show mode selection if on Backtest Simulator
if page == "Backtest Simulator":
    mode = st.sidebar.radio("Dashboard View", ["Beginner Mode", "Quant Mode"])

    st.sidebar.markdown("### Strategy Settings")
    # Replace raw text input with a categorized discovery UI to help beginners
    default_t = st.session_state.get("suggested_ticker", "AAPL")
    ticker = render_ticker_discovery(default_ticker=default_t)
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
        language = st.sidebar.selectbox("Language", ["English", "Spanish", "Hindi"], index=0)
        st.session_state["language"] = language

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

    # Interactive experiment controls: starting amount, monthly contributions, horizon
    st.sidebar.markdown("### Experiment Controls")
    starting_amount = st.sidebar.number_input("Starting amount ($)", value=10000, step=100, min_value=0)
    monthly_contribution = st.sidebar.number_input("Monthly contribution ($)", value=0, step=50, min_value=0)
    use_horizon = st.sidebar.checkbox("Set start by horizon (years)", value=False)
    if use_horizon:
        horizon_years = st.sidebar.slider("Investment horizon (years)", 1, 40, 3)
    else:
        horizon_years = None

    # Simulation assumptions (help users understand modeling choices)
    with st.sidebar.expander("ⓘ Simulation assumptions", expanded=False):
        st.markdown(
            """
        - Contributions are added before returns on the first trading day of each later month in the selected period.
        - No transaction costs or fees are modeled here (the Prediction Lab lets you add them).
        - Dividends are included only if present in the price series used (Close prices may already reflect total return in ETF data).
        - Returns are nominal (not inflation-adjusted) unless you adjust inputs externally.
        - Missing trading days are handled by aligning to available trading dates.
        """
        )

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

    # Run button; also allow auto-run via session_state when a goal card triggers an experiment.
    # Results stay on screen after later clicks (e.g. "Run variant"), because Streamlit reruns the
    # whole script on every click and a button is only True for one rerun.
    fresh_run = bool(
        st.sidebar.button("Run Backtest", width="stretch") or st.session_state.get("auto_run", False)
    )
    run_btn = fresh_run or st.session_state.get("active_run") is not None

# --- Main Panel ---
if page == "Backtest Simulator":
    if mode == "Beginner Mode":
        st.title("QuantLit")
        st.caption("Learn how investing works without risking real money.")
    else:
        st.title("QuantLit: Algorithmic Literacy Lab")
        st.caption("Test trading strategies on real historical data.")

    if run_btn:
        if fresh_run:
            # If a quick-run was triggered by the experiment builder, consume its params
            run_params = st.session_state.pop("run_params", None)
            if run_params:
                starting_amount = run_params.get("starting_amount", starting_amount)
                monthly_contribution = run_params.get("monthly_contribution", monthly_contribution)
                if run_params.get("horizon_years") is not None:
                    use_horizon = True
                    horizon_years = run_params.get("horizon_years")
                ticker = run_params.get("ticker", ticker)
                strategy_choice = run_params.get("strategy", strategy_choice)
            # Remember exactly what was run, so later clicks redraw the same experiment.
            st.session_state["active_run"] = {
                "ticker": ticker,
                "start_date": start_date,
                "end_date": end_date,
                "starting_amount": starting_amount,
                "monthly_contribution": monthly_contribution,
                "use_horizon": use_horizon,
                "horizon_years": horizon_years,
                "strategy_choice": strategy_choice,
                "short_window": short_window,
                "long_window": long_window,
            }
        else:
            saved = st.session_state["active_run"]
            ticker = saved["ticker"]
            start_date = saved["start_date"]
            end_date = saved["end_date"]
            starting_amount = saved["starting_amount"]
            monthly_contribution = saved["monthly_contribution"]
            use_horizon = saved["use_horizon"]
            horizon_years = saved["horizon_years"]
            strategy_choice = saved["strategy_choice"]
            short_window = saved["short_window"]
            long_window = saved["long_window"]

        if st.button("← Start a new experiment"):
            st.session_state.pop("active_run", None)
            safe_rerun()

        # clear auto_run so it doesn't repeat
        if st.session_state.get("auto_run", False):
            st.session_state["auto_run"] = False
        with st.spinner(f"Loading data for {ticker}..."):
            # Support single ticker or baskets (list or comma-separated)
            # If user specified a horizon, override start_date accordingly
            if use_horizon and horizon_years is not None:
                end_dt = pd.to_datetime(end_date)
                start_date = end_dt - pd.DateOffset(years=int(horizon_years))

            if pd.Timestamp(start_date) > pd.Timestamp(end_date):
                st.error("Start date must be on or before end date.")
                st.stop()
            ticker = ",".join(ticker) if isinstance(ticker, (list, tuple)) else ticker
            try:
                data = load_market_data(
                    ticker,
                    start_date.strftime("%Y-%m-%d"),
                    end_date.strftime("%Y-%m-%d"),
                )
            except MarketDataError as error:
                st.error(str(error))
                st.stop()
            if mode == "Beginner Mode":
                st.success(f"Loaded {len(data)} days of data for {ticker}.")
            else:
                st.success(f"Loaded {len(data)} trading days.")
            if len(data) < 2:
                st.error("At least two valid closing prices are needed for a backtest.")
                st.stop()

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
            ml_signals = ml_predictor_strategy(data)
            prediction_dates = ml_signals.index[
                ml_signals["evaluation_prediction"]
            ]
            evaluation_start = None
            if len(prediction_dates) > 0:
                first_prediction = data.index.get_loc(prediction_dates[0])
                if first_prediction + 1 < len(data):
                    evaluation_start = data.index[first_prediction + 1]
            if evaluation_start is None:
                st.warning(
                    "There is not enough history for an out-of-sample ML test. "
                    "The ML result is excluded from this comparison."
                )
                strategies.pop("ML Predictor")

            results_dict = {}
            for name, (func, kwargs) in strategies.items():
                with st.spinner(f"Running {name}..."):
                    if name == "ML Predictor":
                        signals = ml_signals
                    else:
                        signals = func(data, **kwargs) if kwargs else func(data)
                    sim = run_simulation(
                        data,
                        signals,
                        starting_money=starting_amount,
                        monthly_contribution=monthly_contribution,
                        start_date=evaluation_start,
                    )
                    stats = calculate_stats(sim)
                    results_dict[name] = (sim, stats)

            st.subheader("Same-period results")
            st.dataframe(compare_results(results_dict), hide_index=True)

            if mode == "Beginner Mode":
                st.info(
                    "Want to test your intuition? Open the **Prediction Lab** in the sidebar "
                    "and guess the result before you see it."
                )

            if mode == "Beginner Mode":
                st.subheader("How did each strategy perform?")
                render_beginner_explanation(
                    results_dict, ticker, show_tooltips=beginner_jargon
                )
                # show concept cards for each strategy to explain key metrics
                for name, (sim, stats) in results_dict.items():
                    st.markdown(f"**{name} — Explanation**")
                    show_metric_explainers(stats, results=sim, starting_amount=starting_amount, start_date=start_date)
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

            if mode == "Beginner Mode" and "Buy & Hold" in results_dict:
                st.subheader("What if the market drops?")
                st.caption(
                    "This uses the largest actual buy-and-hold decline in the "
                    "selected test period. It is one historical example, not a forecast."
                )
                benchmark_results = results_dict["Buy & Hold"][0]
                benchmark_path = benchmark_results["performance_index"]
                benchmark_drawdown = benchmark_path / benchmark_path.cummax() - 1
                trough_date = benchmark_drawdown.idxmin()
                trough_position = benchmark_results.index.get_loc(trough_date)
                if trough_position > 0 and benchmark_drawdown.loc[trough_date] < 0:
                    through_trough = benchmark_path.iloc[: trough_position + 1]
                    peak_date = through_trough.idxmax()
                    strategy_names = list(results_dict)
                    pair_columns = st.columns(2)
                    with pair_columns[0]:
                        first_strategy = st.selectbox(
                            "First strategy",
                            strategy_names,
                            key="drawdown_strategy_one",
                        )
                    with pair_columns[1]:
                        second_strategy = st.selectbox(
                            "Second strategy",
                            strategy_names,
                            index=min(1, len(strategy_names) - 1),
                            key="drawdown_strategy_two",
                        )

                    outcomes = {}
                    for name in [first_strategy, second_strategy]:
                        period_returns = results_dict[name][0].loc[
                            peak_date:trough_date, "strategy_return"
                        ]
                        outcomes[name] = float(
                            1000 * (1 + period_returns).prod()
                        )
                    st.write(
                        f"Observed decline: {peak_date.date()} to {trough_date.date()} "
                        f"({benchmark_drawdown.loc[trough_date]:.1%})."
                    )
                    st.write(
                        f"A $1,000 starting balance ended at "
                        f"${outcomes[first_strategy]:,.2f} with {first_strategy} "
                        f"and ${outcomes[second_strategy]:,.2f} with {second_strategy}."
                    )
                else:
                    st.info("No market decline occurred in the selected test period.")

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
                        # Beginner prediction exercise: ask before revealing
                        if mode == "Beginner Mode":
                            st.markdown(
                                f"If you invested $1,000 on {crisis_date.date()}, what percent gain would you need to recover from a 40% loss?"
                            )
                            choice = st.radio(
                                "Pick one:",
                                ["40%", "50%", "66.7%", "100%"],
                                index=0,
                            )
                            if st.button("Reveal answer"):
                                correct = 1 / (1 - 0.4) - 1
                                st.success(f"Correct answer: {correct:.1%} ({correct:.1%})")
                                st.markdown(
                                    "A 40% drop requires about a 66.7% gain to get back to even."
                                )

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
                evaluation_start = None
                if strategy_choice == "ML Predictor":
                    prediction_dates = signals.index[
                        signals["evaluation_prediction"]
                    ]
                    if len(prediction_dates) == 0:
                        st.warning(
                            "There is not enough history for an out-of-sample ML test. "
                            "Choose another strategy or a longer date range."
                        )
                        st.stop()
                    first_prediction = data.index.get_loc(prediction_dates[0])
                    if first_prediction + 1 >= len(data):
                        st.warning("There are no trading days after the ML test begins.")
                        st.stop()
                    evaluation_start = data.index[first_prediction + 1]
                results = run_simulation(
                    data,
                    signals,
                    starting_money=starting_amount,
                    monthly_contribution=monthly_contribution,
                    start_date=evaluation_start,
                )
                stats = calculate_stats(results)
                # record experiment summary in session history
                ex_hist = st.session_state.get("experiments", [])
                summary = {
                    "name": name,
                    "ticker": ticker,
                    "starting_amount": starting_amount,
                    "monthly_contribution": monthly_contribution,
                    "horizon_years": horizon_years,
                    "final_value": stats.get("final_value", None),
                    "total_return": stats.get("total_return", None),
                    "stats": stats,
                    "results": results,
                    "created_at": pd.Timestamp.now().isoformat(),
                }
                if fresh_run:  # don't re-save the same experiment on every redraw
                    ex_hist.append(summary)
                    st.session_state["experiments"] = ex_hist

            if mode == "Beginner Mode":
                st.subheader(f"Your results using {name}")
                render_beginner_explanation(
                    {name: (results, stats)}, ticker, show_tooltips=beginner_jargon
                )
                # HERO result
                st.markdown("## Your hypothetical investment")
                sv = float(starting_amount)
                fv = float(stats.get("final_value", 0.0))
                tr = stats.get("total_return", 0.0)
                contributed = stats.get("total_contributions", sv)
                st.markdown(f"### ${contributed:,.0f} contributed → ${fv:,.0f}")
                st.write(f"Investment return, excluding deposits: {tr:.2%}")
                st.caption("This is a historical simulation, not a prediction of future performance.")

                # Show Data
                with st.expander("Show the data (yearly returns)"):
                    try:
                        yearly = (
                            (1 + results["strategy_return"])
                            .resample("YE")
                            .prod()
                            .sub(1)
                        )
                        df_yearly = yearly.to_frame(name="annual_return")
                        df_yearly["annual_return"] = df_yearly["annual_return"].map(lambda x: f"{x:.2%}")
                        st.table(df_yearly)
                        st.write("Notice that the average does not describe each year.")
                    except Exception:
                        st.info("Yearly data not available for this series.")

                # Show Math
                with st.expander("Show the math"):
                    try:
                        days = (results.index[-1] - results.index[0]).days
                        years = days / 365.25 if days > 0 else None
                        cagr = stats.get("annualized_return")
                        st.markdown("**Investment return** = product(1 + daily strategy return) - 1")
                        st.markdown("**CAGR** = (1 + investment return)^(1 / years) - 1")
                        st.write(f"Years: {years:.1f}" if years is not None else "Years: N/A")
                        if cagr is not None:
                            st.write(f"Annualized investment return (CAGR): {cagr:.2%}")
                        else:
                            st.info("CAGR is undefined for this return series or period.")
                    except Exception:
                        st.info("Could not compute math for this experiment.")

                # Change one variable (now supports time horizon)
                st.markdown("---")
                st.subheader("Try changing one variable")
                var = st.selectbox(
                    "Choose a variable to change:",
                    ["Starting amount", "Monthly contribution", "Time horizon (years)"],
                )
                # defaults
                new_start = sv
                new_monthly = monthly_contribution
                new_horizon = None
                if var == "Starting amount":
                    new_start = st.number_input("New starting amount ($)", value=int(sv), step=100)
                elif var == "Monthly contribution":
                    new_monthly = st.number_input(
                        "New monthly contribution ($)", value=int(monthly_contribution), step=50
                    )
                else:
                    try:
                        days = (data.index[-1] - data.index[0]).days
                        current_years = max(1, int(days / 365.25))
                    except Exception:
                        current_years = 5
                    new_horizon = st.slider("New time horizon (years)", 1, 40, value=current_years)

                if st.button("Run variant"):
                    # Prepare variant data/signals. If horizon changed, slice data and recompute signals.
                    variant_data = data
                    if new_horizon is not None:
                        end_dt = data.index[-1]
                        candidate_start = end_dt - pd.DateOffset(years=int(new_horizon))
                        if candidate_start > data.index[0]:
                            variant_data = data.loc[candidate_start:]

                    # Recompute signals if we sliced the data
                    try:
                        new_signals = func(variant_data, **kwargs) if kwargs else func(variant_data)
                    except Exception:
                        new_signals = signals

                    new_res = run_simulation(
                        variant_data, new_signals, starting_money=new_start, monthly_contribution=new_monthly
                    )
                    new_stats = calculate_stats(new_res)

                    # show comparison
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("**Original**")
                        st.write(f"Final value: ${fv:,.2f}")
                        st.write(f"Total return: {tr:.2%}")
                        drawdown = stats.get("max_drawdown")
                        st.write(
                            "Max drawdown: "
                            + (f"{drawdown:.2%}" if drawdown is not None else "N/A")
                        )
                    with col2:
                        st.markdown("**Variant**")
                        nf = new_stats.get("final_value", 0.0)
                        nt = new_stats.get("total_return", 0.0)
                        st.write(f"Final value: ${nf:,.2f}")
                        st.write(f"Total return: {nt:.2%}")
                        new_drawdown = new_stats.get("max_drawdown")
                        st.write(
                            "Max drawdown: "
                            + (
                                f"{new_drawdown:.2%}"
                                if new_drawdown is not None
                                else "N/A"
                            )
                        )
                    st.markdown("---")
                    diff = nf - fv
                    st.write(f"Difference: ${diff:,.2f}")

                    # short learning summary
                    learn = []
                    if new_start != sv:
                        learn.append(f"Changed starting amount from ${int(sv):,} to ${int(new_start):,}.")
                    if new_monthly != monthly_contribution:
                        learn.append(
                            f"Changed monthly contribution from ${int(monthly_contribution):,} to ${int(new_monthly):,}."
                        )
                    if new_horizon is not None:
                        learn.append(f"Changed time horizon to {int(new_horizon)} years.")
                    if learn:
                        st.markdown("**What changed:**")
                        for l in learn:
                            st.write(f"- {l}")

                # concept explainers with context
                show_metric_explainers(stats, results=results, starting_amount=starting_amount, start_date=start_date)
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

            # My Experiments: history and compare
            def money(x):
                try:
                    return f"${int(x):,}"
                except Exception:
                    try:
                        return f"${float(x):,.2f}"
                    except Exception:
                        return str(x)

            with st.expander("My Experiments (history & compare)", expanded=False):
                ex_hist = st.session_state.get("experiments", [])
                if not ex_hist:
                    st.info("No experiments recorded yet. Run an experiment to save it here.")
                else:
                    # Show a compact list of experiments
                    for i, e in enumerate(reversed(ex_hist)):
                        idx = len(ex_hist) - 1 - i
                        # pretty card
                        created = e.get("created_at")
                        try:
                            created_fmt = pd.to_datetime(created).strftime("%Y-%m-%d %H:%M")
                        except Exception:
                            created_fmt = created or ""

                        st.markdown(f"**{money(e.get('starting_amount'))} → {e.get('final_value') and money(e.get('final_value')) or '—'} — {e.get('name')}**")
                        st.write(f"{e.get('ticker')} · {e.get('horizon_years') or 'varies'} years · ${int(e.get('monthly_contribution',0))}/mo")
                        st.write(f"Saved: {created_fmt}")
                        # inline actions: rename, delete, export
                        cols_a = st.columns([2, 1, 1])
                        with cols_a[0]:
                            new_name = st.text_input(f"Name #{idx}", value=e.get("name"), key=f"exp_name_{idx}")
                            if new_name != e.get("name"):
                                ex_hist[idx]["name"] = new_name
                                st.session_state["experiments"] = ex_hist
                        with cols_a[1]:
                            if st.button("Delete", key=f"exp_delete_{idx}"):
                                ex_hist.pop(idx)
                                st.session_state["experiments"] = ex_hist
                                safe_rerun()
                        with cols_a[2]:
                            # export single experiment as JSON
                            import json

                            exp_json = json.dumps(e, default=str, indent=2)
                            st.download_button(
                                label="Export JSON",
                                data=exp_json,
                                file_name=f"experiment_{idx}.json",
                                mime="application/json",
                                key=f"exp_export_{idx}",
                            )
                        st.markdown("---")

                    # Select experiments to compare
                    indices = list(range(len(ex_hist)))
                    left = st.selectbox("Left experiment", indices, format_func=lambda i: f"#{i} — {ex_hist[i].get('name')}")
                    right = st.selectbox("Right experiment", indices, index=max(0, len(indices) - 1), format_func=lambda i: f"#{i} — {ex_hist[i].get('name')}")

                    if left == right:
                        st.warning("Pick two different experiments to compare.")
                    else:
                        e1 = ex_hist[left]
                        e2 = ex_hist[right]

                        def compute_cagr_from_results(entry):
                            res = entry.get("results")
                            if res is None:
                                return None
                            try:
                                return entry.get("stats", {}).get("annualized_return")
                            except Exception:
                                return None

                        c1 = compute_cagr_from_results(e1)
                        c2 = compute_cagr_from_results(e2)

                        cols = st.columns(2)
                        with cols[0]:
                            st.markdown(f"### #{left} — {e1.get('name')}")
                            st.write(f"Ticker: {e1.get('ticker')}")
                            st.write(f"Start: {money(e1.get('starting_amount'))}")
                            st.write(f"Monthly: ${int(e1.get('monthly_contribution',0))}")
                            st.write(f"Final value: ${e1.get('final_value'):,}")
                            return_value = e1.get("total_return")
                            st.write(
                                "Investment return: "
                                + (f"{return_value:.2%}" if return_value is not None else "N/A")
                            )
                            if c1 is not None:
                                st.write(f"CAGR: {c1:.2%}")
                            drawdown_value = e1.get("stats", {}).get("max_drawdown")
                            st.write(
                                "Max drawdown: "
                                + (
                                    f"{drawdown_value:.2%}"
                                    if drawdown_value is not None
                                    else "N/A"
                                )
                            )
                            # insights
                            ins1 = generate_insights(e1.get('stats', {}), results=e1.get('results'), starting_amount=e1.get('starting_amount'))
                            if ins1:
                                st.markdown("**What did I learn:**")
                                for it in ins1:
                                    st.write(f"- {it}")
                        with cols[1]:
                            st.markdown(f"### #{right} — {e2.get('name')}")
                            st.write(f"Ticker: {e2.get('ticker')}")
                            st.write(f"Start: {money(e2.get('starting_amount'))}")
                            st.write(f"Monthly: ${int(e2.get('monthly_contribution',0))}")
                            st.write(f"Final value: ${e2.get('final_value'):,}")
                            return_value = e2.get("total_return")
                            st.write(
                                "Investment return: "
                                + (f"{return_value:.2%}" if return_value is not None else "N/A")
                            )
                            if c2 is not None:
                                st.write(f"CAGR: {c2:.2%}")
                            drawdown_value = e2.get("stats", {}).get("max_drawdown")
                            st.write(
                                "Max drawdown: "
                                + (
                                    f"{drawdown_value:.2%}"
                                    if drawdown_value is not None
                                    else "N/A"
                                )
                            )
                            ins2 = generate_insights(e2.get('stats', {}), results=e2.get('results'), starting_amount=e2.get('starting_amount'))
                            if ins2:
                                st.markdown("**What did I learn:**")
                                for it in ins2:
                                    st.write(f"- {it}")

                        # Show equity curves if both have results
                        if e1.get("results") is not None and e2.get("results") is not None:
                            st.markdown("#### Equity Curves")
                            plot_equity_curve(e1.get("results"), f"Exp #{left}: {e1.get('name')}")
                            plot_equity_curve(e2.get("results"), f"Exp #{right}: {e2.get('name')}")

                        # export both
                        import json
                        all_json = json.dumps([e1, e2], default=str, indent=2)
                        st.download_button(
                            label="Export both as JSON",
                            data=all_json,
                            file_name=f"experiments_{left}_{right}.json",
                            mime="application/json",
                            key=f"export_pair_{left}_{right}",
                        )

    else:
        # If the user hasn't run yet, show a goal-first onboarding for Beginner Mode
        if mode == "Beginner Mode":
            st.subheader("What do you want to learn?")
            cols = st.columns(3)
            goals = [
                (t("Grow money over time"), t("See how compounding works"), "VTI"),
                (t("Understand risk"), t("See drawdowns and stress tests"), "VOO"),
                (t("Compare investments"), t("Compare investment strategies"), "VTI"),
            ]
            for i, (title_g, desc, suggestion) in enumerate(goals):
                with cols[i]:
                    st.markdown(f"### {title_g}")
                    st.write(desc)
                    if st.button(f"Use this goal: {title_g}", key=f"goal_{i}"):
                        # Set an experiment template (does not run immediately)
                        st.session_state["selected_goal"] = title_g
                        st.session_state["suggested_ticker"] = suggestion
                        # prepare a small ExperimentConfig tailored to each goal
                        if title_g == t("Grow money over time"):
                            exp = ExperimentConfig.preset_for_goal("Grow money over time", suggestion)
                        elif title_g == t("Understand risk"):
                            exp = ExperimentConfig.preset_for_goal("Understand risk", suggestion)
                        else:
                            exp = ExperimentConfig.preset_for_goal("Compare investments", suggestion)
                        st.session_state["experiment_template"] = exp.to_dict()
                        safe_rerun()

            st.markdown("---")
            # If a goal was selected, show the experiment builder (user must click Run)
            tmpl = st.session_state.get("experiment_template")
            if tmpl:
                exp = ExperimentConfig.from_dict(tmpl)
                st.subheader("Let's build your experiment")
                st.write(f"Goal: {st.session_state.get('selected_goal')}")
                st.write(f"Lesson: {exp.lesson}")

                col_a, col_b = st.columns(2)
                with col_a:
                    ea = st.number_input(t("Starting amount ($)"), value=int(exp.starting_amount), step=100)
                    ec = st.number_input(t("Monthly contribution ($)"), value=int(exp.monthly_contribution), step=50)
                with col_b:
                    eh = st.slider(t("Time horizon (years)"), 1, 40, value=int(exp.horizon_years or 10))
                    et = st.text_input("Suggested ticker", value=exp.ticker)

                if st.button(t("Run Experiment")):
                    # update experiment object and store run params
                    exp.starting_amount = ea
                    exp.monthly_contribution = ec
                    exp.horizon_years = eh
                    exp.ticker = et
                    st.session_state["experiment_template"] = exp.to_dict()
                    st.session_state["run_params"] = exp.to_dict()
                    st.session_state["auto_run"] = True
                    safe_rerun()

                st.markdown("---")
                st.info("Adjust the experiment parameters above, then click Run Experiment to see results.")
            else:
                st.info("Or configure the ticker and date range in the sidebar and click Run Backtest.")
            # Quick demo runner for judges: prefilled trial that runs immediately
            if st.button(t("Try QuantLit Demo")):
                demo = {
                    "starting_amount": 10000,
                    "monthly_contribution": 100,
                    "horizon_years": 10,
                    "ticker": "VTI",
                    "strategy": "Buy & Hold",
                }
                st.session_state["run_params"] = demo
                st.session_state["auto_run"] = True
                safe_rerun()
        else:
            st.info("Configure your strategy in the sidebar and click Run Backtest.")
            st.markdown("""
            ### Quick Start
            1. Enter a stock ticker
            2. Pick a date range
            3. Choose a strategy or compare all
            4. Click Run Backtest
            """)

elif page == "Prediction Lab":
    render_lab_page(load_market_data)
elif page == "Investing Guide":
    render_investing_guide()
elif page == "Methodology":
    st.title("Methodology & Assumptions")
    st.markdown(
        "This page explains how QuantLit runs historical experiments and the key modeling choices."
    )
    with st.expander("Data sources"):
        st.markdown(
            "We primarily use historical price data from Yahoo Finance via `yfinance`. ETF close prices may already reflect total return; individual stocks may not include dividends."
        )
    with st.expander("Contribution timing"):
        st.markdown(
            "Monthly contributions are added before returns on the first trading day of each later month in the selected period. The initial balance is present on the first selected date."
        )
    with st.expander("Fees & taxes"):
        st.markdown(
            "We do not model transaction costs, management fees, or taxes. Results are gross nominal returns; this app does not estimate net returns after costs."
        )
    with st.expander("Nominal vs Real returns"):
        st.markdown(
            "Results are nominal (not inflation-adjusted) by default. The comparison chart uses an example 2% inflation assumption, not actual inflation for the selected dates."
        )
    with st.expander("Missing data & alignment"):
        st.markdown(
            "We align series to available trading dates and drop missing days. When combining multiple tickers, we compute returns per asset and then average returns (equal-weight) before compounding — this prevents raw price averaging bias."
        )
    with st.expander("Limitations & disclaimer"):
        st.markdown(
            "Historical simulations are educational tools, not investment advice. Past performance is not a guarantee of future results."
        )

elif page == "Resources":
    render_resource_library()
