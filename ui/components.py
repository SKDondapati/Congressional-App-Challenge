import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def plot_equity_curve(results_df, strategy_name):
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=results_df.index,
            y=results_df['portfolio_value'],
            name=f'{strategy_name} Strategy',
            line=dict(color='blue', width=2),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=results_df.index,
            y=results_df['buy_hold_value'],
            name='Buy & Hold Benchmark',
            line=dict(color='gray', width=2, dash='dash'),
        )
    )

    drawdown = (results_df['portfolio_value'] - results_df['portfolio_value'].cummax()) / results_df['portfolio_value'].cummax()
    crash_mask = drawdown < -0.15
    if crash_mask.any():
        crash_dates = results_df.index[crash_mask.to_numpy()]
        if len(crash_dates) > 0:
            fig.add_vrect(
                x0=crash_dates[0],
                x1=crash_dates[-1],
                fillcolor='red',
                opacity=0.1,
                layer='below',
                line_width=0,
                annotation_text='Stress Period',
            )

    fig.update_layout(
        title='Portfolio Value Over Time',
        xaxis_title='Date',
        yaxis_title='Portfolio Value ($)',
        hovermode='x',
        legend=dict(x=0, y=1, bgcolor='rgba(255,255,255,0.8)'),
    )
    return fig


def plot_drawdown(results_df):
    cum_max = results_df['portfolio_value'].cummax()
    drawdown = (results_df['portfolio_value'] - cum_max) / cum_max

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=drawdown.index,
            y=drawdown.values * 100,
            fill='tozeroy',
            line=dict(color='red', width=1),
            name='Drawdown %',
        )
    )
    fig.update_layout(
        title='Drawdown Over Time',
        xaxis_title='Date',
        yaxis_title='Drawdown (%)',
        hovermode='x',
    )
    return fig


def display_metrics(stats):
    col1, col2, col3, col4 = st.columns(4)
    col1.metric('Total Return', f"{stats['total_return']:.2%}")
    col2.metric('Sharpe Ratio', f"{stats['sharpe_ratio']:.2f}")
    col3.metric('Max Drawdown', f"{stats['max_drawdown']:.2%}")
    col4.metric('Final Value', f"${stats['final_value']:,.2f}")


def render_shock_card(stats, strategy_name):
    max_drawdown = float(stats.get('max_drawdown', 0.0))
    if max_drawdown < -0.20:
        st.error(f'⚠️ **REALITY CHECK** — {strategy_name} had a peak loss of **{max_drawdown:.2%}**')
        recovery_needed = -max_drawdown / (1 + max_drawdown)
        st.write(f'To recover from that loss, you would need a **{recovery_needed:.2%}** gain just to break even.')
        st.caption('This is why risk management matters more than chasing returns.')
    elif max_drawdown < -0.10:
        st.warning(f'⚠️ {strategy_name} saw a drawdown of {max_drawdown:.2%} — be careful.')


def render_educational_footer():
    st.divider()
    st.subheader('🧠 Algorithmic Literacy Takeaways')
    st.markdown(
        """
        - **Higher returns come with higher risk** — check the drawdown.
        - **ML isn't magic** — it can lose during crashes.
        - **Buy & Hold isn't always bad** — sometimes patience wins.
        - **Always backtest** before trusting a strategy.
        - **This is a simulation** — not financial advice.
        """
    )
    st.caption('Built by students for the Congressional App Challenge')


__all__ = [
    'plot_equity_curve',
    'plot_drawdown',
    'display_metrics',
    'render_shock_card',
    'render_educational_footer',
]