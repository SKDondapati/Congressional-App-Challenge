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
    st.plotly_chart(fig, use_container_width=True)
    return None


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
    st.plotly_chart(fig, use_container_width=True)
    return None


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


def render_beginner_explanation(results_dict, ticker):
    st.markdown(f"### Beginner Summary for {ticker}")
    st.write("This summary explains results in plain language so you can learn what happened.")
    for name, (sim, stats) in results_dict.items():
        st.markdown(f"**{name}**")
        st.write(f"Final value: ${stats.get('final_value', 0):,.2f}")
        st.write(f"Total return: {stats.get('total_return', 0):.2%}")
        dd = stats.get('max_drawdown', 0.0)
        st.write(f"Maximum drawdown: {dd:.2%}")
        if dd < -0.2:
            st.warning("This strategy had large losses during a stress period. Consider diversifying and using smaller position sizes.")
        st.markdown("---")


def render_quant_metrics(stats):
    st.markdown("### Quant Metrics")
    display_metrics(stats)
    st.markdown("**Notes:**")
    st.write("Sharpe ratio measures risk-adjusted return. Max drawdown shows peak loss from a high point.")


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
    st.caption("This guide is for educational purposes only. It is not financial advice. Always do your own research.")


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
    st.caption("These resources are suggestions, not endorsements. Always do your own research.")


__all__ = [
    'plot_equity_curve',
    'plot_drawdown',
    'display_metrics',
    'render_shock_card',
    'render_educational_footer',
    'render_beginner_explanation',
    'render_quant_metrics',
    'render_investing_guide',
    'render_resource_library',
]