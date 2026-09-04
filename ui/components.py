import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def plot_equity_curve(results_df, strategy_name, palette=None):
    """Plot portfolio and buy&hold series. Accepts a `palette` dict for accessibility.

    palette keys: 'primary', 'benchmark', 'stress'
    """
    if palette is None:
        primary = "#1f77b4"
        benchmark = "gray"
        stress = "#d62728"
    else:
        primary = palette.get("primary", "#1f77b4")
        benchmark = palette.get("benchmark", "gray")
        stress = palette.get("stress", "#d62728")

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=results_df.index,
            y=results_df["portfolio_value"],
            name=f"{strategy_name} Strategy",
            line=dict(color=primary, width=3),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=results_df.index,
            y=results_df["buy_hold_value"],
            name="Buy & Hold Benchmark",
            line=dict(color=benchmark, width=2, dash="dash"),
        )
    )

    drawdown = (
        results_df["portfolio_value"] - results_df["portfolio_value"].cummax()
    ) / results_df["portfolio_value"].cummax()
    crash_mask = drawdown < -0.15
    if crash_mask.any():
        crash_dates = results_df.index[crash_mask.to_numpy()]
        if len(crash_dates) > 0:
            fig.add_vrect(
                x0=crash_dates[0],
                x1=crash_dates[-1],
                fillcolor=stress,
                opacity=0.1,
                layer="below",
                line_width=0,
                annotation_text="Stress Period",
            )

    fig.update_layout(
        title="Portfolio Value Over Time",
        xaxis_title="Date",
        yaxis_title="Portfolio Value ($)",
        hovermode="x",
        legend=dict(x=0, y=1, bgcolor="rgba(255,255,255,0.8)"),
    )
    st.plotly_chart(fig, width="stretch")
    # Provide a short textual summary for screen readers and captions
    try:
        end_val = results_df["portfolio_value"].iloc[-1]
        max_dd = (
            (results_df["portfolio_value"] - results_df["portfolio_value"].cummax())
            / results_df["portfolio_value"].cummax()
        ).min()
        st.caption(f"End value: ${end_val:,.2f} • Peak drawdown: {max_dd:.2%}")
    except Exception:
        pass
    return None


def plot_drawdown(results_df, palette=None):
    """Plot drawdown; palette can supply 'stress' color."""
    if palette is None:
        draw_color = "red"
    else:
        draw_color = palette.get("stress", "red")

    cum_max = results_df["portfolio_value"].cummax()
    drawdown = (results_df["portfolio_value"] - cum_max) / cum_max

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=drawdown.index,
            y=drawdown.values * 100,
            fill="tozeroy",
            line=dict(color=draw_color, width=1),
            name="Drawdown %",
        )
    )
    fig.update_layout(
        title="Drawdown Over Time",
        xaxis_title="Date",
        yaxis_title="Drawdown (%)",
        hovermode="x",
    )
    st.plotly_chart(fig, width="stretch")
    try:
        st.caption(f"Worst drawdown: {drawdown.min():.2%}")
    except Exception:
        pass
    return None


def display_metrics(stats, show_tooltips=False):
    """Render key metrics, optionally with beginner-friendly tooltips/translations."""
    translations = {
        "Total Return": "How much your money grew (including gains).",
        "Sharpe Ratio": "Risk-adjusted return: reward per unit of price bounciness.",
        "Max Drawdown": "Largest peak-to-trough loss seen during the period.",
        "Final Value": "Portfolio value at the end of the simulation.",
    }

    def _label_html(label):
        if show_tooltips and label in translations:
            tooltip = translations[label]
            return f'<span title="{tooltip}">{label}</span>'
        return label

    col1, col2, col3, col4 = st.columns(4)
    col1.markdown(_label_html("Total Return"), unsafe_allow_html=True)
    col1.write(f"{stats.get('total_return', 0):.2%}")

    col2.markdown(_label_html("Sharpe Ratio"), unsafe_allow_html=True)
    col2.write(f"{stats.get('sharpe_ratio', 0):.2f}")

    col3.markdown(_label_html("Max Drawdown"), unsafe_allow_html=True)
    col3.write(f"{stats.get('max_drawdown', 0):.2%}")

    col4.markdown(_label_html("Final Value"), unsafe_allow_html=True)
    col4.write(f"${stats.get('final_value', 0):,.2f}")


def render_shock_card(stats, strategy_name):
    max_drawdown = float(stats.get("max_drawdown", 0.0))
    if max_drawdown < -0.20:
        st.error(
            f"⚠️ **REALITY CHECK** — {strategy_name} had a peak loss of **{max_drawdown:.2%}**"
        )
        recovery_needed = -max_drawdown / (1 + max_drawdown)
        st.write(
            f"To recover from that loss, you would need a **{recovery_needed:.2%}** gain just to break even."
        )
        st.caption("This is why risk management matters more than chasing returns.")
    elif max_drawdown < -0.10:
        st.warning(
            f"⚠️ {strategy_name} saw a drawdown of {max_drawdown:.2%} — be careful."
        )


def render_concept_card(title, value=None, simple="", example="", quant="", calculation=None, so_what=None, key=None):
    """Render a four-part explanation card: Simple / Example / Quant / So what?

    Use emojis to make the sections friendly for beginners.
    """
    header = title
    if value is not None:
        header = f"{title} — {value}"
    st.markdown(f"### {header}")
    with st.expander("Explain this"):
        st.markdown("**💡 Simple**")
        st.write(simple)

        st.markdown("**🧮 Example**")
        st.write(example)

        st.markdown("**📐 Quant**")
        st.write(quant)

        if calculation:
            # Build a base key from provided key or sanitized title
            base = f"show_calc_{str(key)}" if key else f"show_calc_{title.replace(' ', '_')[:40]}"
            # Ensure uniqueness across this Streamlit session by tracking used keys
            used = st.session_state.get("_used_widget_keys", [])
            candidate = base
            i = 1
            while candidate in used:
                candidate = f"{base}_{i}"
                i += 1
            # record it so subsequent cards won't collide
            used.append(candidate)
            st.session_state["_used_widget_keys"] = used
            if st.checkbox("Show calculation", key=candidate):
                st.code(calculation)

        # So what? — render caller-provided concise takeaway when available
        st.markdown("**🎯 So what?**")
        if so_what:
            st.write(so_what)
        else:
            st.write(
                "This metric helps you understand tradeoffs. Use the example and quant sections for details."
            )


def render_educational_footer():
    st.divider()
    st.subheader("🧠 Algorithmic Literacy Takeaways")
    st.markdown("""
        - **Higher returns come with higher risk** — check the drawdown.
        - **ML isn't magic** — it can lose during crashes.
        - **Buy & Hold isn't always bad** — sometimes patience wins.
        - **Always backtest** before trusting a strategy.
        - **This is a simulation** — not financial advice.
        """)
    st.caption("Built by students for the Congressional App Challenge")


def render_beginner_explanation(results_dict, ticker, show_tooltips=True):
    st.markdown(f"### Beginner Summary for {ticker}")
    st.write(
        "This summary explains results in plain language so you can learn what happened."
    )
    term_map = {
        "Total return": "How much the money changed over the period.",
        "Final value": "The dollar amount you would have at the end.",
        "Maximum drawdown": "The biggest loss from a prior high point.",
    }

    for name, (sim, stats) in results_dict.items():
        st.markdown(f"**{name}**")
        fv_label = "Final value"
        tr_label = "Total return"
        dd_label = "Maximum drawdown"

        if show_tooltips:
            st.markdown(
                f"<strong title=\"{term_map[fv_label]}\">{fv_label}</strong>: ${stats.get('final_value', 0):,.2f}",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<strong title=\"{term_map[tr_label]}\">{tr_label}</strong>: {stats.get('total_return', 0):.2%}",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<strong title=\"{term_map[dd_label]}\">{dd_label}</strong>: {stats.get('max_drawdown', 0):.2%}",
                unsafe_allow_html=True,
            )
        else:
            st.write(f"Final value: ${stats.get('final_value', 0):,.2f}")
            st.write(f"Total return: {stats.get('total_return', 0):.2%}")
            dd = stats.get("max_drawdown", 0.0)
            st.write(f"Maximum drawdown: {dd:.2%}")
            if dd < -0.2:
                st.warning(
                    "This strategy had large losses during a stress period. Consider diversifying and using smaller position sizes."
                )
        st.markdown("---")


def render_quant_metrics(stats):
    st.markdown("### Quant Metrics")
    display_metrics(stats)
    st.markdown("**Notes:**")
    st.write(
        "Sharpe ratio measures risk-adjusted return. Max drawdown shows peak loss from a high point."
    )


def render_risk_scatter(results_dict):
    """Render a scatter plot of Sharpe vs Total Return for given result dict."""
    import plotly.express as px

    rows = []
    for name, (sim, stats) in results_dict.items():
        rows.append(
            {
                "strategy": name,
                "total_return": stats.get("total_return", 0),
                "sharpe_ratio": stats.get("sharpe_ratio", 0),
                "max_drawdown": stats.get("max_drawdown", 0),
            }
        )
    if not rows:
        st.info("No results to visualize for risk metrics.")
        return
    df = pd.DataFrame(rows)
    fig = px.scatter(
        df,
        x="sharpe_ratio",
        y="total_return",
        size=df["max_drawdown"].abs(),
        hover_name="strategy",
        title="Risk vs Return: Sharpe vs Total Return",
    )
    fig.update_layout(xaxis_title="Sharpe Ratio", yaxis_title="Total Return")
    st.plotly_chart(fig, width="stretch")


def plot_inflation_vs_sp500(
    start_date, end_date, inflation_rate=0.02, index_ticker="SPY"
):
    """Plot a comparison of $1,000 invested in SP500 ETF vs cash losing value to inflation.

    Uses a simple compounded inflation series at `inflation_rate` per year.
    """
    import yfinance as yf

    try:
        raw = yf.download(index_ticker, start=start_date, end=end_date)
        if raw is None or raw.empty:
            st.error("Unable to download index data for inflation comparison.")
            return
        prices = raw["Close"].dropna()
    except Exception:
        st.error("Error fetching index data for inflation comparison.")
        return

    # Normalize both to 1000 at start
    prices = prices / prices.iloc[0] * 1000.0

    # create inflation series assuming daily compounding
    days = (prices.index - prices.index[0]).days
    daily_rate = (1 + inflation_rate) ** (1 / 252) - 1
    inflation = 1000.0 * ((1 + daily_rate) ** (range(len(prices))))
    import numpy as np

    inflation = 1000.0 * (1 + daily_rate) ** np.arange(len(prices))

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(x=prices.index, y=prices.values, name=f"{index_ticker} Value")
    )
    fig.add_trace(
        go.Scatter(
            x=prices.index,
            y=inflation,
            name="Cash adjusted for inflation",
            line=dict(dash="dash"),
        )
    )
    fig.update_layout(
        title="Inflation vs Market (starting $1000)",
        xaxis_title="Date",
        yaxis_title="Value ($)",
    )
    # show the chart (stretch to container)
    st.plotly_chart(fig, width="stretch")


def simulate_1000_from_date(data, start_invest_date):
    """Return a series showing how $1,000 invested at start_invest_date would evolve using data['close']."""
    if start_invest_date not in data.index:
        # find next valid date
        idx = data.index.searchsorted(start_invest_date)
        if idx >= len(data.index):
            return None
        start_idx = idx
    else:
        start_idx = data.index.get_loc(start_invest_date)

    series = data["close"].iloc[start_idx:]
    rel = series / series.iloc[0] * 1000.0
    return rel


def render_investing_guide():
    st.title("How to Start Investing in the US Stock Market")
    st.caption("A simple guide for immigrant families and new investors")

    st.markdown("""
    ### Welcome
    
    If you are new to the US, investing can feel confusing. This guide explains the basics in plain language. No jargon. No pressure.
    """)

    with st.expander("What is a stock?"):
        st.markdown("""
        A stock is a small piece of a company. When you buy a stock, you own a tiny part of that business.
        
        **Example:** If you buy one share of Apple (AAPL), you own a tiny slice of Apple. If Apple makes money, the value of your share might go up. If Apple struggles, your share might lose value.
        
        **Key point:** Stocks go up and down. That is normal. The US stock market has gone up over the long term, but there are always ups and downs along the way.
        """)

    with st.expander("What is a stock market?"):
        st.markdown("""
        The stock market is where people buy and sell stocks. Think of it like a giant marketplace.
        
        The two biggest US stock exchanges are:
        - **NYSE** (New York Stock Exchange) - older companies like IBM, Ford
        - **NASDAQ** - tech companies like Apple, Microsoft, Tesla
        
        When people say "the market is up," they usually mean the S&P 500 (a group of 500 large US companies) has gone up.
        """)

    with st.expander("How do I actually start investing?"):
        st.markdown("""
        Here is the step-by-step process:
        
        1. **Open a brokerage account** - This is like a bank account for stocks. Popular options include:
           - Fidelity
           - Vanguard
           - Charles Schwab
           - Robinhood (app-based, simple for beginners)
        
        2. **Link your bank account** - Transfer money from your bank to the brokerage.
        
        3. **Pick an investment** - For beginners, start with an index fund like the S&P 500. This spreads your money across 500 companies so you are not relying on just one stock.
        
        4. **Buy and hold** - The simplest strategy. Buy shares and keep them for years. Do not panic sell when the market drops.
        
        **Important:** You do not need a lot of money to start. Many brokers let you start with $0 or very small amounts.
        """)

    with st.expander("What is an index fund or ETF?"):
        st.markdown("""
        An index fund (or ETF) is a basket of stocks. When you buy one share of an index fund, you are buying tiny pieces of many companies at once.
        
        **Popular examples:**
        - **SPY** - Tracks the S&P 500 (500 largest US companies)
        - **VTI** - Tracks the entire US stock market
        - **QQQ** - Tracks the Nasdaq (mostly tech companies)
        
        **Why index funds are good for beginners:** They are diversified. If one company fails, the others can still grow. They are low cost and simple.
        """)

    with st.expander("What is a trading strategy?"):
        st.markdown("""
        A trading strategy is a set of rules that tells you when to buy and when to sell.
        
        **Common strategies:**
        - **Buy and Hold** - Buy and never sell. Simple and often works well over long periods.
        - **Moving Average** - Buy when price goes above its average, sell when it goes below.
        - **Value investing** - Buy companies that seem undervalued.
        - **Growth investing** - Buy companies that are growing fast.
        
        **The lesson from this app:** No strategy is perfect. Some work better in certain periods. The best strategy depends on your goals and how much risk you can handle.
        """)

    with st.expander("What is risk and why does it matter?"):
        st.markdown("""
        Risk means the chance of losing money. All investing has some risk.
        
        **Types of risk:**
        - **Market risk** - The whole market drops (like in 2008 or 2020)
        - **Company risk** - One specific company fails
        - **Inflation risk** - Your money loses value over time if it just sits in cash
        
        **Rule of thumb:** Higher returns usually come with higher risk. If something promises big returns with no risk, it is probably a scam.
        
        **How to manage risk:**
        - Diversify (don't put all your money in one stock)
        - Invest for the long term (5+ years)
        - Do not invest money you need in the next few years
        """)

    with st.expander("What is a 401(k) or IRA?"):
        st.markdown("""
        These are special accounts that give you tax benefits for saving for retirement.
        
        - **401(k)** - Offered by many employers. They might match some of your contributions (free money!).
        - **IRA** - Individual Retirement Account. You open it yourself.
        
        **Why they matter:** Money grows tax-free or tax-deferred. This means you keep more of your returns.
        
        **Advice for new immigrants:** If your employer offers a 401(k) match, try to contribute at least enough to get the full match. It is free money.
        """)

    with st.expander("Should I invest or pay off debt first?"):
        st.markdown("""
        This depends on the interest rate of your debt.
        
        - **High interest debt (credit cards, payday loans):** Pay this off first. The interest is higher than what you can earn investing.
        - **Low interest debt (mortgage, student loans):** You can invest while paying this off slowly.
        
        **General rule:** If debt interest is above 6-8%, focus on paying it down first.
        """)

    with st.expander("What if English is not my first language?"):
        st.markdown("""
        That is okay. Many brokerages offer support in multiple languages.
        
        - Fidelity offers Spanish, Chinese, and other languages
        - Schwab offers support in Spanish, Chinese, Korean, and more
        - Many apps have language settings
        
        You can also find investing information in your language on YouTube and community groups. Look for trusted sources, not random influencers.
        """)

    st.divider()
    st.caption(
        "This guide is for educational purposes only. It is not financial advice. Always do your own research."
    )


def render_resource_library():
    st.title("Resources for New Investors")
    st.caption("Trusted websites, books, and tools to help you learn")

    st.markdown("### Websites")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **Free Learning**
        - [Investopedia](https://www.investopedia.com/) - Dictionary and tutorials
        - [Khan Academy Finance](https://www.khanacademy.org/economics-finance-domain) - Free courses
        - [SEC Investor.gov](https://www.investor.gov/) - US government resource
        - [FINRA](https://www.finra.org/investors) - Investor protection
        """)

    with col2:
        st.markdown("""
        **Brokerage Education**
        - [Fidelity Learning Center](https://www.fidelity.com/learning-center)
        - [Schwab Insights](https://www.schwab.com/learn)
        - [Vanguard Investor Education](https://investor.vanguard.com/investor-education/)
        - [Robinhood Learn](https://learn.robinhood.com/)
        """)

    st.markdown("### Books for Beginners")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        - "The Simple Path to Wealth" by JL Collins
        - "The Little Book of Common Sense Investing" by John C. Bogle
        - "I Will Teach You to Be Rich" by Ramit Sethi
        - "The Index Card" by Helaine Olen and Harold Pollack
        """)

    with col2:
        st.markdown("""
        - "A Random Walk Down Wall Street" by Burton Malkiel
        - "The Bogleheads' Guide to Investing" by Taylor Larimore
        - "Rich Dad Poor Dad" by Robert Kiyosaki (good for mindset)
        - "Psychology of Money" by Morgan Housel
        """)

    st.markdown("### Tools")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **Brokerage Accounts (for beginners)**
        - Fidelity - No minimum, good education
        - Vanguard - Low costs, great index funds
        - Charles Schwab - Good customer support
        - Robinhood - Simple app, good for starting
        """)

    with col2:
        st.markdown("""
        **Research Tools**
        - Yahoo Finance - Free stock data
        - TradingView - Charts and analysis
        - Morningstar - Fund research
        - Seeking Alpha - News and analysis
        """)

    st.markdown("### For Immigrant Families")

    st.markdown("""
    - **MyMoney.gov** - US government financial education in multiple languages
    - **Consumer Financial Protection Bureau** - Resources in Spanish, Chinese, Korean, Vietnamese, and more
    - **Local community centers** - Many offer free financial literacy classes
    - **Library** - Many public libraries have free financial education resources
    - **Religious and community organizations** - Often have trusted advisors who understand immigrant perspectives
    """)

    st.markdown("### Important Warning")

    st.warning("""
    **Avoid scams:** If something sounds too good to be true, it probably is.
    
    - No legitimate investment guarantees returns
    - Do not send money to people you do not know
    - Check if the person is registered with FINRA or SEC
    - Be careful with social media "gurus"
    - Never share your account passwords
    """)

    st.divider()
    st.caption(
        "These resources are suggestions, not endorsements. Always do your own research."
    )


def render_ticker_discovery(default_ticker="AAPL"):
    """Render a categorized ticker discovery UI in the sidebar and return the chosen ticker.

    Provides three entry paths:
    - Category: curated groups like Market Average, Tech Giants, Everyday Brands
    - Risk Bucket: representative ETFs/stocks by risk profile
    - Manual: free text ticker input for advanced users
    """
    st.sidebar.markdown("### Ticker Discovery")
    pick_mode = st.sidebar.radio(
        "Pick by", ["Category", "Risk Bucket", "Manual"], index=0
    )

    categories = {
        "The Market Average": ["VOO", "SPY", "VTI"],
        "Tech Giants": ["AAPL", "MSFT", "GOOGL"],
        "Everyday Brands": ["WMT", "KO", "PG"],
    }

    risk_buckets = {
        "Slow & Steady": ["VOO", "VTI"],
        "Balanced": ["VTI", "SPY"],
        "High Growth": ["QQQ", "TSLA", "ARKK"],
    }

    if pick_mode == "Category":
        cat = st.sidebar.selectbox("Category", list(categories.keys()))
        ticker = st.sidebar.selectbox("Pick an example", categories[cat], index=0)
    elif pick_mode == "Risk Bucket":
        bucket = st.sidebar.selectbox("Risk Profile", list(risk_buckets.keys()))
        use_full = st.sidebar.checkbox("Use full basket (recommended)", value=True)
        if use_full:
            # Return a comma-separated list which the data loader understands
            ticker = ",".join(risk_buckets[bucket])
        else:
            ticker = st.sidebar.selectbox(
                "Representative ETF/Stock", risk_buckets[bucket], index=0
            )
    else:
        ticker = st.sidebar.text_input("Stock Ticker", value=default_ticker)

    # Provide a lightweight explanation for beginners
    with st.sidebar.expander("Why these choices?"):
        st.write(
            "Curated groups help beginners discover sensible, diversified options instead of guessing tickers."
        )

    return ticker


__all__ = [
    "plot_equity_curve",
    "plot_drawdown",
    "display_metrics",
    "render_shock_card",
    "render_educational_footer",
    "render_beginner_explanation",
    "render_quant_metrics",
    "render_investing_guide",
    "render_resource_library",
    "render_ticker_discovery",
]
