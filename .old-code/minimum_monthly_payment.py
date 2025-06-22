import math
import pandas as pd
from typing import List, Dict, Tuple


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


def calculate_variable_rate_mortgage(loan_amount: float, 
                                   interest_rates: List[float], 
                                   total_years: int) -> Dict[str, any]:
    """
    Calculate monthly mortgage payments with variable interest rates.
    
    Args:
        loan_amount: Total price of house / loan amount
        interest_rates: List of 6 annual interest rates (as decimals) for years 1,2,3,4,5,6+
                       e.g., [0.03, 0.035, 0.04, 0.045, 0.05, 0.055] for 3%, 3.5%, 4%, 4.5%, 5%, 5.5%
        total_years: Total number of years for the mortgage
    
    Returns:
        Dictionary containing:
        - payment_schedule: Detailed month-by-month breakdown
        - total_paid: Total amount paid over the life of the loan
        - total_interest: Total interest paid
        - loan_amount: Original loan amount
    """
    if len(interest_rates) != 6:
        raise ValueError("Must provide exactly 6 interest rates for years 1,2,3,4,5,6+")
    
    payment_schedule = []
    remaining_balance = loan_amount
    total_paid = 0
    
    for year in range(1, total_years + 1):
        # Determine which interest rate to use
        if year <= 5:
            rate_index = year - 1  # Years 1-5 use rates 0-4
        else:
            rate_index = 5  # Year 6+ uses rate 5
        
        current_rate = interest_rates[rate_index]
        remaining_years = total_years - year + 1
        
        # Calculate monthly payment for this year based on remaining balance and years
        monthly_payment = calculate_monthly_payment(remaining_balance, current_rate, remaining_years)
        
        # Calculate month-by-month for this year
        monthly_rate = current_rate / 12
        for month in range(12):
            if remaining_balance <= 0:
                break
                
            interest_payment = remaining_balance * monthly_rate
            principal_payment = min(monthly_payment - interest_payment, remaining_balance)
            
            # Store each month's data
            month_info = {
                'year': year,
                'month': month + 1,
                'payment_number': (year - 1) * 12 + month + 1,
                'interest_rate': current_rate,
                'monthly_payment': monthly_payment,
                'interest_paid': interest_payment,
                'principal_paid': principal_payment,
                'starting_balance': remaining_balance,
                'ending_balance': remaining_balance - principal_payment
            }
            payment_schedule.append(month_info)
            
            remaining_balance -= principal_payment
            total_paid += monthly_payment
            
            if remaining_balance <= 0.01:  # Handle rounding
                remaining_balance = 0
                break
        
        if remaining_balance <= 0:
            break
    
    total_interest = total_paid - loan_amount
    
    return {
        'payment_schedule': payment_schedule,
        'total_paid': total_paid,
        'total_interest': total_interest,
        'loan_amount': loan_amount
    }


def create_payment_dataframe(result: Dict[str, any]) -> pd.DataFrame:
    df = pd.DataFrame(result['payment_schedule'])
    
    # Format the DataFrame for better display
    df['interest_rate_pct'] = df['interest_rate'] * 100
    
    # Round columns
    df = df.round({
        'interest_rate_pct': 3,
        'monthly_payment': 2,
        'interest_paid': 2,
        'principal_paid': 2,
        'starting_balance': 2,
        'ending_balance': 2
    })
    
    # Select and rename columns
    df = df[['payment_number', 'year', 'month', 'interest_rate_pct', 'monthly_payment', 
             'interest_paid', 'principal_paid', 'starting_balance', 'ending_balance']]
    df.columns = ['Payment #', 'Year', 'Month', 'Interest Rate (%)', 'Monthly Payment', 
                  'Interest Paid', 'Principal Paid', 'Starting Balance', 'Ending Balance']
    
    return df


if __name__ == "__main__":
    house_price = 4_300_000
    rates = [0.023, 0.029, 0.035, 0.04495, 0.04495, 0.05495]  # 2.3%, 2.9%, 3.5%, 4.495%, 4.495%, 5.495%
    years = 40
    
    # Calculate mortgage with monthly breakdown
    result = calculate_variable_rate_mortgage(house_price, rates, years)
    
    print(f"Loan Amount: ${result['loan_amount']:,.2f}")
    print(f"Total Paid: ${result['total_paid']:,.2f}")
    print(f"Total Interest: ${result['total_interest']:,.2f}")
    print()
    
    # Create and display DataFrame (first 24 months as example)
    df = create_payment_dataframe(result)
    print(df.to_string(index=False))