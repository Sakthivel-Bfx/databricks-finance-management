
import csv
import random
from pathlib import Path
from datetime import date, timedelta
from decimal import Decimal

random.seed(42)

BASE_DIR = Path('/Workspace/Users/sakthivel.r@bloomfieldx.com/databricks-finance-management/Source_data/') 
OUTPUT_DIR = BASE_DIR / "generated_data"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TODAY = date.today()

DEPARTMENTS = [
    "Finance", "Sales", "Marketing",
    "Operations", "Technology"
]

CURRENCIES = ["USD", "EUR", "GBP", "INR", "CAD"]


def read_csv(filename):
    with open(OUTPUT_DIR / filename, newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def write_csv(filename, records):
    if not records:
        return

    with open(
        OUTPUT_DIR / filename,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(file, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)

    print(f"Generated {len(records)} records: {filename}")


def random_date():
    start = date(2023, 1, 1)
    days = (TODAY - start).days
    return (start + timedelta(days=random.randint(0, days))).isoformat()


def random_amount(minimum=100, maximum=50000):
    return str(Decimal(str(random.uniform(
        minimum, maximum
    ))).quantize(Decimal("0.01")))


def generate_invoices(customers, count=3000):
    invoices = []

    for i in range(1, count + 1):
        amount = Decimal(random_amount(500, 25000))
        status = random.choice(
            ["Paid", "Paid", "Pending", "Overdue", "Partially Paid"]
        )

        paid_amount = {
            "Paid": amount,
            "Pending": Decimal("0"),
            "Overdue": Decimal("0"),
            "Partially Paid": (amount * Decimal("0.50")).quantize(
                Decimal("0.01")
            )
        }[status]

        invoices.append({
            "invoice_id": f"INV{i:06d}",
            "customer_id": random.choice(customers)["customer_id"],
            "invoice_date": random_date(),
            "due_date": random_date(),
            "invoice_amount": str(amount),
            "paid_amount": str(paid_amount),
            "outstanding_amount": str(amount - paid_amount),
            "currency": random.choice(CURRENCIES),
            "status": status
        })

    return invoices


def generate_revenue(customers, accounts, count=10000):
    revenue_accounts = [
        a for a in accounts if a["account_type"] == "Revenue"
    ]

    records = []

    for i in range(1, count + 1):
        records.append({
            "transaction_id": f"REV{i:07d}",
            "customer_id": random.choice(customers)["customer_id"],
            "account_id": random.choice(revenue_accounts)["account_id"],
            "transaction_date": random_date(),
            "amount": random_amount(100, 50000),
            "currency": random.choice(CURRENCIES),
            "transaction_type": "Revenue"
        })

    return records


def generate_expenses(vendors, accounts, count=5000):
    expense_accounts = [
        a for a in accounts if a["account_type"] == "Expense"
    ]

    records = []

    for i in range(1, count + 1):
        records.append({
            "transaction_id": f"EXP{i:07d}",
            "vendor_id": random.choice(vendors)["vendor_id"],
            "account_id": random.choice(expense_accounts)["account_id"],
            "transaction_date": random_date(),
            "amount": random_amount(50, 30000),
            "currency": random.choice(CURRENCIES),
            "transaction_type": "Expense"
        })

    return records


def generate_budgets(accounts):
    budget_accounts = [
        a for a in accounts
        if a["account_type"] in ["Revenue", "Expense"]
    ][:10]

    budgets = []
    budget_id = 1

    for month in range(1, 13):
        for department in DEPARTMENTS:
            for account in budget_accounts:
                budgets.append({
                    "budget_id": f"BUD{budget_id:06d}",
                    "budget_year": 2026,
                    "budget_month": month,
                    "department": department,
                    "account_id": account["account_id"],
                    "budget_amount": random_amount(10000, 100000)
                })
                budget_id += 1

    return budgets


def generate_journals(revenue, expenses, accounts):
    account_lookup = {
        a["account_category"]: a["account_id"]
        for a in accounts
    }

    ar_account = account_lookup["Accounts Receivable"]
    ap_account = account_lookup["Accounts Payable"]

    journals = []
    journal_id = 1

    def add_journal(transaction, debit_account, credit_account):
        nonlocal journal_id

        amount = Decimal(transaction["amount"])
        entry_id = f"JE{journal_id:07d}"

        common = {
            "journal_entry_id": entry_id,
            "journal_date": transaction["transaction_date"],
            "currency": transaction["currency"],
            "reference_id": transaction["transaction_id"]
        }

        journals.append({
            **common,
            "line_number": 1,
            "account_id": debit_account,
            "debit": str(amount),
            "credit": "0.00"
        })

        journals.append({
            **common,
            "line_number": 2,
            "account_id": credit_account,
            "debit": "0.00",
            "credit": str(amount)
        })

        journal_id += 1

    for transaction in revenue:
        add_journal(
            transaction,
            ar_account,
            transaction["account_id"]
        )

    for transaction in expenses:
        add_journal(
            transaction,
            transaction["account_id"],
            ap_account
        )

    return journals


def validate_journals(journals):
    totals = {}

    for row in journals:
        entry_id = row["journal_entry_id"]

        if entry_id not in totals:
            totals[entry_id] = {
                "debit": Decimal("0"),
                "credit": Decimal("0")
            }

        totals[entry_id]["debit"] += Decimal(row["debit"])
        totals[entry_id]["credit"] += Decimal(row["credit"])

    unbalanced = [
        entry_id for entry_id, values in totals.items()
        if values["debit"] != values["credit"]
    ]

    if unbalanced:
        raise ValueError(
            f"Unbalanced journal entries found: {unbalanced[:10]}"
        )

    print(f"Validated {len(totals)} balanced journal entries.")


def main():
    customers = read_csv("customers.csv")
    vendors = read_csv("vendors.csv")
    accounts = read_csv("chart_of_accounts.csv")

    invoices = generate_invoices(customers)
    revenue = generate_revenue(customers, accounts)
    expenses = generate_expenses(vendors, accounts)
    budgets = generate_budgets(accounts)

    journals = generate_journals(
        revenue, expenses, accounts
    )

    validate_journals(journals)

    write_csv("invoices.csv", invoices)
    write_csv("revenue_transactions.csv", revenue)
    write_csv("expense_transactions.csv", expenses)
    write_csv("budgets.csv", budgets)
    write_csv("journal_entries.csv", journals)

    print("\nAll financial transaction datasets generated successfully.")


if __name__ == "__main__":
    main()
