"""Logic for the Prediction-versus-Reality Lab (no Streamlit code, so it can be tested)."""

import pandas as pd

from backtest.engine import calculate_stats, run_simulation
from strategies.benchmark import buy_hold_strategy
from strategies.ml_predictor import ml_predictor_strategy
from strategies.moving_average import moving_average_strategy

CLOSE_ENOUGH = 0.10  # a guess within 10 percentage points counts as close

STRATEGY_MA = "Moving-average rule"
STRATEGY_ML = "AI predictor"


class LabError(ValueError):
    """The experiment can't run; the message is safe to show to the user."""


def _trade_stats(results):
    trades = int(round(results["trade"].sum())) if "trade" in results else 0
    in_market = float(results["holding"].mean()) if "holding" in results and len(results) else 0.0
    return trades, in_market


def run_lab_experiment(data, strategy, short_window=20, long_window=50, cost_per_trade=0.001,
                       starting_money=10000):
    """Run one strategy and buy-and-hold over the same evaluation window.

    For the AI predictor, the model trains on the first 80% of the dates, and
    BOTH approaches are scored only on the last 20% the model never saw. That
    keeps the comparison fair and avoids data leakage.
    """
    if data is None or len(data) < 2:
        raise LabError("Not enough price data to run an experiment.")

    if strategy == STRATEGY_MA:
        if len(data) < long_window + 20:
            raise LabError(
                f"Only {len(data)} trading days were found. That's not enough for a {long_window}-day "
                "moving average. Choose a longer time period."
            )
        signals = moving_average_strategy(data, short_window, long_window)
        evaluation_start = None
    elif strategy == STRATEGY_ML:
        signals = ml_predictor_strategy(data, lookback=5, test_size=0.2)
        prediction_dates = signals.index[signals["evaluation_prediction"]]
        if len(prediction_dates) == 0:
            raise LabError("The AI needs more history to learn from. Choose a period of at least 2 years.")
        first = data.index.get_loc(prediction_dates[0])
        if first + 1 >= len(data):
            raise LabError("There are no trading days left to test the AI on. Choose a longer period.")
        evaluation_start = data.index[first + 1]
    else:
        raise LabError(f"Unknown strategy: {strategy}")

    bench_signals = buy_hold_strategy(data)
    kwargs = dict(starting_money=starting_money, start_date=evaluation_start, cost_per_trade=cost_per_trade)
    strat_res = run_simulation(data, signals, **kwargs)
    bench_res = run_simulation(data, bench_signals, **kwargs)

    s, b = calculate_stats(strat_res), calculate_stats(bench_res)
    s["num_trades"], s["time_in_market"] = _trade_stats(strat_res)
    b["num_trades"], b["time_in_market"] = _trade_stats(bench_res)
    # Stretching a few months of results into a yearly rate is misleading, so skip it.
    if (strat_res.index[-1] - strat_res.index[0]).days < 365:
        s["annualized_return"] = b["annualized_return"] = None
    return {
        "signals": signals,
        "strat_res": strat_res,
        "bench_res": bench_res,
        "s": s,
        "b": b,
        "yearly": yearly_comparison(strat_res, bench_res),
        "evaluation_start": evaluation_start,
    }


def yearly_comparison(strat_res, bench_res):
    """Each calendar year's return for both approaches, and which one won."""
    by_year = pd.DataFrame({
        "strategy": strat_res["strategy_return"],
        "benchmark": bench_res["strategy_return"],
    })
    by_year = (1 + by_year).groupby(by_year.index.year).prod() - 1
    by_year.index.name = "year"
    by_year["winner"] = ["strategy" if s > b else "benchmark"
                         for s, b in zip(by_year["strategy"], by_year["benchmark"])]
    return by_year


def score_prediction(prediction, strat_stats, bench_stats):
    """Compare a user's locked-in prediction with what happened.

    prediction keys: winner ("strategy"/"benchmark"), bench_return (fraction),
    bench_drawdown (positive fraction, e.g. 0.30 for a 30% drop).
    """
    actual_winner = "strategy" if strat_stats["final_value"] > bench_stats["final_value"] else "benchmark"
    actual_return = bench_stats["total_return"] or 0.0
    actual_drop = -(bench_stats["max_drawdown"] or 0.0)
    return [
        {"question": "Which ends with more money?", "guess": prediction["winner"],
         "actual": actual_winner, "correct": prediction["winner"] == actual_winner},
        {"question": "Buy-and-hold total return", "guess": prediction["bench_return"],
         "actual": actual_return,
         "correct": abs(prediction["bench_return"] - actual_return) <= CLOSE_ENOUGH},
        {"question": "Buy-and-hold worst drop", "guess": prediction["bench_drawdown"],
         "actual": actual_drop,
         "correct": abs(prediction["bench_drawdown"] - actual_drop) <= CLOSE_ENOUGH},
    ]


def explain_results(strategy, s, b, cost_per_trade, yearly=None):
    """Plain-English reasons the experiment turned out the way it did."""
    name = "The AI predictor" if strategy == STRATEGY_ML else "The moving-average rule"
    notes = []
    gap = (s["total_return"] or 0) - (b["total_return"] or 0)
    winner = name if gap > 0 else "Buy-and-hold"
    notes.append(f"{winner} came out ahead by {abs(gap) * 100:.1f} percentage points of total return.")

    notes.append(
        f"{name} was invested only {s['time_in_market']:.0%} of the time. The rest of the time its money sat "
        "in cash earning 0%. Cash protects you during crashes, but it misses gains when the market rebounds."
    )

    sd, bd = s["max_drawdown"] or 0, b["max_drawdown"] or 0
    if sd > bd + 0.05:
        notes.append(f"Its worst drop ({sd:.0%}) was smaller than buy-and-hold's ({bd:.0%}). Stepping aside "
                     "during downturns reduced the pain, even if it didn't always earn more.")
    elif sd < bd - 0.05:
        notes.append(f"Its worst drop ({sd:.0%}) was bigger than buy-and-hold's ({bd:.0%}). That can happen when "
                     "it sells after a dip and buys back after a rally, which is called getting 'whipsawed'.")

    if s["num_trades"] > 0 and cost_per_trade > 0:
        drag = 1 - (1 - cost_per_trade) ** s["num_trades"]
        notes.append(f"It made {s['num_trades']} trades. At {cost_per_trade:.2%} per trade, fees alone cost "
                     f"about {drag:.1%} of the portfolio.")
    elif s["num_trades"] > 0:
        notes.append(f"It made {s['num_trades']} trades, and this run assumed trading is free. Real trading "
                     "has costs. Try raising the trading cost to see how much that matters.")

    if strategy == STRATEGY_ML:
        notes.append("The AI learned from the first 80% of the period and was tested only on the last 20%, which "
                     "it had never seen. Doing well on data it trained on would prove nothing.")

    if (s["sharpe_ratio"] is not None and b["sharpe_ratio"] is not None
            and s["sharpe_ratio"] > b["sharpe_ratio"] and gap < 0):
        notes.append("It earned less but had a better Sharpe ratio, meaning more return for each unit of "
                     "bumpiness. Which is 'better' depends on whether you care more about growth or a smoother ride.")

    if yearly is not None and len(yearly) >= 2:
        wins = int((yearly["winner"] == "strategy").sum())
        steady = wins >= 0.7 * len(yearly) or wins <= 0.3 * len(yearly)
        notes.append(f"Year by year, it beat buy-and-hold in {wins} of {len(yearly)} years. "
                     + ("That's a fairly consistent pattern." if steady
                        else "The winner changes from year to year, so this result may not repeat."))
    return notes


LIMITS = [
    ("The past doesn't predict the future",
     "A strategy that worked on old data can fail on new data. Markets change."),
    ("One stock, one time period",
     "Results can flip with a different ticker or dates. Try a few before drawing conclusions."),
    ("Overfitting",
     "If you keep tweaking settings until one wins, you've probably found luck, not a rule."),
    ("Simplified trading",
     "Trades happen at the closing price, cash earns 0%, and taxes are ignored. Real trading is messier."),
    ("Survivorship bias",
     "Companies you've heard of today are the ones that survived. Testing only winners makes any strategy look good."),
]
