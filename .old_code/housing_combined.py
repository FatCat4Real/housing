import pandas as pd
import calendar
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List, Dict

# Default values
DEFAULT_HOUSE_PRICE = 4_300_000
DEFAULT_DOWN_PAYMENT = 0
DEFAULT_INTEREST_RATE = 4.0
DEFAULT_MONTHLY_PAYMENT = 20_000
DEFAULT_YEARLY_ADD_ON = 50_000
DEFAULT_REFINANCE_CYCLE_YEARS = 0
DEFAULT_RAISE_AFTER_REFINANCE = 0
DEFAULT_START_YEAR = 2026
DEFAULT_START_MONTH = 1

st.set_page_config(
    page_title='🏠 House Loan Planning Calculator',
    layout='wide',
    initial_sidebar_state='expanded'
)

# Custom CSS for better styling (theme-aware)
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .metric-card {
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
    }
    .interest-rate-section {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e9ecef;
        margin: 1rem 0;
    }
    .sidebar-info {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        border-left: 4px solid #667eea;
    }
</style>
""", unsafe_allow_html=True)



# Main header
st.markdown("""
<div class="main-header">
    <h1 style="color: white; text-align: center; margin: 0;">
        🏠 House Loan Planning Calculator
    </h1>
    <p style="color: white; text-align: center; margin: 0.5rem 0 0 0;">
        Plan your mortgage payments with detailed analysis and visualizations
    </p>
</div>
""", unsafe_allow_html=True)

# Shared calculation functions
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

# Shared visualization functions
def render_summary_metrics(df, debt):
    """Render the summary metrics section"""
    total_months = len(df)
    total_full_years = int(total_months / 12)
    total_full_months = total_months - (total_full_years * 12)
    total_interest = df['interest_payment'].sum()
    total_principal = df['principal_payment'].sum()
    total_paid = total_interest + total_principal

    st.markdown("## 📈 Loan Summary")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("⏱️ Total Duration", f"{total_full_years}y {total_full_months}m")
    with col2:
        st.metric("💰 Total Interest", f"฿{total_interest:,.0f}")
    with col3:
        st.metric("💸 Total Paid", f"฿{total_paid:,.0f}")
    with col4:
        effective_rate = (total_interest / debt) * 100
        st.metric("📊 Effective Rate", f"{effective_rate:.1f}%")
    
    return total_interest, total_principal

def render_visualizations(df, mode="simple"):
    """Render the payment schedule"""
    st.markdown("## 📊 Payment Schedule")
    
    display_df = df.copy()
    display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
    
    if mode == "variable":
        # Include rate and payment columns for variable mode
        display_df = display_df[['date', 'starting_principal_balance', 'applied_rate', 'applied_payment', 'principal_payment', 'interest_payment', 'total_payment', 'add_on', 'remaining_principal_balance']]
        display_df.columns = ['Date', 'Starting Balance (฿)', 'Rate (%)', 'Monthly Payment (฿)', 'Principal (฿)', 'Interest (฿)', 'Total Payment (฿)', 'Add-on (฿)', 'Remaining Balance (฿)']
        # Format rate
        display_df['Rate (%)'] = display_df['Rate (%)'].apply(lambda x: f"{x:.3f}%")
        format_cols = ['Starting Balance (฿)', 'Monthly Payment (฿)', 'Principal (฿)', 'Interest (฿)', 'Total Payment (฿)', 'Add-on (฿)', 'Remaining Balance (฿)']
    elif mode == "standard" or mode == "variable_standard":
        # Include calculated payment column for standard mortgage modes
        if 'applied_rate' in display_df.columns:
            # Variable rate standard mortgage
            display_df = display_df[['date', 'starting_principal_balance', 'applied_rate', 'calculated_payment', 'principal_payment', 'interest_payment', 'total_payment', 'add_on', 'top_up', 'remaining_principal_balance']]
            display_df.columns = ['Date', 'Starting Balance (฿)', 'Rate (%)', 'Calculated Payment (฿)', 'Principal (฿)', 'Interest (฿)', 'Total Payment (฿)', 'Add-on (฿)', 'Top-up (฿)', 'Remaining Balance (฿)']
            # Format rate
            display_df['Rate (%)'] = display_df['Rate (%)'].apply(lambda x: f"{x:.3f}%")
            format_cols = ['Starting Balance (฿)', 'Calculated Payment (฿)', 'Principal (฿)', 'Interest (฿)', 'Total Payment (฿)', 'Add-on (฿)', 'Top-up (฿)', 'Remaining Balance (฿)']
        else:
            # Fixed rate standard mortgage
            display_df = display_df[['date', 'starting_principal_balance', 'calculated_payment', 'principal_payment', 'interest_payment', 'total_payment', 'add_on', 'top_up', 'remaining_principal_balance']]
            display_df.columns = ['Date', 'Starting Balance (฿)', 'Calculated Payment (฿)', 'Principal (฿)', 'Interest (฿)', 'Total Payment (฿)', 'Add-on (฿)', 'Top-up (฿)', 'Remaining Balance (฿)']
            format_cols = ['Starting Balance (฿)', 'Calculated Payment (฿)', 'Principal (฿)', 'Interest (฿)', 'Total Payment (฿)', 'Add-on (฿)', 'Top-up (฿)', 'Remaining Balance (฿)']
    else:
        # Simple mode without rate and payment columns
        display_df = display_df[['date', 'starting_principal_balance', 'principal_payment', 'interest_payment', 'total_payment', 'add_on', 'remaining_principal_balance']]
        display_df.columns = ['Date', 'Starting Balance (฿)', 'Principal (฿)', 'Interest (฿)', 'Total Payment (฿)', 'Add-on (฿)', 'Remaining Balance (฿)']
        format_cols = ['Starting Balance (฿)', 'Principal (฿)', 'Interest (฿)', 'Total Payment (฿)', 'Add-on (฿)', 'Remaining Balance (฿)']
    
    # Format numbers
    for col in format_cols:
        display_df[col] = display_df[col].apply(lambda x: f"฿{x:,.0f}")
    
    st.dataframe(display_df, use_container_width=True, height=400)



# Main application logic
st.markdown("## 📊 Loan Parameters")

# Property Information
st.markdown("### 🏡 Property Information")
col1, col2, col3 = st.columns(3)
with col1:
    house_price = st.number_input("🏠 Full House Price (฿)", value=DEFAULT_HOUSE_PRICE, step=100_000, format="%d")
with col2:
    down = st.number_input("💰 Down Payment (฿)", value=DEFAULT_DOWN_PAYMENT, step=100_000, format="%d")
with col3:
    calculator_mode = st.selectbox(
        "🧮 Calculation Method",
        options=["Standard Mortgage Calculator", "Manual Payment Input (Fixed Interest Rates)", "Manual Payment Input (Variable Interest Rates)"],
        help="Standard: Calculated payments using mortgage formula. Manual Fixed: Fixed payments you choose with single rate. Manual Variable: Fixed payments you choose with different rates by year."
    )

if calculator_mode == "Manual Payment Input (Fixed Interest Rates)":
    # Simple Calculator Mode
    
    # Interest Rate (moved out of Property Information)
    st.markdown("### 📈 Interest Rate")
    interest = st.number_input("📈 Interest Rate (%)", value=DEFAULT_INTEREST_RATE, step=0.1, format="%.1f")
    interest = interest / 100

    # Payment Structure
    st.markdown("### 💳 Payment Structure")
    col1, col2 = st.columns(2)
    with col1:
        monthly_payment = st.number_input("💵 Monthly Payment (฿)", value=DEFAULT_MONTHLY_PAYMENT, step=1000, format="%d")
    with col2:
        yearly_add_on = st.number_input("📈 Yearly Add-on (฿)", value=DEFAULT_YEARLY_ADD_ON, step=10_000, format="%d")

    debt = house_price - down

    st.markdown("---")

    # Calculate loan schedule
    with st.spinner('Calculating loan schedule...'):
        df = calculate_loan_schedule_simple(
            start_year=DEFAULT_START_YEAR, 
            start_month=DEFAULT_START_MONTH, 
            debt=debt, 
            interest_pct=interest, 
            monthly_payment=monthly_payment, 
            yearly_add_on=yearly_add_on
        )

    # Render results
    total_interest, total_principal = render_summary_metrics(df, debt)
    render_visualizations(df, mode="simple")

elif calculator_mode == "Manual Payment Input (Variable Interest Rates)":
    # Variable Rates Calculator Mode

    # Interest Rate & Payment Configuration
    st.markdown("### 📈💳 Interest Rate & Payment Configuration")

    # Initialize session state for additional years
    if 'additional_years' not in st.session_state:
        st.session_state.additional_years = 0

    # Store rates and payments in dictionaries
    interest_rates = {}
    monthly_payments = {}

    # Base configuration for first 3 years - compact side-by-side layout
    for year in range(1, 4):
        col_rate, col_payment = st.columns([1, 1])
        with col_rate:
            rate = st.number_input(f"Year {year} Rate (%)", value=DEFAULT_INTEREST_RATE, step=0.001, format="%.3f", key=f"rate_{year}")
            interest_rates[year] = rate / 100
        with col_payment:
            payment = st.number_input(f"Year {year} Payment (฿)", value=DEFAULT_MONTHLY_PAYMENT, step=1000, format="%d", key=f"payment_{year}")
            monthly_payments[year] = payment

    # Additional years section
    if st.session_state.additional_years > 0:
        for i in range(st.session_state.additional_years):
            year_num = 4 + i
            col_rate, col_payment = st.columns([1, 1])
            with col_rate:
                rate = st.number_input(f"Year {year_num} Rate (%)", value=DEFAULT_INTEREST_RATE, step=0.001, format="%.3f", key=f"rate_{year_num}")
                interest_rates[year_num] = rate / 100
            with col_payment:
                payment = st.number_input(f"Year {year_num} Payment (฿)", value=DEFAULT_MONTHLY_PAYMENT, step=1000, format="%d", key=f"payment_{year_num}")
                monthly_payments[year_num] = payment

    # "From X year onwards" section
    max_defined_year = 3 + st.session_state.additional_years
    from_year_onwards = max_defined_year + 1
    col_rate_onwards, col_payment_onwards = st.columns([1, 1])
    with col_rate_onwards:
        from_year_rate = st.number_input(f"From Year {from_year_onwards}+ Rate (%)", value=DEFAULT_INTEREST_RATE, step=0.001, format="%.3f", key="rate_onwards")
        interest_rates['onwards'] = from_year_rate / 100
    with col_payment_onwards:
        from_year_payment = st.number_input(f"From Year {from_year_onwards}+ Payment (฿)", value=DEFAULT_MONTHLY_PAYMENT, step=1000, format="%d", key="payment_onwards")
        monthly_payments['onwards'] = from_year_payment

    # Buttons for adding/removing years
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Add Another Year"):
            st.session_state.additional_years += 1
            st.rerun()
    with col2:
        if st.session_state.additional_years > 0 and st.button("➖ Remove Last Year"):
            st.session_state.additional_years -= 1
            st.rerun()

    # Additional Payment Options
    st.markdown("### 📈 Additional Payment Options")
    yearly_add_on = st.number_input("📈 Yearly Add-on (฿)", value=DEFAULT_YEARLY_ADD_ON, step=10_000, format="%d")

    debt = house_price - down

    st.markdown("---")

    # Calculate loan schedule with variable rates and payments
    with st.spinner('Calculating loan schedule with variable interest rates and payments...'):
        df = calculate_loan_schedule_variable_rates(
            start_year=DEFAULT_START_YEAR, 
            start_month=DEFAULT_START_MONTH, 
            debt=debt, 
            interest_rates_dict=interest_rates, 
            monthly_payments_dict=monthly_payments, 
            yearly_add_on=yearly_add_on
        )

    # Render results
    total_interest, total_principal = render_summary_metrics(df, debt)
    render_visualizations(df, mode="variable")

elif calculator_mode == "Standard Mortgage Calculator":
    # Standard Mortgage Calculator Mode
    
    # Loan Term and Interest Configuration
    st.markdown("### 📈 Loan Configuration")
    col1, col2 = st.columns(2)
    with col1:
        loan_years = st.number_input("📅 Loan Term (Years)", value=40, min_value=1, max_value=50, step=1)
    with col2:
        # Choose between fixed or variable rate
        rate_type = st.radio("Interest Rate Type:", ["Variable Rates (6 periods)", "Fixed Rate"])
    
    if rate_type == "Fixed Rate":
        # Fixed rate standard mortgage
        interest = st.number_input("📈 Interest Rate (%)", value=DEFAULT_INTEREST_RATE, step=0.1, format="%.1f")
        interest = interest / 100
        
        # Calculate debt first
        debt = house_price - down
        
        # Calculate and display the monthly payment
        calculated_payment = calculate_monthly_payment(debt, interest, loan_years)
        st.info(f"💳 **Calculated Monthly Payment: ฿{calculated_payment:,.2f}**")
        
        # Top up payment strategies
        st.markdown("### 💰 Top Up Payment")
        top_up_strategy = st.selectbox(
            "Top Up Strategy",
            options=["None", "Fixed Amount", "Additional Amount", "Percentage Increase"],
            help="Choose how to add extra payments to principal"
        )
        
        top_up_params = {}
        if top_up_strategy == "Fixed Amount":
            top_up_amount = st.number_input("💰 Top up to at least (฿)", value=20000, step=1000, format="%d", 
                                          help="If calculated payment is less than this amount, the difference goes to principal")
            top_up_params = {"strategy": "fixed", "amount": top_up_amount}
        elif top_up_strategy == "Additional Amount":
            additional_amount = st.number_input("💰 Additional amount (฿)", value=5000, step=1000, format="%d",
                                              help="Add this amount to the required payment each month")
            top_up_params = {"strategy": "additional", "amount": additional_amount}
        elif top_up_strategy == "Percentage Increase":
            percentage = st.number_input("💰 Percentage increase (%)", value=10.0, step=1.0, format="%.1f",
                                       help="Increase the required payment by this percentage")
            top_up_params = {"strategy": "percentage", "amount": percentage}
        else:
            top_up_params = {"strategy": "none", "amount": 0}
        
        yearly_add_on = 0  # No additional payments for standard mortgage

        st.markdown("---")

        # Calculate loan schedule
        with st.spinner('Calculating standard mortgage schedule...'):
            df, monthly_payment = calculate_standard_mortgage_schedule(
                start_year=DEFAULT_START_YEAR, 
                start_month=DEFAULT_START_MONTH, 
                debt=debt, 
                annual_rate=interest, 
                years=loan_years,
                yearly_add_on=yearly_add_on,
                top_up_params=top_up_params
            )

        # Render results
        total_interest, total_principal = render_summary_metrics(df, debt)
        render_visualizations(df, mode="standard")
        
    else:
        # Variable rates standard mortgage
        st.markdown("### 📈 Variable Interest Rates (Years 1,2,3,4,5,6+)")
        
        # Collect 6 interest rates
        col1, col2, col3 = st.columns(3)
        with col1:
            rate1 = st.number_input("Year 1 Rate (%)", value=2.3, step=0.001, format="%.3f", key="std_rate_1")
            rate2 = st.number_input("Year 2 Rate (%)", value=2.9, step=0.001, format="%.3f", key="std_rate_2")
        with col2:
            rate3 = st.number_input("Year 3 Rate (%)", value=3.5, step=0.001, format="%.3f", key="std_rate_3")
            rate4 = st.number_input("Year 4 Rate (%)", value=4.495, step=0.001, format="%.3f", key="std_rate_4")
        with col3:
            rate5 = st.number_input("Year 5 Rate (%)", value=4.495, step=0.001, format="%.3f", key="std_rate_5")
            rate6 = st.number_input("Year 6+ Rate (%)", value=5.495, step=0.001, format="%.3f", key="std_rate_6")
        
        rates = [rate1/100, rate2/100, rate3/100, rate4/100, rate5/100, rate6/100]
        
        # Calculate and display the initial monthly payment
        debt = house_price - down
        initial_payment = calculate_monthly_payment(debt, rates[0], loan_years)
        st.info(f"💳 **Initial Monthly Payment (Year 1): ฿{initial_payment:,.2f}** (Payment will be recalculated each year)")
        
        # Top up payment strategies
        st.markdown("### 💰 Top Up Payment")
        top_up_strategy = st.selectbox(
            "Top Up Strategy",
            options=["None", "Fixed Amount", "Additional Amount", "Percentage Increase"],
            help="Choose how to add extra payments to principal",
            key="var_strategy"
        )
        
        top_up_params = {}
        if top_up_strategy == "Fixed Amount":
            top_up_amount = st.number_input("💰 Top up to at least (฿)", value=20000, step=1000, format="%d", 
                                          help="If calculated payment is less than this amount, the difference goes to principal", key="var_fixed")
            top_up_params = {"strategy": "fixed", "amount": top_up_amount}
        elif top_up_strategy == "Additional Amount":
            additional_amount = st.number_input("💰 Additional amount (฿)", value=5000, step=1000, format="%d",
                                              help="Add this amount to the required payment each month", key="var_additional")
            top_up_params = {"strategy": "additional", "amount": additional_amount}
        elif top_up_strategy == "Percentage Increase":
            percentage = st.number_input("💰 Percentage increase (%)", value=10.0, step=1.0, format="%.1f",
                                       help="Increase the required payment by this percentage", key="var_percentage")
            top_up_params = {"strategy": "percentage", "amount": percentage}
        else:
            top_up_params = {"strategy": "none", "amount": 0}
        
        yearly_add_on = 0  # No additional payments for standard mortgage

        st.markdown("---")

        # Calculate loan schedule
        with st.spinner('Calculating variable rate mortgage schedule...'):
            df = calculate_variable_rate_mortgage_schedule(
                start_year=DEFAULT_START_YEAR, 
                start_month=DEFAULT_START_MONTH, 
                debt=debt, 
                interest_rates_list=rates, 
                years=loan_years,
                yearly_add_on=yearly_add_on,
                top_up_params=top_up_params
            )

        # Render results
        total_interest, total_principal = render_summary_metrics(df, debt)
        render_visualizations(df, mode="variable_standard") 