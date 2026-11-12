import streamlit as st
from utils.database import run_query

st.set_page_config(
    page_title="Finance Management",
    page_icon="💰",
    layout="wide"
)

st.title("Finance Management Dashboard")
st.caption("Financial overview powered by Databricks Gold tables")

try:
    # Revenue, expenses and profit by currency
    pl_query = """
        SELECT
            currency,
            SUM(total_revenue) AS total_revenue,
            SUM(total_expenses) AS total_expenses,
            SUM(gross_profit) AS gross_profit
        FROM finance_management.gold.profit_loss_summary
        GROUP BY currency
        ORDER BY currency
    """

    pl_df = run_query(pl_query)

    st.subheader("Profit and Loss Overview")

    if not pl_df.empty:
        for _, row in pl_df.iterrows():
            st.markdown(f"### Currency: {row['currency']}")

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Revenue",
                f"{row['total_revenue']:,.2f}"
            )

            col2.metric(
                "Expenses",
                f"{row['total_expenses']:,.2f}"
            )

            col3.metric(
                "Gross Profit",
                f"{row['gross_profit']:,.2f}"
            )

    else:
        st.info("No profit and loss data available.")

    # Accounts receivable
    st.divider()
    st.subheader("Accounts Receivable")

    
    ar_query = """
        SELECT
            currency,
            SUM(invoice_amount) AS invoice_amount,
            SUM(paid_amount) AS paid_amount,
            SUM(outstanding_amount) AS outstanding_amount
        FROM finance_management.gold.accounts_receivable_summary
        GROUP BY currency
        ORDER BY currency
    """

    ar_df = run_query(ar_query)

    if not ar_df.empty:
        st.dataframe(
            ar_df,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No accounts receivable data available.")

    # Monthly financial trends
    st.divider()
    st.subheader("Monthly Financial Trends")

    trend_query = """
        SELECT
            transaction_year,
            transaction_month,
            currency,
            SUM(total_revenue) AS revenue,
            SUM(total_expenses) AS expenses,
            SUM(gross_profit) AS profit
        FROM finance_management.gold.profit_loss_summary
        GROUP BY
            transaction_year,
            transaction_month,
            currency
        ORDER BY
            transaction_year,
            transaction_month,
            currency
    """

    trend_df = run_query(trend_query)

    if not trend_df.empty:
        selected_currency = st.selectbox(
            "Select Currency",
            sorted(trend_df["currency"].dropna().unique())
        )

        currency_df = trend_df[
            trend_df["currency"] == selected_currency
        ]

        currency_df["period"] = (
            currency_df["transaction_year"].astype(str)
            + "-"
            + currency_df["transaction_month"].astype(str).str.zfill(2)
        )

        st.line_chart(
            currency_df.set_index("period")[
                ["revenue", "expenses", "profit"]
            ]
        )

except Exception as e:
    st.error("Unable to load Finance Dashboard.")
    st.exception(e)