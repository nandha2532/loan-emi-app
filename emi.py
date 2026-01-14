from dateutil.relativedelta import relativedelta
from decimal import Decimal, ROUND_HALF_UP


def round2(val):
    return float(Decimal(val).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def generate_emi_schedule(
    loan_id,
    loan_amount,
    tenure_months,
    monthly_interest_rate,
    emi_start_date,
    first_month_principal_override=None,
):
    """
    FLAT PRINCIPAL EMI CALCULATION
    - Fixed principal every month
    - Interest on outstanding balance
    - Optional first EMI principal adjustment
    """

    schedule = []
    balance = round2(loan_amount)

    base_principal = round2(loan_amount / tenure_months)

    for i in range(tenure_months):
        emi_no = i + 1
        emi_date = emi_start_date + relativedelta(months=i)

        # Principal logic
        if emi_no == 1 and first_month_principal_override:
            principal = round2(first_month_principal_override)
        elif emi_no == tenure_months:
            principal = balance  # final adjustment
        else:
            principal = base_principal

        interest = round2(balance * (monthly_interest_rate / 100))
        total = round2(principal + interest)

        balance = round2(balance - principal)
        if balance < 0:
            balance = 0

        schedule.append(
            {
                "loan_id": loan_id,
                "emi_no": emi_no,
                "emi_date": emi_date,
                "principal": principal,
                "interest": interest,
                "total": total,
                "balance": balance,
            }
        )

    return schedule
    
