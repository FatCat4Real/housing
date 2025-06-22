import pandas as pd
import calendar
import streamlit as st
from .constants import DEFAULT_START_YEAR, DEFAULT_START_MONTH

@st.cache_data
def calculate_loan_schedule_simple(start_year, start_month, debt, interest_pct, monthly_payment, yearly_add_on):
    """Simple loan calculation with fixed interest rate and payment"""
    year = start_year
    month = start_month
    left_principal_balance = debt
    period = 0

    starting_principal_balances = []
    remaining_principal_balances = []
    principal_payments = []
    interest_payments = []
    total_payments = []
    add_ons = []
    years = []
    months = []

    while left_principal_balance > 0:
        starting_principal_balances.append(left_principal_balance)
        
        period += 1
        
        # Interest for this period
        days_in_month = calendar.monthrange(year, month)[1]
        interest_payment = left_principal_balance * interest_pct * days_in_month / 365

        # Year-end additional payment
        add_on = 0
        if period % 12 == 0:
            add_on = yearly_add_on
        add_ons.append(add_on)
        
        # Principal payment for this period
        total_available_payment = monthly_payment + add_ons[-1]
        principal_available = total_available_payment - interest_payment
        
        # Ensure we have enough payment to cover interest, otherwise set principal payment to 0
        if total_available_payment <= interest_payment:
            principal_payment = 0
        else:
            principal_payment = min(left_principal_balance, principal_available)

        # Remaining principal
        left_principal_balance -= principal_payment
        
        if month == 12:
            month = 1
            year += 1
        else:
            month += 1
        
        remaining_principal_balances.append(left_principal_balance)
        principal_payments.append(principal_payment)
        interest_payments.append(interest_payment)
        total_payments.append(principal_payment + interest_payment + add_on)
        years.append(year)
        months.append(month)
        
        # Check if remaining balance is decreasing
        if len(remaining_principal_balances) > 1 and remaining_principal_balances[-1] > remaining_principal_balances[-2]:
            raise Exception("Remaining balance is not decreasing, something is wrong")

    df = pd.DataFrame({
        'starting_principal_balance': starting_principal_balances,
        'principal_payment': principal_payments,
        'interest_payment': interest_payments,
        'total_payment': total_payments,
        'add_on': add_ons,
        'remaining_principal_balance': remaining_principal_balances,
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

@st.cache_data
def calculate_loan_schedule_variable_rates(start_year, start_month, debt, interest_rates_dict, monthly_payments_dict, yearly_add_on):
    """Variable rates loan calculation with different rates and payments by year"""
    year = start_year
    month = start_month
    left_principal_balance = debt
    period = 0
    loan_year = 1  # Track which year of the loan we're in

    starting_principal_balances = []
    remaining_principal_balances = []
    principal_payments = []
    interest_payments = []
    total_payments = []
    add_ons = []
    years = []
    months = []
    applied_rates = []  # Track which rate was applied each month
    applied_payments = []  # Track which payment was applied each month

    def get_interest_rate_for_loan_year(loan_year, rates_dict):
        """Get the appropriate interest rate for the given loan year"""
        if loan_year in rates_dict:
            return rates_dict[loan_year]
        else:
            # Use the 'onwards' rate for years beyond the defined ones
            return rates_dict['onwards']

    def get_monthly_payment_for_loan_year(loan_year, payments_dict):
        """Get the appropriate monthly payment for the given loan year"""
        if loan_year in payments_dict:
            return payments_dict[loan_year]
        else:
            # Use the 'onwards' payment for years beyond the defined ones
            return payments_dict['onwards']

    while left_principal_balance > 0:
        starting_principal_balances.append(left_principal_balance)
        
        period += 1
        
        # Determine current interest rate and monthly payment based on loan year
        current_interest_rate = get_interest_rate_for_loan_year(loan_year, interest_rates_dict)
        current_monthly_payment = get_monthly_payment_for_loan_year(loan_year, monthly_payments_dict)
        applied_rates.append(current_interest_rate * 100)  # Store as percentage for display
        applied_payments.append(current_monthly_payment)  # Store monthly payment for display
        
        # Interest for this period
        days_in_month = calendar.monthrange(year, month)[1]
        interest_payment = left_principal_balance * current_interest_rate * days_in_month / 365

        # Year-end additional payment
        add_on = 0
        if period % 12 == 0:
            add_on = yearly_add_on
            loan_year += 1  # Increment loan year at the end of each 12-month period
        add_ons.append(add_on)
        
        # Principal payment for this period
        total_available_payment = current_monthly_payment + add_ons[-1]
        principal_available = total_available_payment - interest_payment
        
        # Ensure we have enough payment to cover interest, otherwise set principal payment to 0
        if total_available_payment <= interest_payment:
            principal_payment = 0
        else:
            principal_payment = min(left_principal_balance, principal_available)

        # Remaining principal
        left_principal_balance -= principal_payment
        
        remaining_principal_balances.append(left_principal_balance)
        principal_payments.append(principal_payment)
        interest_payments.append(interest_payment)
        total_payments.append(principal_payment + interest_payment + add_on)
        years.append(year)
        months.append(month)

        if month == 12:
            month = 1
            year += 1
        else:
            month += 1
        
        # Check if remaining balance is decreasing
        if len(remaining_principal_balances) > 1 and remaining_principal_balances[-1] > remaining_principal_balances[-2]:
            raise Exception("Remaining balance is not decreasing, something is wrong")

    df = pd.DataFrame({
        'starting_principal_balance': starting_principal_balances,
        'principal_payment': principal_payments,
        'interest_payment': interest_payments,
        'total_payment': total_payments,
        'add_on': add_ons,
        'remaining_principal_balance': remaining_principal_balances,
        'year': years,
        'month': months,
        'applied_rate': applied_rates,
        'applied_payment': applied_payments
    })
    
    # Add period number and date for better visualization
    df['period'] = range(len(df))
    df['date'] = pd.to_datetime(df[['year', 'month']].assign(day=1))
    df['total_payment'] = df['principal_payment'] + df['interest_payment']
    df['cumulative_interest'] = df['interest_payment'].cumsum()
    df['cumulative_principal'] = df['principal_payment'].cumsum()
    df['cumulative_total'] = df['total_payment'].cumsum()
    
    return df

def calculate_monthly_payment(principal: float, annual_rate: float, years: int) -> float:
    """
    Calculate monthly mortgage payment using the standard mortgage formula.
    
    Args:
        principal: Loan amount
        annual_rate: Annual interest rate (as decimal, e.g., 0.05 for 5%)
        years: Number of years for the loan
    
    Returns:
        Monthly payment amount
    """
    if annual_rate == 0:
        return principal / (years * 12)
    
    monthly_rate = annual_rate / 12
    num_payments = years * 12
    
    # Standard mortgage payment formula
    payment = principal * (monthly_rate * (1 + monthly_rate) ** num_payments) / \
              ((1 + monthly_rate) ** num_payments - 1)
    
    return payment

def calculate_top_up_amount(base_payment, top_up_params):
    """Calculate top-up amount based on strategy"""
    if not top_up_params or top_up_params.get("strategy") == "none":
        return 0
    
    strategy = top_up_params.get("strategy")
    amount = top_up_params.get("amount", 0)
    
    if strategy == "fixed":
        # Top up to at least X amount
        return max(0, amount - base_payment)
    elif strategy == "additional":
        # Add X amount to the payment
        return amount
    elif strategy == "percentage":
        # Increase payment by X%
        return base_payment * (amount / 100)
    else:
        return 0

@st.cache_data
def calculate_standard_mortgage_schedule(start_year, start_month, debt, annual_rate, years, yearly_add_on, top_up_params=None):
    """Standard mortgage calculation with fixed interest rate and calculated payments"""
    monthly_payment = calculate_monthly_payment(debt, annual_rate, years)
    
    year = start_year
    month = start_month
    left_principal_balance = debt
    period = 0

    starting_principal_balances = []
    remaining_principal_balances = []
    principal_payments = []
    interest_payments = []
    total_payments = []
    add_ons = []
    years_list = []
    months = []
    calculated_payments = []  # Track the calculated monthly payment
    top_up_amounts = []  # Track the top-up amounts

    while left_principal_balance > 0 and period < (years * 12):
        starting_principal_balances.append(left_principal_balance)
        calculated_payments.append(monthly_payment)
        
        period += 1
        
        # Interest for this period (using monthly rate to match payment calculation)
        monthly_rate = annual_rate / 12
        interest_payment = left_principal_balance * monthly_rate

        # Year-end additional payment
        add_on = 0
        if period % 12 == 0:
            add_on = yearly_add_on
        add_ons.append(add_on)
        
        # Calculate top-up amount based on strategy
        top_up_amount = calculate_top_up_amount(monthly_payment, top_up_params)
        
        # Principal payment for this period
        total_available_payment = monthly_payment + top_up_amount + add_ons[-1]
        principal_available = total_available_payment - interest_payment
        
        # Ensure we have enough payment to cover interest
        if total_available_payment <= interest_payment:
            principal_payment = 0
        else:
            principal_payment = min(left_principal_balance, principal_available)

        # Remaining principal
        left_principal_balance -= principal_payment
        
        remaining_principal_balances.append(left_principal_balance)
        principal_payments.append(principal_payment)
        interest_payments.append(interest_payment)
        total_payments.append(principal_payment + interest_payment + add_on + top_up_amount)
        top_up_amounts.append(top_up_amount)
        years_list.append(year)
        months.append(month)

        if month == 12:
            month = 1
            year += 1
        else:
            month += 1
            
        # Safety check
        if len(remaining_principal_balances) > 1 and remaining_principal_balances[-1] > remaining_principal_balances[-2]:
            raise Exception("Remaining balance is not decreasing, something is wrong")

    df = pd.DataFrame({
        'starting_principal_balance': starting_principal_balances,
        'principal_payment': principal_payments,
        'interest_payment': interest_payments,
        'total_payment': total_payments,
        'add_on': add_ons,
        'top_up': top_up_amounts,
        'remaining_principal_balance': remaining_principal_balances,
        'year': years_list,
        'month': months,
        'calculated_payment': calculated_payments
    })
    
    # Add period number and date for better visualization
    df['period'] = range(len(df))
    df['date'] = pd.to_datetime(df[['year', 'month']].assign(day=1))
    df['total_payment'] = df['principal_payment'] + df['interest_payment']
    df['cumulative_interest'] = df['interest_payment'].cumsum()
    df['cumulative_principal'] = df['principal_payment'].cumsum()
    df['cumulative_total'] = df['total_payment'].cumsum()
    
    return df, monthly_payment

@st.cache_data
def calculate_variable_rate_mortgage_schedule(start_year, start_month, debt, interest_rates_list, years, yearly_add_on, top_up_params=None):
    """Variable rate mortgage calculation based on the original minimum_monthly_payment.py logic"""
    if len(interest_rates_list) != 6:
        raise ValueError("Must provide exactly 6 interest rates for years 1,2,3,4,5,6+")
    
    payment_schedule = []
    remaining_balance = debt
    total_paid = 0
    
    for loan_year in range(1, years + 1):
        # Determine which interest rate to use
        if loan_year <= 5:
            rate_index = loan_year - 1  # Years 1-5 use rates 0-4
        else:
            rate_index = 5  # Year 6+ uses rate 5
        
        current_rate = interest_rates_list[rate_index]
        remaining_years = years - loan_year + 1
        
        # Calculate monthly payment for this year based on remaining balance and years
        monthly_payment = calculate_monthly_payment(remaining_balance, current_rate, remaining_years)
        
        # Calculate month-by-month for this year
        monthly_rate = current_rate / 12
        year_month = 1
        cal_year = start_year + loan_year - 1
        
        for month_in_year in range(12):
            if remaining_balance <= 0:
                break
                
            # Use monthly interest calculation to match payment calculation
            cal_month = month_in_year + start_month
            if cal_month > 12:
                cal_month -= 12
                cal_year += 1
            
            monthly_rate = current_rate / 12
            interest_payment = remaining_balance * monthly_rate
            
            # Add yearly add-on at the end of the year
            add_on = yearly_add_on if month_in_year == 11 else 0
            
            # Calculate top-up amount based on strategy
            top_up_amount = calculate_top_up_amount(monthly_payment, top_up_params)
            
            total_available_payment = monthly_payment + top_up_amount + add_on
            principal_available = total_available_payment - interest_payment
            
            if total_available_payment <= interest_payment:
                principal_payment = 0
            else:
                principal_payment = min(remaining_balance, principal_available)
            
            # Store each month's data
            month_info = {
                'year': cal_year,
                'month': cal_month,
                'payment_number': (loan_year - 1) * 12 + month_in_year + 1,
                'interest_rate': current_rate,
                'monthly_payment': monthly_payment,
                'interest_paid': interest_payment,
                'principal_paid': principal_payment,
                'starting_balance': remaining_balance,
                'ending_balance': remaining_balance - principal_payment,
                'add_on': add_on,
                'top_up': top_up_amount
            }
            payment_schedule.append(month_info)
            
            remaining_balance -= principal_payment
            total_paid += total_available_payment
            
            if remaining_balance <= 0.01:  # Handle rounding
                remaining_balance = 0
                break
        
        if remaining_balance <= 0:
            break
    
    # Convert to the expected DataFrame format
    df = pd.DataFrame({
        'starting_principal_balance': [m['starting_balance'] for m in payment_schedule],
        'principal_payment': [m['principal_paid'] for m in payment_schedule],
        'interest_payment': [m['interest_paid'] for m in payment_schedule],
        'total_payment': [m['principal_paid'] + m['interest_paid'] + m['add_on'] + m['top_up'] for m in payment_schedule],
        'add_on': [m['add_on'] for m in payment_schedule],
        'top_up': [m['top_up'] for m in payment_schedule],
        'remaining_principal_balance': [m['ending_balance'] for m in payment_schedule],
        'year': [m['year'] for m in payment_schedule],
        'month': [m['month'] for m in payment_schedule],
        'applied_rate': [m['interest_rate'] * 100 for m in payment_schedule],
        'calculated_payment': [m['monthly_payment'] for m in payment_schedule]
    })
    
    # Add period number and date for better visualization
    df['period'] = range(len(df))
    df['date'] = pd.to_datetime(df[['year', 'month']].assign(day=1))
    df['total_payment'] = df['principal_payment'] + df['interest_payment']
    df['cumulative_interest'] = df['interest_payment'].cumsum()
    df['cumulative_principal'] = df['principal_payment'].cumsum()
    df['cumulative_total'] = df['total_payment'].cumsum()
    
    return df 