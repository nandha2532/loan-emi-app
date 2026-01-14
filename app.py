import streamlit as st
import psycopg2
import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta
import os

# ==============================
# DATABASE CONNECTION (NEON)
# ==============================
def get_connection():
    database_url = os.environ.get("DATABASE_URL")

    if not database_url:
        st.error("DATABASE_URL is missing. Add it in Streamlit → Secrets.")
        st.stop()

    return psycopg2.connect(database_url, sslmode="require")


# ==============================
# DB HELPERS
# ==============================
def get_person_id(conn, name):
    cur = conn.cursor()
    cur.execute("SELECT id FROM persons WHERE name=%s", (name,))
    row = cur.fetchone()

    if row:
        return row[0]

    cur.execute("INSERT INTO persons(name) VALUES(%s) RETURNING id", (name,))
    pid = cur.fetchone()[0]
    conn.commit()
    return pid


def generate_emi_schedule(
    amount,
    months,
    annual_interest,
    start_date,
    emi_override=None
):
    schedule = []

    monthly_principal = round(amount / months, 2)
    balance = amount
    rate = annual_interest / 100 / 12
    emi_date = start_date

    for i in range(1, months + 1):
        interest = round(balance * rate, 2)

        principal = monthly_principal
        if emi_override and i == 1:
            principal = round(emi_override - interest, 2)

        total = round(principal + interest, 2)
        balance = round(balance - principal, 2)

        schedule.append({
            "emi_no": i,
            "emi_date": emi_date,
            "principal": principal,
            "interest": interest,
            "total": total,
            "balance": max(balance, 0)
        })

        emi_date += relativedelta(months=1)

    return schedule


# ==============================
# APP UI
# ==============================
st.set_page_config(page_title="Loan EMI Manager", layout="wide")
st.title("💰 Loan EMI Manager")

menu = st.sidebar.radio(
    "Menu",
    ["New Loan", "Monthly EMI View", "Person Statement"]
)

conn = get_connection()
cur = conn.cursor()

# ==============================
# 1. NEW LOAN
# ==============================
if menu == "New Loan":
    st.header("➕ New Loan")

    person_mode = st.radio("Person", ["Existing", "New Person"])

    cur.execute("SELECT name FROM persons ORDER BY name")
    persons = [r[0] for r in cur.fetchall()]

    if person_mode == "Existing":
        if persons:
            person_name = st.selectbox("Select Person", persons)
        else:
            st.warning("No existing persons. Please add a new person.")
            person_mode = "New Person"

    if person_mode == "New Person":
        person_name = st.text_input("Enter Name")

    loan_date = st.date_input("Loan Date", date.today())
    amount = st.number_input("Loan Amount", min_value=1.0, step=1.0)
    tenure = st.number_input("Tenure (Months)", min_value=1, step=1)
    interest = st.number_input("Annual Interest (%)", min_value=0.0, step=0.1)

    emi_start = loan_date + relativedelta(months=1)
    st.info(f"EMI Starts: {emi_start.strftime('%d-%m-%Y')}")

    st.subheader("EMI Overrides (Optional)")
    emi_override = st.number_input(
        "EMI for Month 1 (leave 0 for auto)",
        min_value=0.0,
        step=1.0
    )
    if emi_override == 0:
        emi_override = None

    if st.button("Generate & Save Loan"):
        if not person_name.strip():
            st.error("Person name is required")
            st.stop()

        pid = get_person_id(conn, person_name.strip())

        cur.execute("""
            INSERT INTO loans
            (person_id, loan_date, amount, tenure, interest, emi_start, active)
            VALUES (%s,%s,%s,%s,%s,%s,true)
            RETURNING loan_id
        """, (pid, loan_date, amount, tenure, interest, emi_start))

        loan_id = cur.fetchone()[0]

        schedule = generate_emi_schedule(
            amount,
            tenure,
            interest,
            emi_start,
            emi_override
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
        st.success("Loan saved successfully 🎉")

# ==============================
# 2. MONTHLY EMI VIEW
# ==============================
elif menu == "Monthly EMI View":
    st.header("📅 Monthly EMI Collection")

    months = pd.read_sql("""
        SELECT DISTINCT to_char(emi_date,'YYYY-MM') AS month
        FROM emi_schedule
        ORDER BY month
    """, conn)

    if months.empty:
        st.info("No EMI data available.")
        st.stop()

    selected = st.selectbox("Select Month", months["month"])

    df = pd.read_sql("""
        SELECT p.name, e.emi_date, e.principal, e.interest, e.total
        FROM emi_schedule e
        JOIN loans l ON e.loan_id=l.loan_id
        JOIN persons p ON l.person_id=p.id
        WHERE to_char(e.emi_date,'YYYY-MM')=%s
    """, conn, params=(selected,))

    df = df.reset_index(drop=True)  # REMOVE 0 INDEX FROM UI

    st.metric("Total Collection", f"₹ {df['total'].sum():,.2f}")
    st.dataframe(df, use_container_width=True)

# ==============================
# 3. PERSON STATEMENT
# ==============================
elif menu == "Person Statement":
    st.header("👤 Person Ledger")

    cur.execute("SELECT name FROM persons ORDER BY name")
    persons = [r[0] for r in cur.fetchall()]

    if not persons:
        st.info("No persons available.")
        st.stop()

    sel = st.selectbox("Select Person", persons)
    pid = get_person_id(conn, sel)

    loans = pd.read_sql("""
        SELECT loan_id, loan_date, amount, tenure, interest, active
        FROM loans
        WHERE person_id=%s
    """, conn, params=(pid,))

    st.subheader("Loans")
    st.dataframe(loans, use_container_width=True)

    history = pd.read_sql("""
        SELECT e.emi_date, e.principal, e.interest, e.total, e.balance
        FROM emi_schedule e
        JOIN loans l ON e.loan_id=l.loan_id
        WHERE l.person_id=%s
        ORDER BY e.emi_date
    """, conn, params=(pid,))

    st.subheader("EMI History")
    st.dataframe(history, use_container_width=True)

    st.download_button(
        "Download Statement CSV",
        history.to_csv(index=False).encode("utf-8"),
        f"{sel}_statement.csv"
    )
    
