"""Prediction-versus-Reality Lab page: predict, run a backtest, compare, and reflect."""

from datetime import date

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from analysis.lab import (
    LIMITS, STRATEGY_MA, STRATEGY_ML, LabError, explain_results, run_lab_experiment, score_prediction,
)
from data.data_manager import MarketDataError, make_practice_data

STRATEGY_COLOR = "#0072B2"  # blue
BENCH_COLOR = "#E69F00"     # orange (blue/orange stays distinguishable for color-blind viewers)
BUY_COLOR = "#009E73"
SELL_COLOR = "#D55E00"
STARTING_MONEY = 10_000

TICKERS = {
    "SPY": "S&P 500 fund (500 big US companies)",
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "TSLA": "Tesla",
    "NVDA": "Nvidia",
    "KO": "Coca-Cola",
    "QQQ": "Nasdaq-100 fund (big tech)",
}

PERIODS = {
    "COVID crash and recovery (2019–2021)": ("2019-01-01", "2021-12-31"),
    "2022 bear market (2021–2023)": ("2021-01-01", "2023-06-30"),
    "Long run (2010–2024)": ("2010-01-01", "2024-12-31"),
    "Last 5 years": (str(date.today().replace(year=date.today().year - 5)), str(date.today())),
    "Custom dates": None,
}

WINDOWS = {
    "Fast: 20-day vs 50-day": (20, 50),
    "Classic: 50-day vs 200-day ('golden cross')": (50, 200),
    "Custom": None,
}

HELP = {
    "ticker": "The short code for a stock or fund. AAPL is Apple; SPY tracks the S&P 500 (500 big US companies).",
    "ma": "Own the stock when the short-term average price is above the long-term average (an uptrend). "
          "Otherwise, hold cash.",
    "ml": "A random-forest model looks at recent price moves and guesses whether tomorrow will be up or down. "
          "It buys when it predicts 'up'. It learns from the first 80% of the period and is tested on the last 20%.",
    "cost": "Fees and the small price difference you lose on each buy or sell. They add up for strategies that "
            "trade a lot.",
    "return": "How much the money grew overall. +50% means $10,000 became $15,000.",
    "drawdown": "The worst drop from a high point to a later low. A 30% drop means at some point you were 30% "
                "below your best value.",
    "cagr": "The steady yearly growth rate that would give the same result. Shown as N/A for tests shorter "
            "than a year, because stretching a few months into a yearly rate is misleading.",
    "sharpe": "Return per unit of bumpiness. Higher is better; below 0 means cash would have done better.",
    "vol": "How much the value bounces around, per year. Higher means a bumpier ride.",
}


def _init_state():
    st.session_state.setdefault("lab_experiments", [])
    st.session_state.setdefault("lab_current", None)


def _setup_and_predict(default_ticker):
    """Step 1 updates live. Step 2 is a form, so the prediction is locked in before results appear."""
    with st.container(border=True):
        st.markdown("### Step 1 · Set up the experiment")
        source = st.radio(
            "Data", ["Real market data", "Practice data (simulated, works offline)"], horizontal=True,
            help="Practice data is randomly generated prices for when the internet or Yahoo Finance is down. "
                 "It is not real history.",
        )
        practice = source.startswith("Practice")
        c1, c2, c3 = st.columns(3)
        with c1:
            if practice:
                ticker = "PRACTICE"
                st.markdown("**Stock or fund**")
                st.caption("Practice mode uses one simulated stock.")
            else:
                options = list(TICKERS) + ["Other…"]
                index = options.index(default_ticker) if default_ticker in TICKERS else 0
                ticker = st.selectbox("Stock or fund", options, index=index, help=HELP["ticker"],
                                      format_func=lambda t: f"{t}: {TICKERS[t]}" if t in TICKERS else t)
                if ticker == "Other…":
                    ticker = st.text_input("Ticker symbol", placeholder="e.g., AMZN").strip().upper()
        with c2:
            period = st.selectbox("Time period", list(PERIODS))
            if PERIODS[period] is None:
                d1, d2 = st.columns(2)
                start = d1.date_input("Start", date(2018, 1, 1), min_value=date(1990, 1, 1), max_value=date.today())
                end = d2.date_input("End", date.today(), min_value=date(1990, 1, 1), max_value=date.today())
            else:
                start, end = PERIODS[period]
        with c3:
            strategy = st.radio("Strategy to test", [STRATEGY_MA, STRATEGY_ML],
                                captions=["Follows price trends", "Machine learning (random forest)"])
        short_w, long_w = 20, 50
        cols = st.columns(2)
        with cols[0]:
            if strategy == STRATEGY_MA:
                win = st.selectbox("Moving-average rule", list(WINDOWS), help=HELP["ma"])
                if WINDOWS[win] is None:
                    w1, w2 = st.columns(2)
                    short_w = int(w1.number_input("Short (days)", 2, 250, 10))
                    long_w = int(w2.number_input("Long (days)", 3, 400, 30))
                else:
                    short_w, long_w = WINDOWS[win]
            else:
                st.caption(HELP["ml"])
        with cols[1]:
            cost_pct = st.slider("Trading cost per trade (%)", 0.0, 1.0, 0.10, 0.05, help=HELP["cost"])

    name = "The AI predictor" if strategy == STRATEGY_ML else "The moving-average rule"
    with st.form("lab_prediction"):
        st.markdown("### Step 2 · Make your prediction")
        st.caption(f"Both approaches start with ${STARTING_MONEY:,}. Lock in your guesses before you see anything.")
        p1, p2, p3 = st.columns(3)
        winner = p1.radio("Which will end with more money?", [name, "Buy and hold"])
        bench_ret = p2.slider("Buy-and-hold total return (%)", -90, 500, 40, 5, help=HELP["return"])
        bench_dd = p3.slider("Buy-and-hold worst drop (%)", 0, 90, 20, 5, help=HELP["drawdown"])
        if strategy == STRATEGY_ML:
            st.caption("Note: for the AI, both approaches are scored only on the last 20% of the period, so guess "
                       "returns for that shorter stretch.")
        reason = st.text_input("Why? (optional)", placeholder="e.g., 'Trend-following should dodge the 2020 crash.'")
        submitted = st.form_submit_button("Lock in my prediction & run the test", type="primary")

    if not submitted:
        return None
    return {
        "practice": practice, "ticker": ticker or "", "start": str(start), "end": str(end),
        "strategy": strategy, "short": short_w, "long": long_w, "cost": cost_pct / 100,
        "prediction": {"winner": "benchmark" if winner == "Buy and hold" else "strategy",
                       "bench_return": bench_ret / 100, "bench_drawdown": bench_dd / 100, "reason": reason},
    }


def _run(cfg, load_market_data):
    if not cfg["practice"] and not cfg["ticker"]:
        st.error("Type a ticker symbol, or pick one from the list.")
        return None
    if cfg["short"] >= cfg["long"]:
        st.error("The short moving average must use fewer days than the long one (for example, 20 and 50).")
        return None
    start, end = pd.Timestamp(cfg["start"]), min(pd.Timestamp(cfg["end"]), pd.Timestamp(date.today()))
    if start >= end:
        st.error("The start date must be before the end date.")
        return None
    try:
        if cfg["practice"]:
            data = make_practice_data(start, end)
        else:
            with st.spinner(f"Downloading {cfg['ticker']} prices from Yahoo Finance…"):
                data = load_market_data(cfg["ticker"], start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
        with st.spinner("Running the experiment…"):
            r = run_lab_experiment(data, cfg["strategy"], cfg["short"], cfg["long"], cfg["cost"], STARTING_MONEY)
    except MarketDataError as error:
        st.error(f"{error} If Yahoo Finance is down, switch to Practice data.")
        return None
    except LabError as error:
        st.error(str(error))
        return None
    r["cfg"] = cfg
    r["score"] = score_prediction(cfg["prediction"], r["s"], r["b"])
    r["notes"] = explain_results(cfg["strategy"], r["s"], r["b"], cfg["cost"], r["yearly"])
    return r


# ------------------------------------------------------------------ charts

def _layout(fig, **kw):
    fig.update_layout(hovermode="x unified", legend=dict(orientation="h", y=1.1),
                      margin=dict(l=10, r=10, t=40, b=10), **kw)
    return fig


def _growth_chart(r, label):
    s_res, b_res = r["strat_res"], r["bench_res"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=b_res.index, y=b_res["portfolio_value"], name="Buy and hold",
                             line=dict(color=BENCH_COLOR, width=2)))
    fig.add_trace(go.Scatter(x=s_res.index, y=s_res["portfolio_value"], name=label,
                             line=dict(color=STRATEGY_COLOR, width=2)))
    change = s_res["holding"].diff().fillna(s_res["holding"])
    # Only mark trades for the moving-average rule; the AI trades too often for markers to be readable.
    if r["cfg"]["strategy"] == STRATEGY_MA:
        for kind, mask, color, symbol in (("Buy", change > 0, BUY_COLOR, "triangle-up"),
                                          ("Sell", change < 0, SELL_COLOR, "triangle-down")):
            pts = s_res[mask]
            fig.add_trace(go.Scatter(x=pts.index, y=pts["portfolio_value"], mode="markers", name=kind,
                                     marker=dict(color=color, symbol=symbol, size=9,
                                                 line=dict(width=1, color="white"))))
    return _layout(fig, yaxis_title="Portfolio value ($)", yaxis_tickprefix="$", yaxis_tickformat=",.0f",
                   height=420)


def _price_chart(r, name):
    sig = r["signals"].loc[r["strat_res"].index[0]:]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=sig.index, y=sig["close"], name=f"{name} price", line=dict(color="#7A7F87")))
    fig.add_trace(go.Scatter(x=sig.index, y=sig["short_ma"], name=f"{r['cfg']['short']}-day average",
                             line=dict(color=STRATEGY_COLOR, width=2)))
    fig.add_trace(go.Scatter(x=sig.index, y=sig["long_ma"], name=f"{r['cfg']['long']}-day average",
                             line=dict(color=BENCH_COLOR, width=2, dash="dash")))
    return _layout(fig, yaxis_title="Price ($)", height=380)


def _drawdown_chart(r, label):
    fig = go.Figure()
    for res, name, color in ((r["bench_res"], "Buy and hold", BENCH_COLOR),
                             (r["strat_res"], label, STRATEGY_COLOR)):
        path = res["performance_index"]
        fig.add_trace(go.Scatter(x=res.index, y=path / path.cummax() - 1, name=name, fill="tozeroy",
                                 line=dict(color=color, width=1.5), opacity=0.5))
    return _layout(fig, yaxis_title="Below previous high", yaxis_tickformat=".0%", height=320)


def _yearly_chart(r, label):
    y = r["yearly"]
    years = [str(i) for i in y.index]
    fig = go.Figure([go.Bar(x=years, y=y["benchmark"], name="Buy and hold", marker_color=BENCH_COLOR),
                     go.Bar(x=years, y=y["strategy"], name=label, marker_color=STRATEGY_COLOR)])
    return _layout(fig, barmode="group", yaxis_title="Return that year", yaxis_tickformat=".0%", height=340)


# ------------------------------------------------------------------ results

def _fmt(value, spec):
    return "N/A" if value is None else format(value, spec)


def _scorecard(s, b, label):
    rows = [
        ("Final value", "final_value", lambda v: f"${v:,.0f}", "return"),
        ("Total return", "total_return", lambda v: f"{v:+.1%}", "return"),
        ("Yearly growth (CAGR)", "annualized_return", lambda v: f"{v:+.1%}", "cagr"),
        ("Worst drop (max drawdown)", "max_drawdown", lambda v: f"{v:.1%}", "drawdown"),
        ("Sharpe ratio", "sharpe_ratio", lambda v: f"{v:.2f}", "sharpe"),
        ("Volatility", "annualized_volatility", lambda v: f"{v:.1%}", "vol"),
    ]
    left, right = st.columns(2)
    with left:
        st.markdown(f"**:blue[{label}]**")
        for title, key, fmt, help_key in rows:
            sv, bv = s.get(key), b.get(key)
            delta = None
            if sv is not None and bv is not None:
                d = sv - bv
                if key == "final_value":
                    # The sign must come first, or Streamlit shows a loss as a green up-arrow.
                    delta = f"{'-' if d < 0 else '+'}${abs(d):,.0f} vs buy & hold"
                elif key == "sharpe_ratio":
                    delta = f"{d:+.2f} vs buy & hold"
                else:
                    delta = f"{d * 100:+.1f} pts vs buy & hold"
            st.metric(title, "N/A" if sv is None else fmt(sv), delta=delta, help=HELP[help_key],
                      delta_color="inverse" if key == "annualized_volatility" else "normal")
        st.caption(f"{s['num_trades']} trades · invested {s['time_in_market']:.0%} of the time")
    with right:
        st.markdown("**:orange[Buy and hold]**")
        for title, key, fmt, help_key in rows:
            bv = b.get(key)
            st.metric(title, "N/A" if bv is None else fmt(bv), help=HELP[help_key])
        st.caption("1 trade · invested 100% of the time")


def _show_results(r):
    cfg, s, b = r["cfg"], r["s"], r["b"]
    label = "AI predictor" if cfg["strategy"] == STRATEGY_ML else f"MA {cfg['short']}/{cfg['long']} rule"
    name = "Practice data (simulated)" if cfg["practice"] else cfg["ticker"]
    first, last = r["strat_res"].index[0], r["strat_res"].index[-1]

    st.markdown("### Step 3 · Prediction vs. reality")
    if cfg["practice"]:
        st.warning("These are **simulated prices**, not real market history. Use them for practice only.")
    st.caption(f"{name} · scored from {first:%b %d, %Y} to {last:%b %d, %Y} · trading cost {cfg['cost']:.2%} "
               f"per trade · starting money ${STARTING_MONEY:,}")
    if cfg["strategy"] == STRATEGY_ML:
        st.info("The AI trained on the period before these dates. Both approaches are scored only on the "
                "stretch it never saw.")

    names = {"strategy": label, "benchmark": "Buy and hold"}
    cols = st.columns(3)
    for col, row in zip(cols, r["score"]):
        if row["question"].startswith("Which"):
            guess, actual = names[row["guess"]], names[row["actual"]]
            verdict = ":green[✔ Correct]" if row["correct"] else ":red[✘ Missed]"
        else:
            guess, actual = f"{row['guess']:.0%}", f"{row['actual']:.0%}"
            verdict = ":green[✔ Within 10 points]" if row["correct"] else ":red[✘ More than 10 points off]"
        with col.container(border=True):
            st.markdown(f"**{row['question']}**")
            st.markdown(f"You guessed: **{guess}**  \nReality: **{actual}**")
            st.markdown(verdict)
    hits = sum(row["correct"] for row in r["score"])
    st.markdown(f"**Score: {hits} / 3.** " + ("Great intuition!" if hits == 3 else "Not bad!" if hits == 2 else
                "Markets are hard to predict, and that's exactly why we test."))
    if cfg["prediction"].get("reason"):
        st.caption(f"Your reasoning: “{cfg['prediction']['reason']}”")

    st.plotly_chart(_growth_chart(r, label), width="stretch")

    tab_names = ["Scorecard", "Drawdowns"] + (["Price & averages"] if cfg["strategy"] == STRATEGY_MA else [])
    tabs = st.tabs(tab_names)
    with tabs[0]:
        _scorecard(s, b, label)
    with tabs[1]:
        st.caption(HELP["drawdown"])
        st.plotly_chart(_drawdown_chart(r, label), width="stretch")
    if cfg["strategy"] == STRATEGY_MA:
        with tabs[2]:
            st.caption("The rule owns the stock when the blue line (short average) is above the orange dashed "
                       "line (long average).")
            st.plotly_chart(_price_chart(r, name), width="stretch")

    st.markdown("### Step 4 · Why did it turn out this way?")
    for note in r["notes"]:
        st.markdown(f"- {note}")

    st.markdown("### Step 5 · Does it hold up year by year?")
    st.caption("If a strategy really works, it should win most years, not just one lucky stretch.")
    if len(r["yearly"]) >= 2:
        st.plotly_chart(_yearly_chart(r, label), width="stretch")
    else:
        st.info("This test covers only one calendar year. Choose a longer time period (like 'Long run') to "
                "see whether the result holds up year after year.")

    st.markdown("### Step 6 · What this test can't tell you")
    for title, text in LIMITS:
        st.markdown(f"- **{title}.** {text}")


def _notebook():
    exps = st.session_state["lab_experiments"]
    if not exps:
        return
    st.divider()
    st.markdown("### Your lab notebook")
    rows = []
    for e in exps:
        label = "AI" if e["cfg"]["strategy"] == STRATEGY_ML else f"MA {e['cfg']['short']}/{e['cfg']['long']}"
        res = e["strat_res"]
        rows.append({
            "Stock": e["cfg"]["ticker"], "Period": f"{res.index[0]:%Y-%m} → {res.index[-1]:%Y-%m}",
            "Strategy": label,
            "Winner": "Strategy" if e["s"]["final_value"] > e["b"]["final_value"] else "Buy & hold",
            "Strategy return": _fmt(e["s"]["total_return"], "+.0%"),
            "Buy & hold return": _fmt(e["b"]["total_return"], "+.0%"),
            "Your score": f"{sum(x['correct'] for x in e['score'])}/3",
        })
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    wins = sum(row["Winner"] == "Strategy" for row in rows)
    st.caption(f"The tested strategy has beaten buy-and-hold in {wins} of your {len(rows)} experiments. "
               "Try different stocks and periods. Does a pattern appear, or is it luck?")
    if st.button("Clear notebook"):
        st.session_state["lab_experiments"] = []
        st.session_state["lab_current"] = None
        st.rerun()


def render_lab_page(load_market_data, default_ticker="SPY"):
    _init_state()
    st.title("Prediction-versus-Reality Lab")
    st.write("**The question:** can a trading rule, or even an AI, beat simply buying and holding? "
             "Make your call, then let history answer.")
    cfg = _setup_and_predict(default_ticker)
    if cfg is not None:
        result = _run(cfg, load_market_data)
        st.session_state["lab_current"] = result  # None after an error, so old results don't look new
        if result is not None:
            st.session_state["lab_experiments"].append(result)
    if st.session_state["lab_current"] is not None:
        _show_results(st.session_state["lab_current"])
    _notebook()
