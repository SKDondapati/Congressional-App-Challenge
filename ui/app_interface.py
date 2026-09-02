import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from backtest.engine import calculate_stats, run_simulation
from data.data_manager import clean_price_data, download_market_data
from strategies.benchmark import buy_hold_strategy
from strategies.moving_average import moving_average_strategy
from strategies.ml_predictor import ml_predictor_strategy
from ui.components import (
    display_metrics,
    plot_drawdown,
    plot_equity_curve,
    render_educational_footer,
    render_shock_card,
)


st.set_page_config(page_title='QuantLit - Algorithmic Literacy Lab', layout='wide')


# --- Sidebar ---
with st.sidebar:
    st.title('⚙️ QuantLit')
    st.markdown('### Strategy Settings')

    ticker = st.text_input('Stock Ticker', value='AAPL')
    start_date = st.date_input('Start Date', pd.to_datetime('2020-01-01'))
    end_date = st.date_input('End Date', pd.to_datetime('2023-12-31'))

    strategy_choice = st.selectbox(
        'Select Strategy',
        ['Moving Average (20/50)', 'ML Predictor', 'Buy & Hold', 'Compare All'],
    )

    short_window = st.slider('Short MA Window', 5, 50, 20) if strategy_choice in ['Moving Average (20/50)', 'Compare All'] else 20
    long_window = st.slider('Long MA Window', 20, 200, 50) if strategy_choice in ['Moving Average (20/50)', 'Compare All'] else 50
    initial_capital = st.number_input('Starting Capital ($)', value=10000, min_value=1000)
    run_btn = st.button('🚀 Run Backtest', use_container_width=True)


# --- Main Panel ---
st.title('📈 QuantLit: Algorithmic Literacy Lab')
st.caption('Test trading strategies on real historical data — no risk, just learning.')


if run_btn:
    with st.spinner(f'Loading data for {ticker}...'):
        raw = download_market_data(ticker, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        if raw is None or raw.empty:
            st.error('No data found for that ticker. Please check the symbol and dates.')
            st.stop()

        data = clean_price_data(raw)
        st.success(f'Loaded {len(data)} days of data.')

    if strategy_choice == 'Compare All':
        strategies = {
            'Moving Average': (moving_average_strategy, {'short_window': short_window, 'long_window': long_window}),
            'ML Predictor': (ml_predictor_strategy, {'lookback': 5, 'test_size': 0.2}),
            'Buy & Hold': (buy_hold_strategy, {}),
        }
        results_dict = {}
        for name, (func, kwargs) in strategies.items():
            with st.spinner(f'Running {name}...'):
                signals = func(data, **kwargs) if kwargs else func(data)
                sim = run_simulation(data, signals, starting_money=initial_capital)
                stats = calculate_stats(sim)
                results_dict[name] = (sim, stats)

        st.subheader('📊 Strategy Comparison')
        cols = st.columns(len(results_dict))
        for i, (name, (_, stats)) in enumerate(results_dict.items()):
            with cols[i]:
                st.markdown(f'**{name}**')
                display_metrics(stats)
                render_shock_card(stats, name)

        st.subheader('Equity Curve Comparison')
        fig = go.Figure()
        for name, (sim, _) in results_dict.items():
            fig.add_trace(go.Scatter(x=sim.index, y=sim['portfolio_value'], name=name))
        fig.add_trace(
            go.Scatter(
                x=list(results_dict['Buy & Hold'][0].index),
                y=list(results_dict['Buy & Hold'][0]['buy_hold_value']),
                name='Buy & Hold Benchmark',
                line=dict(dash='dash', color='gray'),
            )
        )
        fig.update_layout(title='Portfolio Value Comparison', xaxis_title='Date', yaxis_title='Value ($)')
        st.plotly_chart(fig, use_container_width=True)
        render_educational_footer()
    else:
        if strategy_choice == 'Moving Average (20/50)':
            func = moving_average_strategy
            kwargs = {'short_window': short_window, 'long_window': long_window}
            name = f'MA ({short_window}/{long_window})'
        elif strategy_choice == 'ML Predictor':
            func = ml_predictor_strategy
            kwargs = {'lookback': 5, 'test_size': 0.2}
            name = 'ML Predictor'
        else:
            func = buy_hold_strategy
            kwargs = {}
            name = 'Buy & Hold'

        with st.spinner(f'Running {name}...'):
            signals = func(data, **kwargs) if kwargs else func(data)
            results = run_simulation(data, signals, starting_money=initial_capital)
            stats = calculate_stats(results)

        st.subheader(f'📊 {name} Results')
        display_metrics(stats)
        render_shock_card(stats, name)

        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(plot_equity_curve(results, name), use_container_width=True)
        with col2:
            st.plotly_chart(plot_drawdown(results), use_container_width=True)

        render_educational_footer()
else:
    st.info('👈 Configure your strategy in the sidebar and click **Run Backtest** to see results.')
    st.markdown(
        """
        ### Quick Start
        1. Enter a stock ticker (e.g., AAPL, TSLA, SPY)
        2. Pick a date range
        3. Choose a strategy or compare all
        4. Click Run Backtest
        """
    )
