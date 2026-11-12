import os
import streamlit as st
import pandas as pd

from databricks import sql
from databricks.sdk.core import Config


@st.cache_resource
def get_connection():
    cfg = Config()

    warehouse_id = os.getenv("DATABRICKS_WAREHOUSE_ID")

    if not warehouse_id:
        raise ValueError("SQL Warehouse resource is not configured.")

    hostname = cfg.host.replace("https://", "").replace("http://", "")

    return sql.connect(
        server_hostname=hostname,
        http_path=f"/sql/1.0/warehouses/{warehouse_id}",
        credentials_provider=lambda: cfg.authenticate,
        _use_arrow_native_complex_types=False
    )


@st.cache_data(ttl=300)
def run_query(query):
    conn = get_connection()

    with conn.cursor() as cursor:
        cursor.execute(query)
        return cursor.fetchall_arrow().to_pandas()