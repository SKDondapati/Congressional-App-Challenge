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
		simple = t("How much your investment changed from start to finish.")
		tr = stats.get("total_return") if stats else None
		fv = stats.get("final_value") if stats else None
		if tr is not None and fv is not None and starting_amount is not None:
			example = f"Your investment grew from {money(starting_amount)} to {money(fv)}, a historical total return of {tr:.2%}."
			so_what = f"This means your {money(starting_amount)} investment increased by {money(fv - starting_amount)} over the period."
		else:
			example = t("If you put $10,000 in and later had $13,720, that's a +37.2% total return.")
			so_what = None

		quant = t("Total return = (final_value / start_value) - 1. It does not show yearly changes.")
		calculation = "(final_value / start_value) - 1"

	# Sharpe Ratio
	elif title.lower().startswith("sharpe"):
		simple = t("A single number that compares return to how bouncy the investment was.")
		sr = stats.get("sharpe_ratio") if stats else None
		if sr is not None:
			example = f"In this experiment the Sharpe ratio was {sr:.2f}. Higher is generally better."
			so_what = "A higher Sharpe suggests you earned returns with less variability relative to the average."
		else:
			example = t(
				"Imagine two funds that both earned 8% per year. If one had small swings and the other jumped all over the place, the calmer one has a higher Sharpe."
			)
			so_what = None

		quant = t("Sharpe ≈ (mean_return - risk_free) / std_dev_of_returns. Higher is better.")
		calculation = "(mean_return - risk_free_rate) / std_dev(returns)"

	# Max Drawdown
	elif title.lower().startswith("drawdown"):
		simple = t("The biggest drop from a previous high during the period.")
		md = stats.get("max_drawdown") if stats else None
		if md is not None and results is not None:
			pct = f"{md:.2%}"
			try:
				peak = results["portfolio_value"].cummax().max()
				trough = results["portfolio_value"].min()
				example = (
					f"Your investment's largest historical drop was {pct}. In this experiment, a ${int(peak):,} peak fell to about ${int(trough):,}."
				)
				so_what = (
					"A strong long-term return doesn't mean the journey was smooth. Drawdown helps you see how large the worst historical decline was."
				)
			except Exception:
				example = t(
					"If your portfolio reached $10,000 and later fell to $7,500 before recovering, the maximum drawdown was 25%."
				)
				so_what = None
		else:
			example = t(
				"If your portfolio reached $10,000 and later fell to $7,500 before recovering, the maximum drawdown was 25%."
			)
			so_what = None

		quant = t(
			"Max drawdown = min over time of (value / running_max(value) - 1). Expressed as a negative percent."
		)
		calculation = "min( value / running_max(value) - 1 )"

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
				"Volatility measures how bumpy the ride has been. Higher volatility means larger swings — helpful to know for risk tolerance."
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
		cagr = None
		try:
			if results is not None:
				sv = results["portfolio_value"].iloc[0]
				fv = results["portfolio_value"].iloc[-1]
				days = (results.index[-1] - results.index[0]).days
				years = days / 365.25 if days > 0 else 1
				cagr = (fv / sv) ** (1 / years) - 1
		except Exception:
			cagr = None
		if cagr is not None:
			example = f"CAGR for this experiment was about {cagr:.2%} per year over the period."
			so_what = (
				"CAGR smooths year-to-year swings to show an average annual growth rate — useful for comparing investments over different lengths."
			)
		else:
			example = t("CAGR = (final/start)^(1/years) - 1")
			so_what = None
		quant = t("CAGR = (final_value / start_value)^(1 / years) - 1")
		calculation = "(final / start)^(1/years) - 1"

	# Inflation / real returns
	elif title.lower().startswith("inflation"):
		simple = t("How much inflation reduced the purchasing power of your returns.")
		# assume default inflation if we can't compute it here
		inflation_rate = 0.02
		tr = stats.get("total_return") if stats else None
		cagr_val = None
		try:
			if results is not None:
				sv = results["portfolio_value"].iloc[0]
				fv = results["portfolio_value"].iloc[-1]
				days = (results.index[-1] - results.index[0]).days
				years = days / 365.25 if days > 0 else 1
				cagr_val = (fv / sv) ** (1 / years) - 1
		except Exception:
			pass
		if cagr_val is not None:
			real = (1 + cagr_val) / (1 + inflation_rate) - 1
			example = f"Assuming {inflation_rate:.0%} annual inflation, the real CAGR would be about {real:.2%}."
			so_what = (
				"Inflation reduces your purchasing power; compare nominal vs real returns to understand actual improvements in buying power."
			)
		else:
			example = f"Assuming {inflation_rate:.0%} annual inflation, your real returns would be lower than nominal."
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
		f"{stats.get('total_return', 0):.2%}",
		stats=stats,
		results=results,
		starting_amount=starting_amount,
		start_date=start_date,
	)
	render_explain_mode_for_metric(
		"Sharpe Ratio",
		f"{stats.get('sharpe_ratio', 0):.2f}",
		stats=stats,
		results=results,
		starting_amount=starting_amount,
		start_date=start_date,
	)
	render_explain_mode_for_metric(
		"Max Drawdown",
		f"{stats.get('max_drawdown', 0):.2%}",
		stats=stats,
		results=results,
		starting_amount=starting_amount,
		start_date=start_date,
	)

