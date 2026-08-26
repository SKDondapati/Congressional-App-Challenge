import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from data.data_manager import download_market_data, clean_price_data
from strategies.moving_average import moving_average_strategy
from strategies.benchmark import buy_hold_strategy
from backtest.engine import run_simulation, calculate_stats
from ui.components import plot_equity_curve, render_shock_card

def main():
    st.set_page_config(page_title="QuantLit", layout="wide")
    st.title("📊 QuantLit: Algorithmic Literacy Lab")
    
    with st.sidebar:
        st.header("⚙️ Strategy Configuration")
        
        ticker = st.text_input("Stock Ticker", "AAPL")
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", pd.to_datetime("2020-01-01"))
        with col2:
            end_date = st.date_input("End Date", pd.to_datetime("2023-12-31"))
        
        strategy = st.selectbox(
            "Select Strategy",
            ["Moving Average", "Buy & Hold"]
        )
        
        short_window = 20
        long_window = 50
        if strategy == "Moving Average":
            short_window = st.slider("Short MA Window", 5, 50, 20)
            long_window = st.slider("Long MA Window", 20, 200, 50)
        
        initial_capital = st.number_input("Starting Capital ($)", value=10000)
        run_btn = st.button("🚀 Run Backtest")
    
    if run_btn:
        with st.spinner("Loading data and running backtest..."):
            raw = download_market_data(ticker, start_date, end_date)
            if raw is None or raw.empty:
                st.error("No data found. Please check the ticker symbol.")
                return
            
            data = clean_price_data(raw)
            
            if strategy == "Moving Average":
                signals = moving_average_strategy(data, short_window, long_window)
            else:
                signals = buy_hold_strategy(data)
            
            results = run_simulation(data, signals, initial_capital)
            stats = calculate_stats(results)
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Final Value", f"${stats['final_value']:,.2f}")
        col2.metric("Total Return", f"{stats['total_return']:.2%}")
        col3.metric("Sharpe Ratio", f"{stats['sharpe_ratio']:.2f}")
        col4.metric("Max Drawdown", f"{stats['max_drawdown']:.2%}")
        
        # Shock card
        render_shock_card(stats['max_drawdown'])
        
        # Equity curve
        st.subheader("📈 Portfolio Value Over Time")
        fig = plot_equity_curve(results, strategy)
        st.plotly_chart(fig, use_container_width=True)
        
        # Educational footer
        st.divider()
        st.subheader("🧠 What You Learned")
        if stats['max_drawdown'] < -0.20:
            st.write("📉 **Strategies fail during crashes.** Even good strategies can lose 20%+.")
        if stats['sharpe_ratio'] < 1.0:
            st.write("⚠️ **Higher returns come with higher risk.** A Sharpe ratio below 1.0 means the risk wasn't worth it.")
        st.write("💡 **Buy & Hold often outperforms active strategies** over long periods.")

if __name__ == "__main__":
    main()