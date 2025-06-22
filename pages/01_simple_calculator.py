import streamlit as st
import sys
import os

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.constants import DEFAULT_INTEREST_RATE, DEFAULT_MONTHLY_PAYMENT, DEFAULT_YEARLY_ADD_ON, DEFAULT_START_YEAR, DEFAULT_START_MONTH
from utils.calculations import calculate_loan_schedule_simple
from utils.visualizations import render_summary_metrics, render_visualizations, render_property_info_form

st.set_page_config(
    page_title="Simple Calculator - House Loan Planning",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Page header
st.markdown("""
# 💰 Simple Loan Calculator

**Manual Payment Input with Fixed Interest Rate**

This calculator allows you to input your desired monthly payment amount and see how it affects your loan repayment schedule with a fixed interest rate.
""")

# Property Information
house_price, down, debt = render_property_info_form()

st.markdown("---")

# Interest Rate Configuration
st.markdown("### 📈 Interest Rate")
interest = st.number_input(
    "📈 Interest Rate (%)", 
    value=DEFAULT_INTEREST_RATE, 
    step=0.1, 
    format="%.1f",
    help="Annual interest rate for your loan"
)
interest = interest / 100

# Payment Structure
st.markdown("### 💳 Payment Structure")
col1, col2 = st.columns(2)
with col1:
    monthly_payment = st.number_input(
        "💵 Monthly Payment (฿)", 
        value=DEFAULT_MONTHLY_PAYMENT, 
        step=1000, 
        format="%d",
        help="Fixed amount you want to pay each month"
    )
with col2:
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
    with st.spinner('Calculating loan schedule...'):
        try:
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

        except Exception as e:
            st.error(f"Error in calculation: {str(e)}")
            st.error("This usually means your monthly payment is too low to cover the interest. Please increase your monthly payment.")
else:
    st.warning("Please enter a house price greater than your down payment to see calculations.")

# Sidebar information
with st.sidebar:
    st.markdown("""
    ### 💡 How This Calculator Works
    
    **Fixed Interest Rate**: Uses a single interest rate throughout the loan period.
    
    **Manual Payment**: You choose how much to pay each month.
    
    **Daily Interest Calculation**: Interest is calculated based on actual days in each month.
    
    **Year-end Bonus**: Optional additional payment at the end of each year.
    
    ---
    
    ### 📊 Key Features
    - Simple and straightforward
    - Fixed monthly payments
    - Flexible payment amounts
    - Yearly bonus payments
    
    ---
    
    ### ⚠️ Important Notes
    - Monthly payment must cover interest
    - Lower payments = longer loan term
    - Higher payments = shorter loan term
    - Interest calculated daily for accuracy
    """) 