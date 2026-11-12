import streamlit as st
import pandas as pd

from utils.database import run_query

st.set_page_config(
    page_title="Expense Analysis",
    page_icon="💳",
    layout="wide"
)

st.title("Expense Analysis")
st.caption("Expense performance and vendor transaction insights")

TABLE = "finance_management.gold.fact_expense"

try:
    # Load available filters
    filters_df = run_query(f"""
        SELECT DISTINCT currency, transaction_year
        FROM {TABLE}
        ORDER BY currency, transaction_year
    """)

    currencies = sorted(
        filters_df["currency"].dropna().unique().tolist()
    )
    years = sorted(
        filters_df["transaction_year"].dropna().astype(int).unique().tolist()
    )

    col1, col2 = st.columns(2)

    with col1:
        currency = st.selectbox(
            "Currency",
            ["All"] + currencies
        )

    with col2:
        year = st.selectbox(
            "Year",
            ["All"] + years
        )

    conditions = []

    if currency != "All":
        safe_currency = currency.replace("'", "''")
        conditions.append(f"currency = '{safe_currency}'")

    if year != "All":
        conditions.append(f"transaction_year = {int(year)}")

    where_clause = (
        "WHERE " + " AND ".join(conditions)
        if conditions else ""
    )

    # KPI summary
    kpi_df = run_query(f"""
        SELECT
            COUNT(*) AS transaction_count,
            COALESCE(SUM(amount), 0) AS total_expenses,
            COALESCE(AVG(amount), 0) AS average_expense
        FROM {TABLE}
        {where_clause}
    """)

    kpi = kpi_df.iloc[0]

    st.subheader("Expense Overview")

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Total Expenses",
        f"{float(kpi['total_expenses']):,.2f}"
    )
    c2.metric(
        "Transactions",
        f"{int(kpi['transaction_count']):,}"
    )
    c3.metric(
        "Average Expense",
        f"{float(kpi['average_expense']):,.2f}"
    )

    # Monthly expense trend
    st.divider()
    st.subheader("Monthly Expense Trend")

    monthly_df = run_query(f"""
        SELECT
            transaction_year,
            transaction_month,
            SUM(amount) AS expenses
        FROM {TABLE}
        {where_clause}
        GROUP BY transaction_year, transaction_month
        ORDER BY transaction_year, transaction_month
    """)

    if not monthly_df.empty:
        monthly_df["period"] = (
            monthly_df["transaction_year"].astype(str)
            + "-"
            + monthly_df["transaction_month"].astype(str).str.zfill(2)
        )

        st.line_chart(
            monthly_df.set_index("period")["expenses"]
        )

    # Expenses by vendor
    st.divider()
    st.subheader("Top 10 Vendors by Expenses")

    vendor_df = run_query(f"""
        SELECT
            vendor_id,
            SUM(amount) AS expenses,
            COUNT(*) AS transaction_count
        FROM {TABLE}
        {where_clause}
        GROUP BY vendor_id
        ORDER BY expenses DESC
        LIMIT 10
    """)

    if not vendor_df.empty:
        st.bar_chart(
            vendor_df.set_index("vendor_id")["expenses"]
        )
        st.dataframe(
            vendor_df,
            use_container_width=True,
            hide_index=True
        )

    # Expenses by account
    st.divider()
    st.subheader("Expenses by Account")

    account_df = run_query(f"""
        SELECT
            account_id,
            SUM(amount) AS expenses
        FROM {TABLE}
        {where_clause}
        GROUP BY account_id
        ORDER BY expenses DESC
    """)

    if not account_df.empty:
        st.dataframe(
            account_df,
            use_container_width=True,
            hide_index=True
        )

    # Transaction details
    st.divider()
    st.subheader("Expense Transactions")

    details_df = run_query(f"""
        SELECT
            transaction_id,
            vendor_id,
            account_id,
            transaction_date,
            amount,
            currency,
            transaction_type
        FROM {TABLE}
        {where_clause}
        ORDER BY transaction_date DESC
        LIMIT 500
    """)

    st.dataframe(
        details_df,
        use_container_width=True,
        hide_index=True
    )

except Exception as e:
    st.error("Unable to load Expense Analysis.")
    st.exception(e)