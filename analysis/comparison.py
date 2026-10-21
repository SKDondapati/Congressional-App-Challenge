import math

import pandas as pd

from backtest.engine import calculate_stats


def compare_results(results_by_strategy):
	"""Build a small, consistent summary from named simulation results."""
	rows = []
	for name, result in results_by_strategy.items():
		if isinstance(result, tuple):
			result = result[0]
		stats = calculate_stats(result)
		rows.append(
			{
				"strategy": name,
				"final_value": stats["final_value"],
				"total_contributions": stats["total_contributions"],
				"investment_return": stats["total_return"],
				"annualized_return": stats["annualized_return"],
				"max_drawdown": stats["max_drawdown"],
				"annualized_volatility": stats["annualized_volatility"],
				"explanation": (
					f"Ended at ${stats['final_value']:,.2f} after "
					f"${stats['total_contributions']:,.2f} was contributed. "
					"Return, drawdown, and volatility describe investment "
					"performance, not the effect of adding money."
				),
			}
		)
	return pd.DataFrame(rows)


def largest_drawdown_strategies(results_by_strategy, tolerance=1e-9):
	"""Return every strategy tied for the largest valid drawdown."""
	valid_drawdowns = {}
	for name, result in results_by_strategy.items():
		if isinstance(result, tuple):
			result = result[0]
		drawdown = calculate_stats(result).get("max_drawdown")
		if drawdown is not None and math.isfinite(drawdown):
			valid_drawdowns[name] = drawdown

	if not valid_drawdowns:
		return []
	worst_drawdown = min(valid_drawdowns.values())
	if worst_drawdown >= -tolerance:
		return []
	return [
		name
		for name, drawdown in valid_drawdowns.items()
		if math.isclose(drawdown, worst_drawdown, rel_tol=tolerance, abs_tol=tolerance)
	]
