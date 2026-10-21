import streamlit as st
from .components import render_concept_card
from .i18n import t


def render_explain_mode_for_metric(title, value, stats=None, results=None, starting_amount=None, start_date=None):
	"""Show a Simple → Example → Quant → So what explanation for a metric.

	Provide concrete examples using `stats` and `results` when available.
	"""
	stats = stats or {}
	results = results

	# Helper to format dollars
	def money(x):
		try:
			return f"${float(x):,.0f}"
		except Exception:
			return str(x)

	# Total Return
	if title.lower().startswith("total"):
		simple = t("How the investment performed, excluding deposits.")
		tr = stats.get("total_return") if stats else None
		fv = stats.get("final_value") if stats else None
		contributed = stats.get("total_contributions")
		if tr is not None and fv is not None and contributed is not None:
			example = f"You contributed {money(contributed)} and the account ended at {money(fv)}. Investment performance was {tr:.2%}, separate from deposits."
			so_what = "The ending balance includes both your deposits and investment gains or losses; the return isolates the investment part."
		else:
			example = t("If you put $10,000 in and later had $13,720, that's a +37.2% total return.")
			so_what = None

		quant = t("Time-weighted return compounds daily strategy returns. Deposits do not count as gains.")
		calculation = "product(1 + daily_strategy_return) - 1"

	# Sharpe Ratio
	elif title.lower().startswith("sharpe"):
		simple = t("A single number that compares return to how bouncy the investment was.")
		sr = stats.get("sharpe_ratio") if stats else None
		if sr is not None:
			example = f"In this experiment the Sharpe ratio was {sr:.2f}. It summarizes return relative to daily variability."
			so_what = "A higher value is not automatically a better investment. It depends on the period, assumptions, and whether the risk fits your needs."
		else:
			example = "The ratio is undefined for this experiment because it has too few return observations or no return variability."
			so_what = "N/A is more honest than showing a number when the calculation is undefined."

		quant = t("Annualized Sharpe uses daily strategy returns, a 0% annual risk-free rate by default, and 252 trading days.")
		calculation = "sqrt(252) * mean(daily_return - risk_free_rate / 252) / std(daily_return)"

	# Max Drawdown
	elif title.lower().startswith("drawdown"):
		simple = t("The biggest drop from a previous high during the period.")
		md = stats.get("max_drawdown") if stats else None
		if md is not None and results is not None:
			pct = f"{md:.2%}"
			example = f"The worst historical performance drawdown was {pct}. Monthly deposits are excluded from this calculation."
			so_what = "A strong return does not mean the journey was smooth. Drawdown describes the largest fall from a previous performance high."
		else:
			example = t(
				"If your portfolio reached $10,000 and later fell to $7,500 before recovering, the maximum drawdown was 25%."
			)
			so_what = None

		quant = t(
			"Max drawdown = min(performance_index / running_max(performance_index) - 1). Deposits are excluded."
		)
		calculation = "min(performance_index / running_max(performance_index) - 1)"

	# Volatility (annualized)
	elif title.lower().startswith("volatility"):
		simple = t("How big typical day-to-day or year-to-year swings are.")
		vol = None
		if results is not None and "strategy_return" in results.columns:
			daily = results["strategy_return"].dropna()
			if len(daily) > 1:
				vol = daily.std(ddof=1) * (252 ** 0.5)
		if vol is not None:
			example = f"This experiment had an annualized volatility of about {vol:.2%}."
			so_what = (
				"Volatility measures how bumpy the investment returns were. It does not show every kind of risk or predict future swings."
			)
		else:
			example = t("Volatility is the standard deviation of returns, annualized."
			)
			so_what = None
		quant = t("Annualized volatility = std(daily_returns) * sqrt(252).")
		calculation = "std(daily_returns) * sqrt(252)"

	# CAGR (compound annual growth rate)
	elif title.lower().startswith("cagr"):
		simple = t("Average annual growth rate if returns compounded each year.")
		cagr = stats.get("annualized_return")
		if cagr is not None:
			example = f"CAGR for this experiment was about {cagr:.2%} per year over the period."
			so_what = (
				"CAGR smooths year-to-year swings to show an average annual growth rate — useful for comparing investments over different lengths."
			)
		else:
			example = t("CAGR = (final/start)^(1/years) - 1")
			so_what = None
		quant = t("CAGR annualizes time-weighted return over the measured period.")
		calculation = "(1 + time_weighted_return)^(1/years) - 1"

	# Inflation / real returns
	elif title.lower().startswith("inflation"):
		simple = t("How much inflation reduced the purchasing power of your returns.")
		# assume default inflation if we can't compute it here
		inflation_rate = 0.02
		tr = stats.get("total_return") if stats else None
		cagr_val = stats.get("annualized_return")
		if cagr_val is not None:
			real = (1 + cagr_val) / (1 + inflation_rate) - 1
			example = f"Using {inflation_rate:.0%} as an example inflation assumption, estimated real CAGR would be about {real:.2%}. This is not the actual inflation rate for the selected dates."
			so_what = (
				"Inflation reduces your purchasing power; compare nominal vs real returns to understand actual improvements in buying power."
			)
		else:
			example = f"Using {inflation_rate:.0%} as an example assumption, real returns would be lower than nominal. This is not the actual inflation rate for the selected dates."
			so_what = None
		quant = t("Real return ≈ (1 + nominal_return) / (1 + inflation_rate) - 1")
		calculation = "(1 + nominal) / (1 + inflation) - 1"

	else:
		simple = t("A plain-language explanation goes here.")
		example = t("A short example helps connect the idea to money you know.")
		quant = t("Show the formula or the data used to compute the number.")
		calculation = None
		so_what = None

	# Provide a stable key derived from title to avoid duplicate Streamlit widget ids
	safe_key = title.replace(" ", "_").lower()
	render_concept_card(
		title,
		value=value,
		simple=simple,
		example=example,
		quant=quant,
		calculation=calculation,
		so_what=so_what,
		key=safe_key,
	)


def show_metric_explainers(stats, results=None, starting_amount=None, start_date=None):
	"""Given a stats dict and optional results, render explainers for common metrics.

	results: the simulation dataframe (with portfolio_value) so we can build concrete examples.
	"""
	render_explain_mode_for_metric(
		"Total Return",
		f"{stats['total_return']:.2%}" if stats.get("total_return") is not None else "N/A",
		stats=stats,
		results=results,
		starting_amount=starting_amount,
		start_date=start_date,
	)
	render_explain_mode_for_metric(
		"Sharpe Ratio",
		f"{stats['sharpe_ratio']:.2f}" if stats.get("sharpe_ratio") is not None else "N/A",
		stats=stats,
		results=results,
		starting_amount=starting_amount,
		start_date=start_date,
	)
	render_explain_mode_for_metric(
		"Max Drawdown",
		f"{stats['max_drawdown']:.2%}" if stats.get("max_drawdown") is not None else "N/A",
		stats=stats,
		results=results,
		starting_amount=starting_amount,
		start_date=start_date,
	)
	render_explain_mode_for_metric(
		"Volatility",
		(
			f"{stats['annualized_volatility']:.2%}"
			if stats.get("annualized_volatility") is not None
			else "N/A"
		),
		stats=stats,
		results=results,
		starting_amount=starting_amount,
		start_date=start_date,
	)

