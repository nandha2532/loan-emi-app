from dateutil.relativedelta import relativedelta

def generate_emi_schedule(amount, tenure, interest, start_date, first_month_prin=0):
    """
    amount: principal amount (float)
    tenure: months (int)
    interest: annual rate in percent (float)
    start_date: datetime.date (first EMI date)
    returns: list of dicts with keys emi_date (YYYY-MM-DD), principal, interest, total, balance
    """
    rate = float(interest) / 12.0 / 100.0
    if rate == 0:
        emi = float(amount) / int(tenure)
    else:
        emi = float(amount) * rate * (1 + rate) ** tenure / ((1 + rate) ** tenure - 1)

    balance = float(amount)
    schedule = []

    for i in range(int(tenure)):
        interest_amt = balance * rate
        principal = emi - interest_amt
        # optionally handle first_month_prin (not used actively here)
        balance -= principal

        emi_date = (start_date + relativedelta(months=i)).strftime("%Y-%m-%d")

        schedule.append({
            "emi_date": emi_date,
            "principal": round(principal, 2),
            "interest": round(interest_amt, 2),
            "total": round(emi, 2),
            "balance": round(max(balance, 0), 2)
        })

    return schedule
