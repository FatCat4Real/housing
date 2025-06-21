import pandas as pd
import calendar 

DEFAULT_HOUSE_PRICE = 4_300_000
DEFAULT_DOWN_PAYMENT = 300_000
DEFAULT_INTEREST_RATE = 4.0
DEFAULT_MONTHLY_PAYMENT = 20_000
DEFAULT_YEARLY_ADD_ON = 50_000
DEFAULT_REFINANCE_CYCLE_YEARS = 0
DEFAULT_RAISE_AFTER_REFINANCE = 0
DEFAULT_START_YEAR = 2026
DEFAULT_START_MONTH = 1


def calculate_loan_schedule_new(start_year, start_month, debt, interest_pct, monthly_payment, yearly_add_on):
    year = start_year
    month = start_month
    left_balance = debt
    period = 0

    starting_balances = []
    remaining_balances = []
    principal_payments = []
    interest_payments = []
    total_payments = []
    add_ons = []
    years = []
    months = []

    while left_balance > 0:
        starting_balances.append(left_balance)
        
        period += 1
        
        # Interest for this period
        days_in_month = calendar.monthrange(year, month)[1]
        interest_to_pay = left_balance * interest_pct * days_in_month / 365

        # Year-end additional payment
        add_on = 0
        if period % 12 == 0:
            add_on = yearly_add_on
        add_ons.append(add_on)
        
        # Principal payment for this period
        total_available_payment = monthly_payment + add_ons[-1]
        principal_available = total_available_payment - interest_to_pay
        principal_payment = min(left_balance, principal_available)

        # Remaining principal
        left_balance -= principal_payment + interest_to_pay
        
        if month == 12:
            month = 1
            year += 1
        else:
            month += 1
        
        remaining_balances.append(left_balance)
        principal_payments.append(principal_payment)
        interest_payments.append(interest_to_pay)
        total_payments.append(principal_payment + interest_to_pay + add_on)
        years.append(year)
        months.append(month)
        
        # Check if remaining balance is decreasing
        if len(remaining_balances) > 1 and remaining_balances[-1] > remaining_balances[-2]:
            raise Exception("Remaining balance is not decreasing, something is wrong")

    df = pd.DataFrame({
        'starting_balance': starting_balances,
        'principal_payment': principal_payments,
        'interest_payment': interest_payments,
        'total_payment': total_payments,
        'add_on': add_ons,
        'remaining_balance': remaining_balances,
        'year': years,
        'month': months
    })
    
    # Add period number and date for better visualization
    df['period'] = range(len(df))
    df['date'] = pd.to_datetime(df[['year', 'month']].assign(day=1))
    df['total_payment'] = df['principal_payment'] + df['interest_payment']
    df['cumulative_interest'] = df['interest_payment'].cumsum()
    df['cumulative_principal'] = df['principal_payment'].cumsum()
    df['cumulative_total'] = df['total_payment'].cumsum()
    
    return df

debt = DEFAULT_HOUSE_PRICE - DEFAULT_DOWN_PAYMENT
interest_pct = DEFAULT_INTEREST_RATE / 100
monthly_payment = DEFAULT_MONTHLY_PAYMENT
yearly_add_on = DEFAULT_YEARLY_ADD_ON

first_period_interest = debt * (interest_pct * 31 / 365)

if first_period_interest > monthly_payment:
    print("Monthly payment is not enough to cover the interest for the first period")
    exit()

df = calculate_loan_schedule_new(
    start_year=DEFAULT_START_YEAR, 
    start_month=DEFAULT_START_MONTH, 
    debt=debt, 
    interest_pct=interest_pct, 
    monthly_payment=monthly_payment, 
    yearly_add_on=yearly_add_on
)

df