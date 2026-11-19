
from databricks.sdk import WorkspaceClient

from utils.database import run_query


def get_current_user_email():
    try:
        w = WorkspaceClient()
        user = w.current_user.me()

        return user.user_name.lower().strip()

    except Exception as e:
        raise RuntimeError(
            f"Unable to identify current Databricks user: {e}"
        )


def get_user_persona(user_email):

    # Escape single quotes to safely construct the SQL string
    safe_email = user_email.replace("'", "''")

    query = f"""
        SELECT persona
        FROM finance_management.gold.app_user_personas
        WHERE LOWER(user_email) = LOWER('{safe_email}')
          AND is_active = TRUE
        LIMIT 1
    """

    result = run_query(query)

    if result.empty:
        return None

    return result.iloc[0]["persona"]


def authenticate_user():

    user_email = get_current_user_email()
    persona = get_user_persona(user_email)

    if not persona:
        return {
            "email": user_email,
            "persona": None,
            "authorized": False,
        }

    return {
        "email": user_email,
        "persona": persona,
        "authorized": True,
    }