import streamlit as st
import sys
import os

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.constants import DEFAULT_INTEREST_RATE, DEFAULT_VARIABLE_RATES, DEFAULT_START_YEAR, DEFAULT_START_MONTH
from utils.calculations import (
    calculate_standard_mortgage_schedule, 
    calculate_variable_rate_mortgage_schedule,
    calculate_monthly_payment
)
from utils.visualizations import render_summary_metrics, render_visualizations, render_property_info_form, render_top_up_section

# Page header
st.markdown("""
# Standard Mortgage Calculator

**Traditional Mortgage Calculator with Payment Formulas**

This calculator uses standard mortgage formulas to compute your monthly payments based on loan amount, interest rate, and loan term.
""")

# Property Information
house_price, down, debt = render_property_info_form()

st.markdown("---")

# Loan Term and Interest Configuration
st.markdown("### Loan Configuration")
col1, col2 = st.columns(2)
with col1:
    loan_years = st.number_input(
        "Loan Term (Years)", 
        value=40, 
        min_value=1, 
        max_value=50, 
        step=1,
        help="Total number of years to repay the loan"
    )
with col2:
    # Choose between fixed or variable rate
    rate_type = st.radio(
        "Interest Rate Type:", 
        ["Fixed Rate", "Variable Rates (6 periods)"],
        help="Choose between a single fixed rate or variable rates for different periods"
    )

if rate_type == "Fixed Rate":
    # Fixed rate standard mortgage
    st.markdown("### Interest Rate")
    interest = st.number_input(
        "Interest Rate (%)", 
        value=DEFAULT_INTEREST_RATE, 
        step=0.1, 
        format="%.1f",
        help="Annual interest rate for the entire loan term"
    )
    interest = interest / 100
    
    # Calculate and display the monthly payment
    if debt > 0:
        calculated_payment = calculate_monthly_payment(debt, interest, loan_years)
        st.info(f"**Calculated Monthly Payment: ฿{calculated_payment:,.2f}**")
    
    # Top up payment strategies
    top_up_params = render_top_up_section(key_prefix="fixed")
    
    yearly_add_on = 0  # No additional payments for standard mortgage

    st.markdown("---")

    # Calculate and display results
    if debt > 0:
        with st.spinner('Calculating standard mortgage schedule...'):
            try:
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

            except Exception as e:
                st.error(f"Error in calculation: {str(e)}")
                st.error("Please check your input parameters.")
    else:
        st.warning("Please enter a house price greater than your down payment to see calculations.")
        
else:
    # Variable rates standard mortgage
    st.markdown("### Variable Interest Rates (Years 1,2,3,4,5,6+)")
    
    # Collect 6 interest rates
    col1, col2, col3 = st.columns(3)
    with col1:
        rate1 = st.number_input("Year 1 Rate (%)", value=DEFAULT_VARIABLE_RATES[0], step=0.001, format="%.3f", key="std_rate_1")
        rate2 = st.number_input("Year 2 Rate (%)", value=DEFAULT_VARIABLE_RATES[1], step=0.001, format="%.3f", key="std_rate_2")
    with col2:
        rate3 = st.number_input("Year 3 Rate (%)", value=DEFAULT_VARIABLE_RATES[2], step=0.001, format="%.3f", key="std_rate_3")
        rate4 = st.number_input("Year 4 Rate (%)", value=DEFAULT_VARIABLE_RATES[3], step=0.001, format="%.3f", key="std_rate_4")
    with col3:
        rate5 = st.number_input("Year 5 Rate (%)", value=DEFAULT_VARIABLE_RATES[4], step=0.001, format="%.3f", key="std_rate_5")
        rate6 = st.number_input("Year 6+ Rate (%)", value=DEFAULT_VARIABLE_RATES[5], step=0.001, format="%.3f", key="std_rate_6")
    
    rates = [rate1/100, rate2/100, rate3/100, rate4/100, rate5/100, rate6/100]
    
    # Calculate and display the initial monthly payment
    if debt > 0:
        initial_payment = calculate_monthly_payment(debt, rates[0], loan_years)
        st.info(f"**Initial Monthly Payment (Year 1): ฿{initial_payment:,.2f}** (Payment will be recalculated each year)")
    
    # Top up payment strategies
    top_up_params = render_top_up_section(key_prefix="variable")
    
    yearly_add_on = 0  # No additional payments for standard mortgage

    st.markdown("---")

    # Calculate and display results
    if debt > 0:
        with st.spinner('Calculating variable rate mortgage schedule...'):
            try:
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

            except Exception as e:
                st.error(f"Error in calculation: {str(e)}")
                st.error("Please check your input parameters.")
    else:
        st.warning("Please enter a house price greater than your down payment to see calculations.")

# Sidebar information
with st.sidebar:
    st.markdown("""
    ### How This Calculator Works
    
    **Standard Formula**: Uses the traditional mortgage payment formula: 
    
    `M = P × [r(1+r)^n] / [(1+r)^n - 1]`
    
    Where:
    - M = Monthly payment
    - P = Principal loan amount
    - r = Monthly interest rate
    - n = Number of payments
    
    **Monthly Recalculation**: For variable rates, payments are recalculated each year.
    
    **Top-up Options**: Add extra payments to reduce loan term.
    
    ---
    
    ### Key Features
    - Accurate mortgage calculations
    - Fixed or variable rate options
    - Multiple top-up strategies
    - Traditional mortgage structure
    
    ---
    
    ### Important Notes
    - Payments calculated automatically
    - Fixed payment schedule (except variable rates)
    - Standard banking formulas
    - Predictable payment amounts
    
    ### Top-up Strategies
    
    **Fixed Amount**: Ensure minimum payment  
    **Additional Amount**: Add extra each month  
    **Percentage**: Increase payment by %  
    
    All strategies help reduce total interest paid.
    """)

# Show rate summary for variable rates
if rate_type == "Variable Rates (6 periods)":
    with st.expander("📋 Rate Configuration Summary", expanded=False):
        st.markdown("### Variable Rate Configuration:")
        
        for i, rate in enumerate(rates[:-1], 1):
            st.write(f"**Year {i}**: {rate*100:.3f}%")
        st.write(f"**Year 6+**: {rates[-1]*100:.3f}%")
        
        st.markdown("---")
        st.markdown("*Payments will be recalculated each year based on remaining balance and term.*") 