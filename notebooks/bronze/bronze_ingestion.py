
from pyspark.sql import functions as F
from pathlib import Path

# --------------------------------------------------
# 1. Configuration
# --------------------------------------------------

CATALOG = "finance_management"
SCHEMA = "bronze"

# Replace this with the actual path of your cloned
# repository in Databricks Workspace.
DATA_DIR = "/Workspace/Users/sakthivel.r@bloomfieldx.com/databricks-finance-management/Source_data/generated_data"

datasets = {
    "customers": "customers.csv",
    "vendors": "vendors.csv",
    "chart_of_accounts": "chart_of_accounts.csv",
    "revenue_transactions": "revenue_transactions.csv",
    "expense_transactions": "expense_transactions.csv",
    "invoices": "invoices.csv",
    "budgets": "budgets.csv",
    "journal_entries": "journal_entries.csv"
}

# --------------------------------------------------
# 2. Create Unity Catalog and Bronze schema
# --------------------------------------------------

spark.sql(f"CREATE CATALOG IF NOT EXISTS {CATALOG}")
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.{SCHEMA}")

print(f"Target: {CATALOG}.{SCHEMA}")

# --------------------------------------------------
# 3. Load CSV files into Bronze Delta tables
# --------------------------------------------------

for table_name, file_name in datasets.items():

    file_path = f"{DATA_DIR}/{file_name}"

    if not Path(file_path).is_file():
        raise FileNotFoundError(
            f"Source CSV not found: {file_path}"
        )

    print(f"\nProcessing: {file_name}")

    # Preserve original CSV values as strings
    df = (
        spark.read
        .format("csv")
        .option("header", "true")
        .option("inferSchema", "false")
        .option("mode", "FAILFAST")
        .load(f"file:{file_path}")
    )

    # Add Bronze ingestion metadata
    df = (
        df
        .withColumn(
            "ingestion_timestamp",
            F.current_timestamp()
        )
        .withColumn(
            "source_file",
            F.col("_metadata.file_path")
        )
    )

    target_table = f"{CATALOG}.{SCHEMA}.{table_name}"

    # Initial implementation: full refresh
    (
        df.write
        .format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(target_table)
    )

    row_count = spark.table(target_table).count()

    print(
        f"Loaded {row_count} records into {target_table}"
    )

print("\nBronze ingestion completed successfully.")
