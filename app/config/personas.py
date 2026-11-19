PERSONAS = {
    "Finance Admin": {
        "menu": [
            "Dashboard",
            "Revenue",
            "Expenses",
            "Vendors",
            "Customers",
            "Data Quality",
            "Jobs",
            "Persona Management",
            "Reports",
        ],
        "permissions": [
            "view_dashboard",
            "view_revenue",
            "view_expenses",
            "view_vendors",
            "view_customers",
            "view_data_quality",
            "run_jobs",
            "manage_personas",
            "view_reports",
        ],
    },

    "CFO": {
        "menu": [
            "Dashboard",
            "Revenue",
            "Expenses",
            "Reports",
        ],
        "permissions": [
            "view_dashboard",
            "view_revenue",
            "view_expenses",
            "view_reports",
        ],
    },

    "Finance Analyst": {
        "menu": [
            "Dashboard",
            "Revenue",
            "Expenses",
            "Vendors",
            "Customers",
            "Data Quality",
            "Reports",
        ],
        "permissions": [
            "view_dashboard",
            "view_revenue",
            "view_expenses",
            "view_vendors",
            "view_customers",
            "view_data_quality",
            "view_reports",
        ],
    },

    "Accounts Payable": {
        "menu": [
            "Dashboard",
            "Expenses",
            "Vendors",
        ],
        "permissions": [
            "view_dashboard",
            "view_expenses",
            "view_vendors",
        ],
    },

    "Accounts Receivable": {
        "menu": [
            "Dashboard",
            "Revenue",
            "Customers",
        ],
        "permissions": [
            "view_dashboard",
            "view_revenue",
            "view_customers",
        ],
    },
}


def get_persona_config(persona):
    return PERSONAS.get(persona)


def has_permission(persona, permission):
    config = get_persona_config(persona)

    if not config:
        return False

    return permission in config["permissions"]


def get_menu(persona):
    config = get_persona_config(persona)

    if not config:
        return []

    return config["menu"]