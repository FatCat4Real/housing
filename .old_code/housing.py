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
col1, col2, col3 = st.columns(3)
with col1:
    house_price = st.number_input("🏠 Full House Price (฿)", value=DEFAULT_HOUSE_PRICE, step=100_000, format="%d")
with col2:
    down = st.number_input("💰 Down Payment (฿)", value=DEFAULT_DOWN_PAYMENT, step=100_000, format="%d")
with col3:
    interest = st.number_input("📈 Interest Rate (%)", value=DEFAULT_INTEREST_RATE, step=0.1, format="%.1f")
    interest = interest / 100

st.markdown("### 💳 Payment Structure")
col1, col2 = st.columns(2)
with col1:
    monthly_payment = st.number_input("💵 Monthly Payment (฿)", value=DEFAULT_MONTHLY_PAYMENT, step=1000, format="%d")
with col2:
    yearly_add_on = st.number_input("📈 Yearly Add-on (฿)", value=DEFAULT_YEARLY_ADD_ON, step=10_000, format="%d")

# st.markdown("### 🔄 Refinancing Options")
# col1, col2 = st.columns(2)
# with col1:
#     refinance_cycle_years = st.number_input("⏰ Refinance Every ... Years", value=DEFAULT_REFINANCE_CYCLE_YEARS, step=1, format="%d")
# with col2:
#     raise_after_refinance = st.number_input("💪 Payment Increase After Refinance (฿)", value=DEFAULT_RAISE_AFTER_REFINANCE, step=500, format="%d")

# Use default values for refinancing options (hidden for now)
refinance_cycle_years = DEFAULT_REFINANCE_CYCLE_YEARS
raise_after_refinance = DEFAULT_RAISE_AFTER_REFINANCE

debt = house_price - down

# # Display key metrics at the top (removed - redundant with input parameters)
# col1, col2, col3, col4 = st.columns(4)
# with col1:
#     st.metric("🏠 House Price", f"฿{house_price:,.0f}")
# with col2:
#     st.metric("💰 Down Payment", f"฿{down:,.0f}")
# with col3:
#     st.metric("💸 Loan Amount", f"฿{debt:,.0f}")
# with col4:
#     st.metric("📊 Loan-to-Value", f"{(debt/house_price)*100:.1f}%")

st.markdown("---")

# Loan Calculation
@st.cache_data
def calculate_loan_schedule(start_year, start_month, debt, interest_pct, monthly_payment, yearly_add_on):
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
            # If payment doesn't cover interest, we can only pay what we have towards interest
            principal_payment = 0
            # In this case, the loan balance will actually increase due to unpaid interest
            # This is a realistic scenario for insufficient payments
        else:
            # Normal case: payment covers interest plus some principal
            principal_payment = min(left_principal_balance, principal_available)

        # Remaining principal
        left_principal_balance -= principal_payment #+ interest_payment
        
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

# Calculate loan schedule
with st.spinner('Calculating loan schedule...'):
    # df = calculate_loan_schedule(debt, interest, monthly_payment, yearly_add_on, refinance_cycle_years, raise_after_refinance)
    df = calculate_loan_schedule(
        start_year=DEFAULT_START_YEAR, 
        start_month=DEFAULT_START_MONTH, 
        debt=debt, 
        interest_pct=interest, 
        monthly_payment=monthly_payment, 
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

# Visualizations
st.markdown("## 📊 Loan Analysis Visualizations")

# Tab layout for different visualizations
tab1, tab2, tab3, tab4 = st.tabs(["🏠 Balance Over Time", "💰 Payment Breakdown", "📈 Cumulative Analysis", "📋 Payment Schedule"])

with tab1:
    st.markdown("### Remaining Balance Over Time")
    fig_balance = px.line(df[1:], x='date', y='remaining_principal_balance', 
                         title="Remaining Loan Balance Over Time",
                         labels={'remaining_principal_balance': 'Remaining Balance (฿)', 'date': 'Date'})
    fig_balance.update_layout(height=500)
    fig_balance.update_traces(line_color='#667eea', line_width=3)
    st.plotly_chart(fig_balance, use_container_width=True)

with tab2:
    st.markdown("### Monthly Payment Breakdown")
    # Create stacked bar chart for principal vs interest
    df_payments = df[1:].copy()  # Skip first row which has 0 payments
    df_payments = df_payments[::12]  # Show yearly data to avoid overcrowding
    
    fig_breakdown = go.Figure()
    fig_breakdown.add_trace(go.Bar(
        name='Principal Payment',
        x=df_payments['date'],
        y=df_payments['principal_payment'],
        marker_color='#667eea'
    ))
    fig_breakdown.add_trace(go.Bar(
        name='Interest Payment',
        x=df_payments['date'],
        y=df_payments['interest_payment'],
        marker_color='#764ba2'
    ))
    
    fig_breakdown.update_layout(
        title="Principal vs Interest Payment (Yearly View)",
        xaxis_title="Year",
        yaxis_title="Payment Amount (฿)",
        barmode='stack',
        height=500
    )
    st.plotly_chart(fig_breakdown, use_container_width=True)

with tab3:
    st.markdown("### Cumulative Payment Analysis")
    
    fig_cumulative = go.Figure()
    fig_cumulative.add_trace(go.Scatter(
        x=df[1:]['date'],
        y=df[1:]['cumulative_principal'],
        name='Cumulative Principal',
        fill='tonexty',
        marker_color='#667eea'
    ))
    fig_cumulative.add_trace(go.Scatter(
        x=df[1:]['date'],
        y=df[1:]['cumulative_total'],
        name='Cumulative Total',
        fill='tonexty',
        marker_color='#764ba2'
    ))
    
    fig_cumulative.update_layout(
        title="Cumulative Payments Over Time",
        xaxis_title="Date",
        yaxis_title="Cumulative Amount (฿)",
        height=500
    )
    st.plotly_chart(fig_cumulative, use_container_width=True)

with tab4:
    st.markdown("### Payment Schedule Details")
    
    # Show only the first 60 months for better readability
    # display_df = df[1:61].copy()
    display_df = df.copy()
    display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
    display_df = display_df[['date', 'starting_principal_balance', 'principal_payment', 'interest_payment', 'total_payment', 'add_on', 'remaining_principal_balance']]
    display_df.columns = ['Date', 'Starting Balance (฿)', 'Principal (฿)', 'Interest (฿)', 'Total Payment (฿)', 'Add-on (฿)', 'Remaining Balance (฿)']
    
    # Format numbers
    for col in ['Starting Balance (฿)', 'Principal (฿)', 'Interest (฿)', 'Total Payment (฿)', 'Add-on (฿)', 'Remaining Balance (฿)']:
        display_df[col] = display_df[col].apply(lambda x: f"฿{x:,.0f}")
    
    st.dataframe(display_df, use_container_width=True, height=400)

# Additional insights
st.markdown("## 💡 Key Insights")

col1, col2 = st.columns(2)
with col1:
    # Interest vs Principal pie chart
    fig_pie = px.pie(values=[total_interest, total_principal], 
                     names=['Total Interest', 'Total Principal'],
                     title="Interest vs Principal Distribution",
                     color_discrete_sequence=['#764ba2', '#667eea'])
    st.plotly_chart(fig_pie, use_container_width=True)

with col2:
    # Payment evolution over time
    payment_evolution = df[1::12]['total_payment'].values  # Yearly snapshots
    years_evolution = df[1::12]['year'].values
    
    fig_evolution = px.line(x=years_evolution, y=payment_evolution,
                           title="Total Payment Evolution",
                           labels={'x': 'Year', 'y': 'Total Payment (฿)'})
    fig_evolution.update_traces(line_color='#667eea', line_width=3)
    st.plotly_chart(fig_evolution, use_container_width=True)