from datetime import date
from dateutil.relativedelta import relativedelta
from decimal import Decimal, ROUND_HALF_UP


def round2(value):
    """
    Bank-style rounding to 2 decimal places
    """
    return float(Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def calculate_emi(amount, annual_interest_rate, tenure_months):
    """
    Calculate fixed monthly EMI using reducing balance formula
    """
    if annual_interest_rate == 0:
        return amount / tenure_months

    monthly_rate = annual_interest_rate / 100 / 12

    emi = (
        amount
        * monthly_rate
        * (1 + monthly_rate) ** tenure_months
        / ((1 + monthly_rate) ** tenure_months - 1)
    )

    return round2(emi)


def generate_emi_schedule(
    loan_id,
    amount,
    annual_interest_rate,
    tenure_months,
    emi_start_date,
):
    """
    Generates EMI schedule following REDUCING BALANCE method
    EMI number starts from 1
    """

    emi = calculate_emi(amount, annual_interest_rate, tenure_months)
    monthly_rate = annual_interest_rate / 100 / 12

    balance = amount
    schedule = []

    for i in range(tenure_months):
        emi_no = i + 1  # ✅ FIX: EMI starts from 1

        if annual_interest_rate == 0:
            interest = 0
            principal = emi
        else:
            interest = round2(balance * monthly_rate)
            principal = round2(emi - interest)

        # Final EMI balance adjustment (rounding safety)
        if emi_no == tenure_months:
            principal = balance
            emi_total = principal + interest
            balance = 0
        else:
            balance = round2(balance - principal)
            emi_total = round2(principal + interest)

        emi_date = emi_start_date + relativedelta(months=i)

        schedule.append(
            {
                "loan_id": loan_id,
                "emi_no": emi_no,
                "emi_date": emi_date,
                "principal": principal,
                "interest": interest,
                "total": emi_total,
                "balance": balance,
            }
        )

    return schedule
