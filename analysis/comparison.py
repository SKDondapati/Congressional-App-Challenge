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
