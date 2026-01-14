import streamlit as st
from sqlalchemy import create_engine, text
import pandas as pd

# engine using Streamlit secrets
engine = create_engine(
    st.secrets["DATABASE_URL"],
    pool_pre_ping=True
)

def get_person_id(name: str) -> int:
    """
    Insert person if not exists, return id.
    Uses ON CONFLICT to ensure unique names.
    """
    with engine.begin() as conn:
        res = conn.execute(
            text("""
            INSERT INTO persons(name)
            VALUES (:name)
            ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
            RETURNING id
            """),
            {"name": name}
        )
        row = res.fetchone()
        return int(row[0])

def insert_loan(p_id, l_date, amount, tenure, interest, emi_start) -> int:
    """
    Insert loan and return loan_id.
    l_date and emi_start can be date objects or ISO strings.
    """
    with engine.begin() as conn:
        res = conn.execute(
            text("""
            INSERT INTO loans
            (person_id, loan_date, amount, tenure, interest, emi_start, active)
            VALUES (:pid, :ld, :amt, :ten, :int, :emi, TRUE)
            RETURNING loan_id
            """),
            {
                "pid": p_id,
                "ld": l_date,
                "amt": amount,
                "ten": tenure,
                "int": interest,
                "emi": emi_start
            }
        )
        row = res.fetchone()
        return int(row[0])

def insert_emi_schedule(loan_id, schedule: list):
    """
    Insert schedule rows (list of dicts).
    """
    with engine.begin() as conn:
        for r in schedule:
            conn.execute(
                text("""
                INSERT INTO emi_schedule
                (loan_id, emi_date, principal, interest, total, balance)
                VALUES (:lid, :ed, :p, :i, :t, :b)
                """),
                {
                    "lid": loan_id,
                    "ed": r["emi_date"],
                    "p": r["principal"],
                    "i": r["interest"],
                    "t": r["total"],
                    "b": r["balance"]
                }
            )

def read_df(query: str, params: dict = None) -> pd.DataFrame:
    """
    Run a query and return a pandas DataFrame.
    Use :param placeholders when passing params (SQLAlchemy text).
    """
    return pd.read_sql(text(query), engine, params=params)
