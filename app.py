import streamlit as st
import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta

from db import get_person_id, insert_loan, insert_emi_schedule, read_df
from emi import generate_emi_schedule

st.set_page_config(page_title="Loan EMI Manager", layout="wide")

menu = st.sidebar.selectbox(
    "Menu",
    ["New Loan", "Monthly EMI View", "Person Statement", "Export Reports", "Admin Settings"]
)

# ---------- NEW LOAN ----------
if menu == "New Loan":
    st.header("➕ New Loan")

    person_mode = st.radio("Person", ["Existing", "New Person"])

    # read persons safely
    try:
        persons_df = read_df("SELECT id, name FROM persons")
        persons = persons_df["name"].tolist() if not persons_df.empty else []
    except Exception:
        persons = []

    selected_person = None
    new_name = None

    if person_mode == "Existing":
        if persons:
            selected_person = st.selectbox("Select Person", persons)
        else:
            st.info("No existing persons. Please add a new person.")
            person_mode = "New Person"
    if person_mode == "New Person":
        new_name = st.text_input("Enter Name")

    l_date = st.date_input("Loan Date", value=date.today())
    l_amount = st.number_input("Amount", min_value=1.0, format="%f")
    l_tenure = st.number_input("Tenure (months)", min_value=1, step=1)
    l_int = st.number_input("Interest %", min_value=0.0, format="%f")

    emi_start = l_date + relativedelta(months=1)
    st.info(f"EMI Starts: {emi_start.strftime('%d-%m-%Y')}")

    if st.button("Generate & Save Loan"):
        if (person_mode == "Existing" and selected_person) or (person_mode == "New Person" and new_name):
            name = selected_person if person_mode == "Existing" else new_name
            pid = get_person_id(name)

            # Generate schedule
            schedule = generate_emi_schedule(
                l_amount, int(l_tenure), float(l_int), emi_start
            )

            # Insert loan and schedule
            loan_id = insert_loan(pid, l_date, l_amount, int(l_tenure), l_int, emi_start)
            insert_emi_schedule(loan_id, schedule)

            st.success("Loan Saved Successfully!")
        else:
            st.error("Select or add a person")

# ---------- MONTHLY VIEW ----------
elif menu == "Monthly EMI View":
    st.header("📅 Monthly EMI Collection")

    try:
        months_df = read_df("SELECT DISTINCT to_char(emi_date,'YYYY-MM') AS m FROM emi_schedule ORDER BY m")
        months = months_df["m"].tolist() if not months_df.empty else []
    except Exception:
        months = []

    if months:
        sel_month = st.selectbox("Select Month", months)

        df = read_df("""
            SELECT p.name, e.emi_date, e.principal, e.interest, e.total
            FROM emi_schedule e
            JOIN loans l ON e.loan_id = l.loan_id
            JOIN persons p ON l.person_id = p.id
            WHERE to_char(e.emi_date,'YYYY-MM') = :m
            ORDER BY e.emi_date
        """, {"m": sel_month})

        if not df.empty:
            st.metric("Total Collection", f"₹ {df['total'].sum():,.0f}")
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No records for this month.")
    else:
        st.info("No EMI data available yet.")

# ---------- PERSON STATEMENT ----------
elif menu == "Person Statement":
    st.header("👤 Person Statement")

    try:
        persons_df = read_df("SELECT id, name FROM persons")
    except Exception:
        persons_df = pd.DataFrame(columns=["id", "name"])

    if persons_df.empty:
        st.info("No persons found. Add a loan with a new person first.")
    else:
        sel = st.selectbox("Select Person", persons_df["name"].tolist())
        pid = int(persons_df[persons_df["name"] == sel]["id"].values[0])

        hist = read_df("""
            SELECT l.loan_date, e.emi_date, e.principal, e.interest, e.total, e.balance
            FROM emi_schedule e
            JOIN loans l ON e.loan_id = l.loan_id
            WHERE l.person_id = :pid
            ORDER BY e.emi_date
        """, {"pid": pid})

        st.subheader("EMI History")
        st.dataframe(hist, use_container_width=True)
        st.download_button(
            "Download CSV",
            hist.to_csv(index=False).encode("utf-8"),
            f"{sel}_statement.csv"
        )

# ---------- EXPORT ----------
elif menu == "Export Reports":
    st.header("📂 Export Full Data")

    if st.button("Export EMI Schedule"):
        try:
            df = read_df("SELECT * FROM emi_schedule")
            st.download_button(
                "Download CSV",
                df.to_csv(index=False).encode("utf-8"),
                "emi_schedule.csv"
            )
        except Exception as e:
            st.error(f"Failed to export: {e}")

# ---------- ADMIN SETTINGS ----------
elif menu == "Admin Settings":
    st.header("⚙️ Admin")
    # store basic defaults in session_state
    if "def_tenure" not in st.session_state:
        st.session_state.def_tenure = 12
    if "def_int" not in st.session_state:
        st.session_state.def_int = 12.0

    new_t = st.number_input("Default Tenure", value=st.session_state.def_tenure, min_value=1)
    new_i = st.number_input("Default Interest", value=float(st.session_state.def_int), min_value=0.0)

    if st.button("Update Defaults"):
        st.session_state.def_tenure = int(new_t)
        st.session_state.def_int = float(new_i)
        st.success("Updated!")
