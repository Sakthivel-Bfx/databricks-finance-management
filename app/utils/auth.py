import streamlit as st
from databricks.sdk import WorkspaceClient

from utils.database import run_query


def get_current_user_email():
    try:
        w = WorkspaceClient()
        user = w.current_user.me()

        st.write("### Databricks Identity Debug")
        st.write("User name:", user.user_name)
        st.write("Display name:", user.display_name)
        st.write("User ID:", user.id)
        st.write("Email details:", user.emails)

        return user.user_name.lower().strip()

    except Exception as e:
        st.error(f"Identity error: {e}")
        raise


def get_user_persona(user_email):

    # Escape single quotes to safely construct the SQL string
    safe_email = user_email.replace("'", "''")

    query = f"""
        SELECT persona
        FROM finance_management.bronze.app_user_personas
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