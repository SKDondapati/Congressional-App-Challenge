import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def plot_equity_curve(results_df, strategy_name, palette=None):
    if palette is None:
        primary = "#1f77b4"
        benchmark = "gray"
        stress = "#d62728"
    else:
        primary = palette.get("primary", "#1f77b4")
        benchmark = palette.get("benchmark", "gray")
        stress = palette.get("stress", "#d62728")

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=results_df.index,
            y=results_df["portfolio_value"],
            name=f"{strategy_name} Strategy",
            line={"color": primary, "width": 3},
        )
    )
    fig.add_trace(
        go.Scatter(
            x=results_df.index,
            y=results_df["buy_hold_value"],
            name="Buy & Hold Benchmark",
            line={"color": benchmark, "width": 2, "dash": "dash"},
        )
    )

    performance = results_df.get("performance_index", results_df["portfolio_value"])
    drawdown = performance / performance.cummax() - 1
    stress_dates = results_df.index[drawdown < -0.15]
    if len(stress_dates) > 0:
        fig.add_vrect(
            x0=stress_dates[0],
            x1=stress_dates[-1],
            fillcolor=stress,
            opacity=0.1,
            layer="below",
            line_width=0,
            annotation_text="Stress Period",
        )

    fig.update_layout(
        title="Portfolio Value Over Time",
        xaxis_title="Date",
        yaxis_title="Portfolio Value ($)",
        hovermode="x",
    )
    st.plotly_chart(fig, width="stretch")
    st.caption(
        f"End value: ${results_df['portfolio_value'].iloc[-1]:,.2f} · "
        f"Peak drawdown: {drawdown.min():.2%}"
    )


def plot_drawdown(results_df, palette=None):
    color = palette.get("stress", "red") if palette else "red"
    performance = results_df.get("performance_index", results_df["portfolio_value"])
    drawdown = performance / performance.cummax() - 1

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=drawdown.index,
            y=drawdown.values * 100,
            fill="tozeroy",
            line={"color": color, "width": 1},
            name="Drawdown %",
        )
    )
    fig.update_layout(
        title="Drawdown Over Time",
        xaxis_title="Date",
        yaxis_title="Drawdown (%)",
        hovermode="x",
    )
    st.plotly_chart(fig, width="stretch")
    st.caption(f"Worst drawdown: {drawdown.min():.2%}")


def render_risk_scatter(results_dict):
    import plotly.express as px

    rows = []
    for name, (_, stats) in results_dict.items():
        rows.append(
            {
                "strategy": name,
                "total_return": stats.get("total_return", 0),
                "sharpe_ratio": stats.get("sharpe_ratio", 0),
                "max_drawdown": stats.get("max_drawdown", 0),
            }
        )
    if not rows:
        st.info("No results to visualize for risk metrics.")
        return

    frame = pd.DataFrame(rows)
    fig = px.scatter(
        frame,
        x="sharpe_ratio",
        y="total_return",
        size=frame["max_drawdown"].abs(),
        hover_name="strategy",
        title="Risk vs Return: Sharpe vs Total Return",
    )
    fig.update_layout(xaxis_title="Sharpe Ratio", yaxis_title="Total Return")
    st.plotly_chart(fig, width="stretch")


def plot_inflation_vs_sp500(
    start_date, end_date, inflation_rate=0.02, index_ticker="SPY"
):
    """Compare an ETF with cash purchasing power under an example inflation rate."""
    import yfinance as yf

    from data.data_manager import MarketDataError, clean_price_data

    try:
        raw = yf.download(
            index_ticker, start=start_date, end=end_date, progress=False
        )
        prices = clean_price_data(raw)["close"]
    except MarketDataError as error:
        st.error(str(error))
        return
    except Exception:
        st.error("Could not download index data for the inflation comparison.")
        return

    prices = prices / prices.iloc[0] * 1000.0
    years = (prices.index - prices.index[0]).days / 365.25
    cash_value = 1000.0 / (1 + inflation_rate) ** years

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=prices.index, y=prices.values, name=index_ticker))
    fig.add_trace(
        go.Scatter(
            x=prices.index,
            y=cash_value,
            name=f"Cash purchasing power ({inflation_rate:.0%} assumed inflation)",
            line={"dash": "dash"},
        )
    )
    fig.update_layout(
        title="Inflation vs Market (starting $1,000)",
        xaxis_title="Date",
        yaxis_title="Value ($)",
    )
    st.plotly_chart(fig, width="stretch")
    st.caption(
        f"The {inflation_rate:.0%} rate is an example, not actual inflation for these dates."
    )


def simulate_1000_from_date(data, start_invest_date):
    if start_invest_date not in data.index:
        start_index = data.index.searchsorted(start_invest_date)
        if start_index >= len(data.index):
            return None
    else:
        start_index = data.index.get_loc(start_invest_date)

    prices = data["close"].iloc[start_index:]
    if prices.empty:
        return None
    return prices / prices.iloc[0] * 1000.0