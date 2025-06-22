import pandas as pd
import calendar
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Default values
DEFAULT_HOUSE_PRICE = 4_300_000
DEFAULT_DOWN_PAYMENT = 300_000
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
    /* Remove custom metric styling to allow Streamlit's theme handling */
    /*
    .stMetric {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    */
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

# Input Section
st.markdown("## 📊 Loan Parameters")

# Create a nice input layout on the main page
st.markdown("### 🏡 Property Information")
col1, col2 = st.columns(2)
with col1:
    house_price = st.number_input("🏠 Full House Price (฿)", value=DEFAULT_HOUSE_PRICE, step=100_000, format="%d")
with col2:
    down = st.number_input("💰 Down Payment (฿)", value=DEFAULT_DOWN_PAYMENT, step=100_000, format="%d")

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

# Buttons for adding/removing years (shared between both configurations)
col1, col2 = st.columns(2)
with col1:
    if st.button("➕ Add Another Year"):
        st.session_state.additional_years += 1
        st.rerun()
with col2:
    if st.session_state.additional_years > 0 and st.button("➖ Remove Last Year"):
        st.session_state.additional_years -= 1
        st.rerun()



st.markdown("### 📈 Additional Payment Options")
yearly_add_on = st.number_input("📈 Yearly Add-on (฿)", value=DEFAULT_YEARLY_ADD_ON, step=10_000, format="%d")

# Use default values for refinancing options (hidden for now)
refinance_cycle_years = DEFAULT_REFINANCE_CYCLE_YEARS
raise_after_refinance = DEFAULT_RAISE_AFTER_REFINANCE

debt = house_price - down

st.markdown("---")

# Enhanced Loan Calculation with variable interest rates and payments
@st.cache_data
def calculate_loan_schedule_variable_rates(start_year, start_month, debt, interest_rates_dict, monthly_payments_dict, yearly_add_on):
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

# Calculate summary statistics
total_months = len(df) - 1
total_full_years = int(total_months / 12)
total_full_months = total_months - (total_full_years * 12)
total_interest = df['interest_payment'].sum()
total_principal = df['principal_payment'].sum()
total_paid = total_interest + total_principal

# Summary Metrics
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

# Payment Schedule
st.markdown("## 📊 Payment Schedule")

st.markdown("### Payment Schedule Details")

display_df = df.copy()
display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
display_df = display_df[['date', 'starting_principal_balance', 'applied_rate', 'applied_payment', 'principal_payment', 'interest_payment', 'total_payment', 'add_on', 'remaining_principal_balance']]
display_df.columns = ['Date', 'Starting Balance (฿)', 'Rate (%)', 'Monthly Payment (฿)', 'Principal (฿)', 'Interest (฿)', 'Total Payment (฿)', 'Add-on (฿)', 'Remaining Balance (฿)']

# Format numbers
for col in ['Starting Balance (฿)', 'Monthly Payment (฿)', 'Principal (฿)', 'Interest (฿)', 'Total Payment (฿)', 'Add-on (฿)', 'Remaining Balance (฿)']:
    display_df[col] = display_df[col].apply(lambda x: f"฿{x:,.0f}")

# Format rate
display_df['Rate (%)'] = display_df['Rate (%)'].apply(lambda x: f"{x:.3f}%")

st.dataframe(display_df, use_container_width=True, height=400)

