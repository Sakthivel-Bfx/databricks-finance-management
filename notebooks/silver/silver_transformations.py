
from pyspark.sql import functions as F
from pyspark.sql.types import DecimalType

CATALOG = "finance_management"
BRONZE = f"{CATALOG}.bronze"
SILVER = f"{CATALOG}.silver"
QUARANTINE = f"{CATALOG}.silver_quarantine"

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {SILVER}")
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {QUARANTINE}")

# --------------------------------------------------
# Reusable validation and publishing function
# --------------------------------------------------

def publish_silver(df, table_name, primary_key, invalid_condition):

    # Identify invalid records
    invalid_df = (
        df.filter(invalid_condition)
        .withColumn(
            "quarantine_timestamp",
            F.current_timestamp()
        )
        .withColumn(
            "quarantine_reason",
            F.lit("Primary key, data quality or business rule failure")
        )
    )

    # Keep only valid records
    valid_df = df.filter(~invalid_condition)

    # Remove duplicate primary keys from valid records
    duplicate_keys = (
        valid_df.groupBy(primary_key)
        .count()
        .filter(F.col("count") > 1)
        .select(primary_key)
    )

    duplicates = valid_df.join(
        duplicate_keys,
        primary_key,
        "inner"
    )

    invalid_df = invalid_df.unionByName(
        duplicates.withColumn(
            "quarantine_timestamp",
            F.current_timestamp()
        ).withColumn(
            "quarantine_reason",
            F.lit("Duplicate primary key")
        ),
        allowMissingColumns=True
    )

    valid_df = valid_df.join(
        duplicate_keys,
        primary_key,
        "left_anti"
    )

    # Write valid Silver records
    (
        valid_df.write
        .format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(f"{SILVER}.{table_name}")
    )

    # Write quarantined records
    (
        invalid_df.write
        .format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(f"{QUARANTINE}.{table_name}")
    )

    print(
        f"{table_name}: "
        f"Valid={valid_df.count()}, "
        f"Quarantined={invalid_df.count()}"
    )


# --------------------------------------------------
# 1. Customers
# --------------------------------------------------

customers = (
    spark.table(f"{BRONZE}.customers")
    .withColumn("customer_id", F.trim("customer_id"))
    .withColumn("customer_name", F.trim("customer_name"))
    .withColumn("email", F.lower(F.trim("email")))
    .withColumn("created_date", F.to_date("created_date"))
)

publish_silver(
    customers,
    "customers",
    "customer_id",
    F.col("customer_id").isNull() |
    (F.col("customer_id") == "") |
    F.col("customer_name").isNull() |
    F.col("created_date").isNull()
)


# --------------------------------------------------
# 2. Vendors
# --------------------------------------------------

vendors = (
    spark.table(f"{BRONZE}.vendors")
    .withColumn("vendor_id", F.trim("vendor_id"))
    .withColumn("vendor_name", F.trim("vendor_name"))
    .withColumn("email", F.lower(F.trim("email")))
    .withColumn("created_date", F.to_date("created_date"))
)

publish_silver(
    vendors,
    "vendors",
    "vendor_id",
    F.col("vendor_id").isNull() |
    (F.col("vendor_id") == "") |
    F.col("vendor_name").isNull() |
    F.col("created_date").isNull()
)


# --------------------------------------------------
# 3. Chart of Accounts
# --------------------------------------------------

accounts = (
    spark.table(f"{BRONZE}.chart_of_accounts")
    .withColumn("account_id", F.trim("account_id"))
    .withColumn("account_name", F.trim("account_name"))
)

publish_silver(
    accounts,
    "chart_of_accounts",
    "account_id",
    F.col("account_id").isNull() |
    F.col("account_name").isNull() |
    ~F.col("account_type").isin(
        "Asset", "Liability", "Equity", "Revenue", "Expense"
    )
)


# --------------------------------------------------
# 4. Revenue Transactions
# --------------------------------------------------

revenue = (
    spark.table(f"{BRONZE}.revenue_transactions")
    .withColumn("transaction_id", F.trim("transaction_id"))
    .withColumn("transaction_date", F.to_date("transaction_date"))
    .withColumn("amount", F.col("amount").cast(DecimalType(18, 2)))
)

publish_silver(
    revenue,
    "revenue_transactions",
    "transaction_id",
    F.col("transaction_id").isNull() |
    F.col("transaction_date").isNull() |
    F.col("amount").isNull() |
    (F.col("amount") <= 0)
)


# --------------------------------------------------
# 5. Expense Transactions
# --------------------------------------------------

expenses = (
    spark.table(f"{BRONZE}.expense_transactions")
    .withColumn("transaction_id", F.trim("transaction_id"))
    .withColumn("transaction_date", F.to_date("transaction_date"))
    .withColumn("amount", F.col("amount").cast(DecimalType(18, 2)))
)

publish_silver(
    expenses,
    "expense_transactions",
    "transaction_id",
    F.col("transaction_id").isNull() |
    F.col("transaction_date").isNull() |
    F.col("amount").isNull() |
    (F.col("amount") <= 0)
)


# --------------------------------------------------
# 6. Invoices
# --------------------------------------------------

invoices = (
    spark.table(f"{BRONZE}.invoices")
    .withColumn("invoice_id", F.trim("invoice_id"))
    .withColumn("invoice_date", F.to_date("invoice_date"))
    .withColumn("due_date", F.to_date("due_date"))
    .withColumn("invoice_amount", F.col("invoice_amount").cast(DecimalType(18, 2)))
    .withColumn("paid_amount", F.col("paid_amount").cast(DecimalType(18, 2)))
    .withColumn("outstanding_amount", F.col("outstanding_amount").cast(DecimalType(18, 2)))
)

publish_silver(
    invoices,
    "invoices",
    "invoice_id",
    F.col("invoice_id").isNull() |
    F.col("invoice_date").isNull() |
    F.col("due_date").isNull() |
    (F.col("due_date") < F.col("invoice_date")) |
    F.col("invoice_amount").isNull() |
    F.col("paid_amount").isNull() |
    F.col("outstanding_amount").isNull() |
    (F.col("invoice_amount") <= 0) |
    (F.col("paid_amount") < 0) |
    (F.col("outstanding_amount") < 0) |
    (
        F.abs(
            F.col("invoice_amount") -
            F.col("paid_amount") -
            F.col("outstanding_amount")
        ) > F.lit(0.01)
    )
)


# --------------------------------------------------
# 7. Budgets
# --------------------------------------------------

budgets = (
    spark.table(f"{BRONZE}.budgets")
    .withColumn("budget_year", F.col("budget_year").cast("int"))
    .withColumn("budget_month", F.col("budget_month").cast("int"))
    .withColumn("budget_amount", F.col("budget_amount").cast(DecimalType(18, 2)))
)

publish_silver(
    budgets,
    "budgets",
    "budget_id",
    F.col("budget_id").isNull() |
    F.col("budget_amount").isNull() |
    (F.col("budget_amount") < 0) |
    ~F.col("budget_month").between(1, 12)
)


# --------------------------------------------------
# 8. Journal Entries
# --------------------------------------------------

journals = (
    spark.table(f"{BRONZE}.journal_entries")
    .withColumn("journal_date", F.to_date("journal_date"))
    .withColumn("debit", F.col("debit").cast(DecimalType(18, 2)))
    .withColumn("credit", F.col("credit").cast(DecimalType(18, 2)))
)

# Validate each complete journal entry
journal_stats = (
    journals.groupBy("journal_entry_id")
    .agg(
        F.sum("debit").alias("total_debit"),
        F.sum("credit").alias("total_credit"),
        F.count("*").alias("line_count")
    )
    .filter(
        (F.abs(F.col("total_debit") - F.col("total_credit")) > 0.01) |
        (F.col("line_count") < 2)
    )
    .select("journal_entry_id")
)

# Quarantine all lines belonging to an invalid entry
invalid_journals = (
    journals.join(journal_stats, "journal_entry_id", "inner")
    .withColumn("quarantine_timestamp", F.current_timestamp())
    .withColumn(
        "quarantine_reason",
        F.lit("Unbalanced or incomplete journal entry")
    )
)

valid_journals = journals.join(
    journal_stats,
    "journal_entry_id",
    "left_anti"
)

# Also validate individual journal lines
bad_lines = (
    F.col("journal_entry_id").isNull() |
    F.col("journal_date").isNull() |
    F.col("debit").isNull() |
    F.col("credit").isNull() |
    (F.col("debit") < 0) |
    (F.col("credit") < 0) |
    (
        (F.col("debit") > 0) &
        (F.col("credit") > 0)
    ) |
    (
        (F.col("debit") == 0) &
        (F.col("credit") == 0)
    )
)

bad_line_records = valid_journals.filter(bad_lines)

valid_journals = valid_journals.filter(~bad_lines)

invalid_journals = invalid_journals.unionByName(
    bad_line_records.withColumn(
        "quarantine_timestamp", F.current_timestamp()
    ).withColumn(
        "quarantine_reason", F.lit("Invalid journal line")
    ),
    allowMissingColumns=True
)

(
    valid_journals.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(f"{SILVER}.journal_entries")
)

(
    invalid_journals.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(f"{QUARANTINE}.journal_entries")
)

print(
    "Journal entries: "
    f"Valid lines={valid_journals.count()}, "
    f"Quarantined lines={invalid_journals.count()}"
)

print("\nSilver transformation completed.")
