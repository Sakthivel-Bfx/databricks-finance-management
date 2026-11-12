
import csv
import random
from pathlib import Path
from datetime import date, timedelta

# Reproducible synthetic data
random.seed(42)

OUTPUT_DIR = Path('/Workspace/Users/sakthivel.r@bloomfieldx.com/databricks-finance-management/Source_data/generated_data')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def write_csv(filename, records):
    if not records:
        return

    filepath = OUTPUT_DIR / filename

    with open(filepath, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)

    print(f"Generated {len(records)} records: {filepath}")


def random_date(start_year=2023, end_year=2026):
    start = date(start_year, 1, 1)
    end = date(end_year, 12, 31)
    days = (end - start).days
    return (start + timedelta(days=random.randint(0, days))).isoformat()


def generate_customers(count=500):
    customers = []

    for i in range(1, count + 1):
        customers.append({
            "customer_id": f"CUST{i:05d}",
            "customer_name": f"Customer {i:04d}",
            "email": f"customer{i}@example.com",
            "country": random.choice(
                ["USA", "Canada", "UK", "Germany", "India"]
            ),
            "customer_type": random.choice(
                ["Individual", "Business", "Enterprise"]
            ),
            "status": random.choice(["Active", "Active", "Inactive"]),
            "created_date": random_date()
        })

    return customers


def generate_vendors(count=150):
    vendors = []

    for i in range(1, count + 1):
        vendors.append({
            "vendor_id": f"VEND{i:05d}",
            "vendor_name": f"Vendor {i:04d}",
            "email": f"vendor{i}@example.com",
            "country": random.choice(
                ["USA", "Canada", "UK", "Germany", "India"]
            ),
            "vendor_category": random.choice(
                ["Technology", "Logistics", "Marketing", "Operations"]
            ),
            "status": random.choice(["Active", "Active", "Inactive"]),
            "created_date": random_date()
        })

    return vendors


def generate_accounts():
    account_types = {
        "Asset": ["Cash", "Accounts Receivable", "Inventory"],
        "Liability": ["Accounts Payable", "Loans", "Tax Payable"],
        "Equity": ["Share Capital", "Retained Earnings"],
        "Revenue": ["Product Sales", "Service Revenue"],
        "Expense": ["Salaries", "Rent", "Marketing", "Utilities"]
    }

    accounts = []
    account_id = 1000

    for account_type, categories in account_types.items():
        for category in categories:
            for _ in range(1, 6):
                account_id += 1
                accounts.append({
                    "account_id": f"GL{account_id}",
                    "account_name": f"{category} {_}",
                    "account_type": account_type,
                    "account_category": category,
                    "is_active": True
                })

    return accounts


def main():
    customers = generate_customers()
    vendors = generate_vendors()
    accounts = generate_accounts()

    write_csv("customers.csv", customers)
    write_csv("vendors.csv", vendors)
    write_csv("chart_of_accounts.csv", accounts)

    print("\nMaster data generation completed.")


if __name__ == "__main__":
    main()
