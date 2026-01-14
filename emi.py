from datetime import date
from dateutil.relativedelta import relativedelta
import psycopg2
import os

# -------------------------------
# Database connection
# -------------------------------
DATABASE_URL = os.getenv("DATABASE_URL")

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# -------------------------------
# EMI calculation function
# -------------------------------
def generate_emi_schedule(
    loan_id,
    principal_amount,
    annual_interest,
    tenure_months,
    emi_start_date,
    custom_emi=None  # 🔥 NEW: override EMI for all months
):
    """
    Generates EMI schedule and inserts into emi_schedule table
    """

    monthly_rate = annual_interest / (12 * 100)
    balance = principal_amount

    # Auto EMI calculation
    if custom_emi is None:
        emi = (
            principal_amount
            * monthly_rate
            * (1 + monthly_rate) ** tenure_months
        ) / ((1 + monthly_rate) ** tenure_months - 1)
    else:
        emi = custom_emi

    emi = round(emi, 2)

    emi_date = emi_start_date

    for month in range(1, tenure_months + 1):  # ✅ starts from 1
        interest = round(balance * monthly_rate, 2)
        principal = round(emi - interest, 2)

        # Last month adjustment
        if principal > balance:
            principal = balance
            emi = principal + interest

        balance = round(balance - principal, 2)

        cur.execute(
            """
            INSERT INTO emi_schedule
            (loan_id, emi_date, principal, interest, total, balance)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                loan_id,
                emi_date,
                principal,
                interest,
                emi,
                balance
            )
        )

        emi_date += relativedelta(months=1)

    conn.commit()


# -------------------------------
# Example usage
# -------------------------------
if __name__ == "__main__":
    generate_emi_schedule(
        loan_id=1,
        principal_amount=100000,
        annual_interest=12,
        tenure_months=12,
        emi_start_date=date(2024, 1, 1),

        # 🔽 Change this if needed
        custom_emi=None      # auto EMI
        # custom_emi=9000    # fixed EMI for all months
    )

    print("EMI schedule generated successfully.")
    
