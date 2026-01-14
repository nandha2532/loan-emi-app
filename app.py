import streamlit as st
import psycopg2
import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta
import os

# ---------------- DB CONNECTION ----------------
def get_connection():
    return psycopg2.connect(
        host=os.environ["PG_HOST"],
        database=os.environ["PG_DB"],
        user=os.environ["PG_USER"],
        password=os.environ["PG_PASSWORD"],
        port=os.environ["PG_PORT"],
        sslmode="require"
    )

# ---------------- EMI CALCULATION ----------------
def generate_emi_schedule(
    loan_amount, tenure, annual_interest, start_date, emi_overrides=None
):
    balance = loan_amount
    monthly_rate = annual_interest / 12 / 100
    schedule = []

    for month in range(1, tenure + 1):
        principal = round(balance / (tenure - month + 1), 2)
        interest = round(balance * monthly_rate, 2)
        emi = round(principal + interest, 2)

        # Allow manual EMI override
        if emi_overrides and month in emi_overrides:
            emi = emi_overrides[month]
            principal = round(emi - interest, 2)

        balance = round(balance - principal, 2)

        schedule.append({
            "month": month,
            "emi_date": start_date + relativedelta(months=month),
            "principal": principal,
            "interest": interest,
            "total": emi,
            "balance": max(balance, 0)
        })

    return schedule

# ---------------- UI ----------------
st.set_page_config(page_title="Loan EMI App", layout="wide")
st.title("Loan EMI Management")

tab1, tab2 = st.tabs(["Create Loan", "Monthly EMI View"])

# ---------------- CREATE LOAN ----------------
with tab1:
    st.subheader("Create Loan")

    name = st.text_input("Customer Name")

    loan_amount = st.number_input(
        "Loan Amount",
        min_value=1.0,
        value=1.0,
        step=1.0
    )

    tenure = st.number_input(
        "Tenure (Months)",
        min_value=1,
        value=1,
        step=1
    )

    interest = st.number_input(
        "Annual Interest (%)",
        min_value=1.0,
        value=1.0,
        step=0.1
    )

    loan_date = st.date_input("Loan Date", value=date.today())
    emi_start = loan_date

    st.markdown("### EMI Overrides (Optional)")
    emi_overrides = {}

    for i in range(1, tenure + 1):
        override = st.number_input(
            f"EMI for Month {i} (leave default if unchanged)",
            min_value=1.0,
            value=1.0,
            step=1.0,
            key=f"emi_{i}"
        )
        emi_overrides[i] = override

    if st.button("Create Loan"):
        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO persons(name) VALUES(%s) ON CONFLICT (name) DO NOTHING",
            (name,)
        )

        cur.execute("SELECT id FROM persons WHERE name=%s", (name,))
        person_id = cur.fetchone()[0]

        cur.execute("""
            INSERT INTO loans(person_id, loan_date, amount, tenure, interest, emi_start)
            VALUES (%s,%s,%s,%s,%s,%s)
            RETURNING loan_id
        """, (person_id, loan_date, loan_amount, tenure, interest, emi_start))

        loan_id = cur.fetchone()[0]

        schedule = generate_emi_schedule(
            loan_amount, tenure, interest, emi_start, emi_overrides
        )

        for row in schedule:
            cur.execute("""
                INSERT INTO emi_schedule
                (loan_id, emi_date, principal, interest, total, balance)
                VALUES (%s,%s,%s,%s,%s,%s)
            """, (
                loan_id,
                row["emi_date"],
                row["principal"],
                row["interest"],
                row["total"],
                row["balance"]
            ))

        conn.commit()
        conn.close()

        st.success("Loan and EMI schedule created successfully")

# ---------------- MONTHLY VIEW ----------------
with tab2:
    st.subheader("Monthly EMI Collection")

    conn = get_connection()

    df = pd.read_sql("""
        SELECT p.name, e.emi_date, e.principal, e.interest, e.total
        FROM emi_schedule e
        JOIN loans l ON e.loan_id = l.loan_id
        JOIN persons p ON l.person_id = p.id
        ORDER BY e.emi_date
    """, conn)

    conn.close()

    df["month"] = df["emi_date"].dt.to_period("M").astype(str)

    selected_month = st.selectbox(
        "Select Month",
        sorted(df["month"].unique())
    )

    result = df[df["month"] == selected_month].reset_index(drop=True)
    result.index = result.index + 1  # REMOVE 0 FROM UI

    st.metric("Total Collection", f"₹ {result['total'].sum():,.2f}")
    st.dataframe(result, use_container_width=True)
    
