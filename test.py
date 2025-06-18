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

def calculate_loan_schedule(debt, interest, monthly_payment, yearly_add_on, refinance_cycle_years=0, raise_after_refinance=0):
    left = debt
    ton = [debt]
    dok = [debt * interest * 31/365]
    paid = [0]
    monthly_payments = [monthly_payment]
    years = [2026]
    months = [1]
    period = 1
    year = 2026
    month = 1
    raise_ = 0

    while left > 0:
        # Interest for this period
        days_in_month = calendar.monthrange(year, month)[1]
        interest_to_pay = left * interest * days_in_month / 365

        # Year-end additional payment
        if period % 12 == 0:
            add_on = yearly_add_on
        else:
            add_on = 0
        
        # Refinance and payment structure change every x years
        if refinance_cycle_years > 0 and period % (12 * refinance_cycle_years) == 0:
            raise_ += raise_after_refinance
        
        # Principal payment for this period
        # Ensure we have enough payment to cover interest, otherwise set principal payment to 0
        total_available_payment = monthly_payment + add_on + raise_
        if total_available_payment <= interest_to_pay:
            # If payment doesn't cover interest, we can only pay what we have
            ton_to_pay = 0
        else:
            # Normal case: payment covers interest plus some principal
            principal_available = total_available_payment - interest_to_pay
            ton_to_pay = min(left, principal_available)

        # Remaining principal
        left -= ton_to_pay

        period += 1
        
        if month == 12:
            month = 1
            year += 1
        else:
            month += 1
        
        ton.append(left)
        paid.append(ton_to_pay)
        dok.append(interest_to_pay)
        monthly_payments.append(monthly_payment + raise_)
        years.append(year)
        months.append(month)

    df = pd.DataFrame({
        'remaining_balance': ton,
        'principal_payment': paid,
        'interest_payment': dok,
        'monthly_payment': monthly_payments,
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
interest = DEFAULT_INTEREST_RATE / 100
monthly_payment = DEFAULT_MONTHLY_PAYMENT
yearly_add_on = DEFAULT_YEARLY_ADD_ON
refinance_cycle_years = DEFAULT_REFINANCE_CYCLE_YEARS
raise_after_refinance = DEFAULT_RAISE_AFTER_REFINANCE

df = calculate_loan_schedule(debt, interest, monthly_payment, yearly_add_on, refinance_cycle_years, raise_after_refinance)

# print(df)