import pandas as pd
import numpy as np
import streamlit as st

def plot_equity_curve(results df, strategy_name):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=results_df.index, y=results_df['portfolio_value'], name=strategy_name))
    fig.add_trace(go.Scatter(x=results_df.index, y=results_df['buy_hold_value'], name="Buy & Hold"))"))
    fig.update_layout(title="Portfolio Value Over Time")
    st.plotly_chart(fig)

def display_metrics(stats):
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Return", f"{stats['total_return']:.2%}")
    col2.metric("Sharpe Ratio", f"{stats['sharpe_ratio']:.2%}")
    col3.metric("Max Drawdown", f"{stats['max_drawdown']:.2%}")

def render_shock_card(max_drawdown):
    if max_drawdown < -0.2:
        st.error(f"⚠️ REALITY CHECK: You lost {max_drawdown:.2%} at peak.")
        st.write(f"You'd need a {max_drawdown/(1+max_drawdown):.2%} gain to recover.")