import streamlit as st
import sys
import os

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.constants import DEFAULT_INTEREST_RATE, DEFAULT_MONTHLY_PAYMENT, DEFAULT_YEARLY_ADD_ON, DEFAULT_START_YEAR, DEFAULT_START_MONTH
from utils.calculations import calculate_loan_schedule_variable_rates
from utils.visualizations import render_summary_metrics, render_visualizations, render_property_info_form

st.set_page_config(
    page_title="Variable Rate Calculator - House Loan Planning",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Page header
st.markdown("""
# 📈 Variable Rate Loan Calculator

**Manual Payment Input with Variable Interest Rates**

This calculator allows you to set different interest rates and payment amounts for different years of your loan, giving you more realistic planning scenarios.
""")

# Property Information
house_price, down, debt = render_property_info_form()

st.markdown("---")

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
        rate = st.number_input(
            f"Year {year} Rate (%)", 
            value=DEFAULT_INTEREST_RATE, 
            step=0.001, 
            format="%.3f", 
            key=f"rate_{year}",
            help=f"Interest rate for year {year} of the loan"
        )
        interest_rates[year] = rate / 100
    with col_payment:
        payment = st.number_input(
            f"Year {year} Payment (฿)", 
            value=DEFAULT_MONTHLY_PAYMENT, 
            step=1000, 
            format="%d", 
            key=f"payment_{year}",
            help=f"Monthly payment amount for year {year}"
        )
        monthly_payments[year] = payment

# Additional years section
if st.session_state.additional_years > 0:
    for i in range(st.session_state.additional_years):
        year_num = 4 + i
        col_rate, col_payment = st.columns([1, 1])
        with col_rate:
            rate = st.number_input(
                f"Year {year_num} Rate (%)", 
                value=DEFAULT_INTEREST_RATE, 
                step=0.001, 
                format="%.3f", 
                key=f"rate_{year_num}",
                help=f"Interest rate for year {year_num} of the loan"
            )
            interest_rates[year_num] = rate / 100
        with col_payment:
            payment = st.number_input(
                f"Year {year_num} Payment (฿)", 
                value=DEFAULT_MONTHLY_PAYMENT, 
                step=1000, 
                format="%d", 
                key=f"payment_{year_num}",
                help=f"Monthly payment amount for year {year_num}"
            )
            monthly_payments[year_num] = payment

# "From X year onwards" section
max_defined_year = 3 + st.session_state.additional_years
from_year_onwards = max_defined_year + 1
col_rate_onwards, col_payment_onwards = st.columns([1, 1])
with col_rate_onwards:
    from_year_rate = st.number_input(
        f"From Year {from_year_onwards}+ Rate (%)", 
        value=DEFAULT_INTEREST_RATE, 
        step=0.001, 
        format="%.3f", 
        key="rate_onwards",
        help=f"Interest rate for year {from_year_onwards} and beyond"
    )
    interest_rates['onwards'] = from_year_rate / 100
with col_payment_onwards:
    from_year_payment = st.number_input(
        f"From Year {from_year_onwards}+ Payment (฿)", 
        value=DEFAULT_MONTHLY_PAYMENT, 
        step=1000, 
        format="%d", 
        key="payment_onwards",
        help=f"Monthly payment amount for year {from_year_onwards} and beyond"
    )
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
yearly_add_on = st.number_input(
    "📈 Yearly Add-on (฿)", 
    value=DEFAULT_YEARLY_ADD_ON, 
    step=10_000, 
    format="%d",
    help="Additional payment made at the end of each year"
)

st.markdown("---")

# Calculate and display results
if debt > 0:
    with st.spinner('Calculating loan schedule with variable interest rates and payments...'):
        try:
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

        except Exception as e:
            st.error(f"Error in calculation: {str(e)}")
            st.error("This usually means one of your monthly payments is too low to cover the interest for that period. Please increase the payment amounts.")
else:
    st.warning("Please enter a house price greater than your down payment to see calculations.")

# Sidebar information
with st.sidebar:
    st.markdown("""
    ### 💡 How This Calculator Works
    
    **Variable Interest Rates**: Different rates for different years of the loan.
    
    **Variable Payments**: Different payment amounts for different years.
    
    **Flexible Configuration**: Add as many years as needed with specific rates and payments.
    
    **Onwards Rate**: Final rate and payment for remaining years.
    
    ---
    
    ### 📊 Key Features
    - Year-specific interest rates
    - Year-specific payment amounts
    - Dynamic year configuration
    - Realistic scenario modeling
    
    ---
    
    ### ⚠️ Important Notes
    - Each payment must cover its year's interest
    - Rates and payments change annually
    - Use for complex loan structures
    - Plan for rate adjustments over time
    
    ### 💡 Use Cases
    - Promotional rates for first few years
    - Income changes over time
    - Step-up loan programs
    - Mixed rate scenarios
    """)

# Show configuration summary
with st.expander("📋 Configuration Summary", expanded=False):
    st.markdown("### Current Rate & Payment Configuration:")
    
    for year in range(1, max_defined_year + 1):
        if year in interest_rates and year in monthly_payments:
            st.write(f"**Year {year}**: {interest_rates[year]*100:.3f}% rate, ฿{monthly_payments[year]:,} payment")
    
    st.write(f"**Year {from_year_onwards}+**: {interest_rates['onwards']*100:.3f}% rate, ฿{monthly_payments['onwards']:,} payment")
    
    if yearly_add_on > 0:
        st.write(f"**Yearly Add-on**: ฿{yearly_add_on:,} at end of each year") 