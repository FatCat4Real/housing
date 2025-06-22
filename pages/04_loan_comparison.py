import streamlit as st
import sys
import os
import pandas as pd

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.constants import DEFAULT_INTEREST_RATE, DEFAULT_MONTHLY_PAYMENT, DEFAULT_START_YEAR, DEFAULT_START_MONTH
from utils.calculations import calculate_loan_schedule_simple, calculate_monthly_payment
from utils.visualizations import render_summary_metrics

# Page header
st.markdown("""
# Loan Comparison Tool

**Compare Different Loan Scenarios Side-by-Side**

This tool allows you to compare different loan scenarios to help you make informed decisions about your mortgage.
""")

# Initialize session state for scenarios
if 'scenarios' not in st.session_state:
    st.session_state.scenarios = []

# Scenario input section
st.markdown("### Add New Scenario")

with st.form("new_scenario"):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        scenario_name = st.text_input("Scenario Name", value=f"Scenario {len(st.session_state.scenarios) + 1}")
        house_price = st.number_input("House Price (฿)", value=4_300_000, step=100_000, format="%d")
        down_payment = st.number_input("Down Payment (฿)", value=0, step=100_000, format="%d")
    
    with col2:
        interest_rate = st.number_input("Interest Rate (%)", value=DEFAULT_INTEREST_RATE, step=0.1, format="%.1f")
        monthly_payment = st.number_input("Monthly Payment (฿)", value=DEFAULT_MONTHLY_PAYMENT, step=1000, format="%d")
    
    with col3:
        yearly_add_on = st.number_input("Yearly Add-on (฿)", value=50_000, step=10_000, format="%d")
        loan_years = st.number_input("Loan Term (Years)", value=30, min_value=1, max_value=50, step=1)
    
    calculation_type = st.radio(
        "Calculation Type:",
        ["Simple (Manual Payment)", "Standard Mortgage (Calculated Payment)"],
        help="Choose calculation method"
    )
    
    submit_scenario = st.form_submit_button("Add Scenario")
    
    if submit_scenario:
        debt = house_price - down_payment
        
        if debt > 0:
            try:
                scenario_data = {
                    'name': scenario_name,
                    'house_price': house_price,
                    'down_payment': down_payment,
                    'debt': debt,
                    'interest_rate': interest_rate / 100,
                    'monthly_payment': monthly_payment,
                    'yearly_add_on': yearly_add_on,
                    'loan_years': loan_years,
                    'calculation_type': calculation_type
                }
                
                # Calculate scenario
                if calculation_type == "Simple (Manual Payment)":
                    df = calculate_loan_schedule_simple(
                        start_year=DEFAULT_START_YEAR,
                        start_month=DEFAULT_START_MONTH,
                        debt=debt,
                        interest_pct=interest_rate / 100,
                        monthly_payment=monthly_payment,
                        yearly_add_on=yearly_add_on
                    )
                else:
                    # Calculate standard mortgage payment
                    calculated_payment = calculate_monthly_payment(debt, interest_rate / 100, loan_years)
                    df = calculate_loan_schedule_simple(
                        start_year=DEFAULT_START_YEAR,
                        start_month=DEFAULT_START_MONTH,
                        debt=debt,
                        interest_pct=interest_rate / 100,
                        monthly_payment=calculated_payment,
                        yearly_add_on=0  # Standard mortgage doesn't have yearly add-on
                    )
                    scenario_data['calculated_payment'] = calculated_payment
                
                # Calculate summary metrics
                total_months = len(df)
                total_years = total_months / 12
                total_interest = df['interest_payment'].sum()
                total_principal = df['principal_payment'].sum()
                total_paid = total_interest + total_principal
                effective_rate = (total_interest / debt) * 100
                
                scenario_data.update({
                    'total_months': total_months,
                    'total_years': total_years,
                    'total_interest': total_interest,
                    'total_principal': total_principal,
                    'total_paid': total_paid,
                    'effective_rate': effective_rate,
                    'dataframe': df
                })
                
                st.session_state.scenarios.append(scenario_data)
                st.success(f"Added scenario: {scenario_name}")
                st.rerun()
                
            except Exception as e:
                st.error(f"Error calculating scenario: {str(e)}")
        else:
            st.error("House price must be greater than down payment")

st.markdown("---")

# Display scenarios comparison
if st.session_state.scenarios:
    st.markdown("### Scenario Comparison")
    
    # Summary comparison table
    comparison_data = []
    for scenario in st.session_state.scenarios:
        row = {
            'Scenario': scenario['name'],
            'Loan Amount (฿)': f"฿{scenario['debt']:,.0f}",
            'Interest Rate (%)': f"{scenario['interest_rate']*100:.1f}%",
            'Duration': f"{int(scenario['total_years'])}y {int((scenario['total_years'] % 1) * 12)}m",
            'Total Interest (฿)': f"฿{scenario['total_interest']:,.0f}",
            'Total Paid (฿)': f"฿{scenario['total_paid']:,.0f}",
            'Effective Rate (%)': f"{scenario['effective_rate']:.1f}%"
        }
        
        if scenario['calculation_type'] == "Simple (Manual Payment)":
            row['Monthly Payment (฿)'] = f"฿{scenario['monthly_payment']:,.0f}"
        else:
            row['Monthly Payment (฿)'] = f"฿{scenario['calculated_payment']:,.0f}"
            
        comparison_data.append(row)
    
    comparison_df = pd.DataFrame(comparison_data)
    st.dataframe(comparison_df, use_container_width=True)
    
    # Detailed scenario cards
    st.markdown("### Detailed Scenario Information")
    
    # Create columns for scenarios
    num_scenarios = len(st.session_state.scenarios)
    if num_scenarios == 1:
        cols = [st.columns(1)[0]]
    elif num_scenarios == 2:
        cols = st.columns(2)
    else:
        cols = st.columns(min(3, num_scenarios))
    
    for i, scenario in enumerate(st.session_state.scenarios):
        with cols[i % len(cols)]:
            with st.container():
                st.markdown(f"#### {scenario['name']}")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Loan Amount", f"฿{scenario['debt']:,.0f}")
                    st.metric("Interest Rate", f"{scenario['interest_rate']*100:.1f}%")
                    if scenario['calculation_type'] == "Simple (Manual Payment)":
                        st.metric("Monthly Payment", f"฿{scenario['monthly_payment']:,.0f}")
                    else:
                        st.metric("Calculated Payment", f"฿{scenario['calculated_payment']:,.0f}")
                
                with col2:
                    st.metric("Duration", f"{int(scenario['total_years'])}y {int((scenario['total_years'] % 1) * 12)}m")
                    st.metric("Total Interest", f"฿{scenario['total_interest']:,.0f}")
                    st.metric("Effective Rate", f"{scenario['effective_rate']:.1f}%")
                
                # Remove scenario button
                if st.button(f"Remove", key=f"remove_{i}"):
                    st.session_state.scenarios.pop(i)
                    st.rerun()
                
                st.markdown("---")
    
    # Clear all scenarios button
    if st.button("Clear All Scenarios"):
        st.session_state.scenarios = []
        st.rerun()

else:
    st.info("Add your first scenario above to start comparing different loan options!")

# Sidebar information
with st.sidebar:
    st.markdown("""
    ### 💡 How to Use This Tool
    
    1. **Add Scenarios**: Fill in the form above and click "Add Scenario"
    2. **Compare Results**: View the comparison table and detailed cards
    3. **Analyze Differences**: Look at total interest, duration, and effective rates
    4. **Make Decisions**: Choose the scenario that best fits your needs
    
    ---
    
    ### 📊 Key Metrics to Compare
    
    **Total Interest**: Lower is better  
    **Duration**: Shorter saves money  
    **Effective Rate**: Real cost of borrowing  
    **Monthly Payment**: Must fit your budget  
    
    ---
    
    ### 💡 Comparison Tips
    
    - Compare same loan amounts for fair analysis
    - Consider your cash flow capacity
    - Factor in opportunity costs
    - Think about rate change risks
    
    ### 🔍 What to Look For
    
    - **Best Total Cost**: Lowest total interest
    - **Best Cash Flow**: Manageable payments
    - **Best Balance**: Good cost vs. flexibility
    """)
    
    if st.session_state.scenarios:
        st.markdown("---")
        st.markdown(f"### 📈 Current Scenarios: {len(st.session_state.scenarios)}")
        
        for i, scenario in enumerate(st.session_state.scenarios):
            st.write(f"**{i+1}. {scenario['name']}**")
            st.write(f"   💰 ฿{scenario['total_interest']:,.0f} interest")
            st.write(f"   ⏱️ {scenario['total_years']:.1f} years") 