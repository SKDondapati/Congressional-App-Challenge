import streamlit as st


def render_investing_guide():
    st.title("How to Start Investing in the US Stock Market")
    st.caption("A beginner guide for learning the basics")

    st.markdown(
        "Investing can feel unfamiliar when you are starting out. These short "
        "sections explain common terms. They are educational, not personal advice."
    )

    with st.expander("What is a stock?"):
        st.write(
            "A stock is a small ownership share in a company. Its price can rise "
            "or fall, and you can lose money."
        )

    with st.expander("What is an index fund or ETF?"):
        st.write(
            "An index fund or ETF holds a group of investments. A broad fund can "
            "spread company-specific risk, but it can still fall when the market falls."
        )
        st.write("Examples include SPY, which tracks the S&P 500, and VTI, which tracks the US stock market.")

    with st.expander("What does buy and hold mean?"):
        st.write(
            "Buy and hold means staying invested instead of frequently switching "
            "between cash and an investment. It does not prevent losses."
        )

    with st.expander("What is a moving-average strategy?"):
        st.write(
            "This example holds the investment when its short moving average is "
            "above its long moving average, and otherwise holds cash. Past signals "
            "do not predict future prices."
        )

    with st.expander("What is risk?"):
        st.write(
            "Risk includes the chance and size of losses. Diversification can lower "
            "some company-specific risk, but it cannot remove market risk."
        )

    with st.expander("What are a 401(k) and IRA?"):
        st.write(
            "These are common US retirement account types with tax rules that depend "
            "on the account and a person's situation. An employer may offer a 401(k) "
            "match; check the plan details."
        )

    with st.expander("Should I invest or pay off debt first?"):
        st.write(
            "That depends on the debt's interest rate, fees, emergency savings, and "
            "your needs. High-interest debt can be expensive. Consider a qualified "
            "financial counselor for personal guidance."
        )

    st.caption("This guide is for education only, not financial advice.")


def render_resource_library():
    st.title("Resources for New Investors")
    st.caption("These links are educational suggestions, not endorsements.")

    st.markdown("### Free learning")
    st.markdown(
        "- [SEC Investor.gov](https://www.investor.gov/)\n"
        "- [FINRA for Investors](https://www.finra.org/investors)\n"
        "- [Khan Academy Finance](https://www.khanacademy.org/economics-finance-domain)\n"
        "- [Consumer Financial Protection Bureau](https://www.consumerfinance.gov/consumer-tools/)"
    )

    st.markdown("### Books")
    st.markdown(
        "- *The Simple Path to Wealth* by JL Collins\n"
        "- *The Little Book of Common Sense Investing* by John C. Bogle\n"
        "- *The Psychology of Money* by Morgan Housel\n"
        "- *A Random Walk Down Wall Street* by Burton Malkiel"
    )

    st.warning(
        "Be cautious of guaranteed-return claims and requests to share account "
        "passwords. Verify financial professionals through official sources."
    )