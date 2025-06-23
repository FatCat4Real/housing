import streamlit as st
import pandas as pd
import calendar
import json

# Page configuration
st.set_page_config(
    page_title='House Loan Planning Calculator - Standard Mortgage',
    initial_sidebar_state='collapsed'
)

# Constants
DEFAULT_HOUSE_PRICE = 4_300_000
DEFAULT_INTEREST_RATE = 4.0
DEFAULT_START_YEAR = 2026
DEFAULT_START_MONTH = 1
DEFAULT_VARIABLE_RATES = [2.3, 2.9, 3.5, 4.495, 4.495, 5.495]

# Utility Functions
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
    """Calculate top-up amount based on minimum payment and additional amount"""
    if not top_up_params:
        return 0
    
    minimum_payment = top_up_params.get("minimum_payment", 0)
    additional_amount = top_up_params.get("additional_amount", 0)
    
    # Calculate effective payment: max(base_payment, minimum_payment) + additional_amount
    effective_payment = max(base_payment, minimum_payment) + additional_amount
    
    # Return the top-up amount (difference from base payment)
    return effective_payment - base_payment

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

def render_summary_metrics(df, debt, baseline_df=None):
    """Render the summary metrics section"""
    total_months = len(df)
    total_full_years = int(total_months / 12)
    total_full_months = total_months - (total_full_years * 12)
    total_interest = df['interest_payment'].sum()
    total_principal = df['principal_payment'].sum()
    total_paid = total_interest + total_principal

    st.markdown("### 📈 Loan Summary")

    # Calculate baseline metrics if provided
    baseline_months = None
    baseline_interest = None
    duration_delta = None
    interest_delta = None
    
    if baseline_df is not None:
        baseline_months = len(baseline_df)
        baseline_interest = baseline_df['interest_payment'].sum()
        
        # Calculate savings
        months_saved = baseline_months - total_months
        interest_saved = baseline_interest - total_interest
        
        # Format duration savings
        years_saved = int(months_saved / 12)
        months_saved_remainder = months_saved - (years_saved * 12)
        
        if years_saved > 0 and months_saved_remainder > 0:
            duration_delta = f"-{years_saved}y {months_saved_remainder}m"
        elif years_saved > 0:
            duration_delta = f"-{years_saved}y"
        elif months_saved_remainder > 0:
            duration_delta = f"-{months_saved_remainder}m"
        else:
            duration_delta = "0m"
            
        interest_delta = f"-฿{interest_saved:,.0f}" if interest_saved > 0 else f"฿{abs(interest_saved):,.0f}"

    # Calculate average payments for different periods
    # Add relative year column for easier filtering
    df_with_relative_year = df.copy()
    df_with_relative_year['relative_year'] = df_with_relative_year['year'] - DEFAULT_START_YEAR + 1
    
    # Average payment calculations
    avg_payment_total = df['total_payment'].mean()
    
    # Years 1-3
    years_1_3 = df_with_relative_year[df_with_relative_year['relative_year'].between(1, 3)]
    avg_payment_1_3 = years_1_3['total_payment'].mean() if len(years_1_3) > 0 else 0
    
    # Years 4-6
    years_4_6 = df_with_relative_year[df_with_relative_year['relative_year'].between(4, 6)]
    avg_payment_4_6 = years_4_6['total_payment'].mean() if len(years_4_6) > 0 else 0
    
    # Years 7+
    years_7_plus = df_with_relative_year[df_with_relative_year['relative_year'] >= 7]
    avg_payment_7_plus = years_7_plus['total_payment'].mean() if len(years_7_plus) > 0 else 0

    # Stack metrics in 2 rows of 2 for smaller, less crowded layout
    col1, col2, col3= st.columns((1, 1.2, 1.2))
    with col1:
        st.metric("⏱️ Total Duration", f"{total_full_years}y {total_full_months}m", delta=duration_delta, border=True, delta_color='inverse')
    with col2:
        st.metric("💰 Total Interest", f"฿{total_interest:,.0f}", delta=interest_delta, border=True, delta_color='inverse')
    with col3:
        st.metric("💸 Total Paid", f"฿{total_paid:,.0f}", border=True)
    
    # Average payment metrics
    # st.markdown("#### 📊 Average Monthly Payments")
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("📈 Full Lifecycle", f"฿{avg_payment_total:,.0f}", border=True)
    with col2:
        if avg_payment_1_3 > 0:
            st.metric("🚀 Years 1-3", f"฿{avg_payment_1_3:,.0f}", border=True)
        else:
            st.metric("🚀 Years 1-3", "N/A", border=True)
    
    col3, col4 = st.columns(2)
    with col3:
        if avg_payment_4_6 > 0:
            st.metric("⚡ Years 4-6", f"฿{avg_payment_4_6:,.0f}", border=True)
        else:
            st.metric("⚡ Years 4-6", "N/A", border=True)
    with col4:
        if avg_payment_7_plus > 0:
            st.metric("🎯 Years 7+", f"฿{avg_payment_7_plus:,.0f}", border=True)
        else:
            st.metric("🎯 Years 7+", "N/A", border=True)
    
    return total_interest, total_principal

def render_visualizations(df, mode="simple"):
    """Render the payment schedule"""
    st.markdown("### 📊 Payment Schedule")
    
    display_df = df.copy()
    display_df['date'] = display_df['date'].dt.strftime('%Y-%m')
    
    # Always use the same exact columns for consistency
    # Ensure all required columns exist with defaults if missing
    if 'applied_rate' not in display_df.columns:
        # For fixed rate mode, calculate the rate from interest payments
        if len(display_df) > 0:
            # Calculate implied rate from first row's interest payment and starting balance
            first_row = display_df.iloc[0]
            if first_row['starting_principal_balance'] > 0:
                monthly_rate = first_row['interest_payment'] / first_row['starting_principal_balance']
                annual_rate = monthly_rate * 12 * 100  # Convert to annual percentage
                display_df['applied_rate'] = annual_rate
            else:
                display_df['applied_rate'] = 0
        else:
            display_df['applied_rate'] = 0
    
    if 'calculated_payment' not in display_df.columns:
        display_df['calculated_payment'] = display_df['total_payment']
    if 'top_up' not in display_df.columns:
        display_df['top_up'] = 0
    if 'add_on' not in display_df.columns:
        display_df['add_on'] = 0
    
    # Use identical column structure for all modes (now including rate)
    display_df = display_df[['date', 'starting_principal_balance', 'applied_rate', 'calculated_payment', 'principal_payment', 'interest_payment', 'total_payment', 'top_up', 'remaining_principal_balance']]
    display_df.columns = ['Date', 'Starting Balance (฿)', 'Rate (%)', 'Payment (฿)', 'Principal (฿)', 'Interest (฿)', 'Total (฿)', 'Top-up (฿)', 'Remaining (฿)']
    
    # Format rate column
    # display_df['Rate (%)'] = display_df['Rate (%)'].apply(lambda x: f"{x:.3f}%")
    display_df['Rate (%)'] = display_df['Rate (%)'].apply(lambda x: f"{x:.3f}")
    
    # Format all monetary columns
    format_cols = ['Starting Balance (฿)', 'Payment (฿)', 'Principal (฿)', 'Interest (฿)', 'Total (฿)', 'Top-up (฿)', 'Remaining (฿)']
    for col in format_cols:
        # display_df[col] = display_df[col].apply(lambda x: f"฿{x:,.0f}")
        display_df[col] = display_df[col].apply(lambda x: f"{x:,.0f}")

    # Reorder columns
    display_df = display_df[['Date', 'Starting Balance (฿)', 'Rate (%)', 'Payment (฿)', 'Top-up (฿)', 'Total (฿)', 'Principal (฿)', 'Interest (฿)', 'Remaining (฿)']]

    display_df = display_df.drop(columns=['Starting Balance (฿)'])
    
    st.dataframe(display_df.set_index('Date'), use_container_width=True, height=400)

def render_top_up_section(key_prefix="", default_minimum=0, default_additional=0):
    """Render top-up payment section - shared component"""
    # st.markdown("### 💰 Top Up Payment")
    
    col1, col2 = st.columns(2)
    
    with col1:
        minimum_payment = st.number_input(
            "💰 Minimum Payment (฿)", 
            value=default_minimum, 
            step=1000, 
            format="%d", 
            help="Only used when higher than required payment. Payment = MAX(required_payment, minimum_payment)",
            key=f"{key_prefix}_minimum"
        )
    
    with col2:
        additional_amount = st.number_input(
            "💰 Additional Amount (฿)", 
            value=default_additional, 
            step=1000, 
            format="%d",
            help="Extra amount to add on top of the effective payment each month",
            key=f"{key_prefix}_additional"
        )
    
    top_up_params = {
        "minimum_payment": minimum_payment,
        "additional_amount": additional_amount
    }
    
    return top_up_params

# Main Application
st.markdown("## 🏠 Mortgage Calculator")

# Initialize default values - these will be updated by sidebar configurations
config_house_price = DEFAULT_HOUSE_PRICE
config_interest_rate = DEFAULT_INTEREST_RATE
config_variable_rates = DEFAULT_VARIABLE_RATES.copy()
config_loan_term = 40
config_interest_type = "Variable"
config_minimum_payment = 0
config_additional_amount = 0

# Sidebar configurations - MUST BE BEFORE main content to update config values
with st.sidebar:
    st.markdown("## ⚙️ Configuration Presets")
    
    # Initialize variables for configuration loading
    selected_house_config_name = "None"
    selected_strategy_config_name = "None"
    
    # Load house/interest configurations
    st.markdown("### 🏠 House & Interest Presets")
    try:
        with open('config_house_interests.json', 'r') as f:
            house_configs_list = json.load(f)
        
        # Extract house config names for dropdown
        house_config_names = ["None"] + [config.get("CONFIG_NAME", f"House Config {i+1}") for i, config in enumerate(house_configs_list)]
        
        # House configuration selector
        selected_house_config = st.selectbox(
            "Choose house & interest preset:",
            options=house_config_names,
            help="Select a configuration from config_house_interests.json",
            key="house_config"
        )
        
        # Load selected house configuration
        if selected_house_config != "None":
            # Find the selected configuration
            selected_house_config_data = None
            for config in house_configs_list:
                if config.get("CONFIG_NAME") == selected_house_config:
                    selected_house_config_data = config
                    break
            
            if selected_house_config_data:
                selected_house_config_name = selected_house_config
                config_house_price = selected_house_config_data.get("DEFAULT_HOUSE_PRICE", DEFAULT_HOUSE_PRICE)
                config_interest_rate = selected_house_config_data.get("DEFAULT_INTEREST_RATE", DEFAULT_INTEREST_RATE)
                config_variable_rates = selected_house_config_data.get("DEFAULT_VARIABLE_RATES", DEFAULT_VARIABLE_RATES.copy())
                config_loan_term = selected_house_config_data.get("LOAN_TERM", 40)
                config_interest_type = selected_house_config_data.get("INTEREST_TYPE", "Variable")
                
                # Validate variable rates length
                if len(config_variable_rates) != 6:
                    st.warning("⚠️ Variable rates in config should have exactly 6 values. Using defaults.")
                    config_variable_rates = DEFAULT_VARIABLE_RATES.copy()

    except FileNotFoundError:
        st.warning("⚠️ config_house_interests.json not found.")
    except json.JSONDecodeError:
        st.error("❌ Invalid JSON in config_house_interests.json.")
    except Exception as e:
        st.error(f"❌ Error loading house configurations: {str(e)}")

    # Load strategy configurations
    st.markdown("### 💰 Payment Strategy Presets")
    try:
        with open('config_strategy.json', 'r') as f:
            strategy_configs_list = json.load(f)
        
        # Extract strategy config names for dropdown
        strategy_config_names = ["None"] + [config.get("CONFIG_NAME", f"Strategy Config {i+1}") for i, config in enumerate(strategy_configs_list)]
        
        # Strategy configuration selector
        selected_strategy_config = st.selectbox(
            "Choose payment strategy preset:",
            options=strategy_config_names,
            help="Select a configuration from config_strategy.json",
            key="strategy_config"
        )
        
        # Load selected strategy configuration
        if selected_strategy_config != "None":
            # Find the selected configuration
            selected_strategy_config_data = None
            for config in strategy_configs_list:
                if config.get("CONFIG_NAME") == selected_strategy_config:
                    selected_strategy_config_data = config
                    break
            
            if selected_strategy_config_data:
                selected_strategy_config_name = selected_strategy_config
                config_minimum_payment = selected_strategy_config_data.get("MINIMUM_PAYMENT", 0)
                config_additional_amount = selected_strategy_config_data.get("ADDITIONAL_AMOUNT", 0)

    except FileNotFoundError:
        st.warning("⚠️ config_strategy.json not found.")
    except json.JSONDecodeError:
        st.error("❌ Invalid JSON in config_strategy.json.")
    except Exception as e:
        st.error(f"❌ Error loading strategy configurations: {str(e)}")

    # Show loaded configurations in compact format
    if selected_house_config_name != "None" or selected_strategy_config_name != "None":
        st.markdown("### 📋 Active Configurations")
        if selected_house_config_name != "None":
            st.success(f"🏠 **House:** {selected_house_config_name}")
        
        if selected_strategy_config_name != "None":
            st.success(f"💰 **Strategy:** {selected_strategy_config_name}")
    
    st.markdown("---")
    
    # How it works section
    st.markdown("""
    ### ℹ️ How This Calculator Works
    
    **Standard Formula**: Uses the traditional mortgage payment formula: 
    
    `M = P × [r(1+r)^n] / [(1+r)^n - 1]`
    
    Where:
    - M = Monthly payment
    - P = Principal loan amount  
    - r = Monthly interest rate
    - n = Number of payments
    
    **Monthly Recalculation**: For variable rates, payments are recalculated each year.
    
    **Top-up Options**: Add extra payments to reduce loan term.
    """)

# st.write('')
# Property Information

# st.markdown("---")

col1, col2, col3 = st.columns(3)
with col1:
    house_price = st.number_input("Loan Amount (฿)", value=config_house_price, step=100_000, format="%d")

debt = house_price

# Loan Term and Interest Configuration
# st.markdown("### Loan Configuration")
with col2:
    loan_years = st.number_input(
        "Loan Term (Years)", 
        value=config_loan_term, 
        min_value=1, 
        max_value=50, 
        step=1,
        help="Total number of years to repay the loan"
    )
with col3:
    # Choose between fixed or variable rate
    rate_type_options = ["Variable", "Fixed"]
    default_index = rate_type_options.index(config_interest_type) if config_interest_type in rate_type_options else 0
    rate_type = st.radio(
        "Interest Rate Type:", 
        options=rate_type_options,
        index=default_index,
        help="Choose between a single fixed rate or variable rates for different periods",
        horizontal=True
    )

if rate_type == "Fixed":
    # Fixed rate standard mortgage
    # st.markdown("### Interest Rate")
    interest = st.number_input(
        "Interest Rate (%)", 
        value=config_interest_rate, 
        step=0.1, 
        format="%.1f",
        help="Annual interest rate for the entire loan term"
    )
    interest = interest / 100
    
    # Calculate and display the monthly payment
    if debt > 0:
        calculated_payment = calculate_monthly_payment(debt, interest, loan_years)
        # st.info(f"**Calculated Monthly Payment: ฿{calculated_payment:,.2f}**")
    
    # Top up payment strategies
    top_up_params = render_top_up_section(key_prefix="topup", default_minimum=config_minimum_payment, default_additional=config_additional_amount)
    
    yearly_add_on = 0  # No additional payments for standard mortgage

    # st.markdown("---")

    # Calculate and display results
    if debt > 0:
        with st.spinner('Calculating standard mortgage schedule...'):
            try:
                # Calculate baseline (no top-up payments)
                baseline_params = {"minimum_payment": 0, "additional_amount": 0}
                baseline_df, baseline_payment = calculate_standard_mortgage_schedule(
                    start_year=DEFAULT_START_YEAR, 
                    start_month=DEFAULT_START_MONTH, 
                    debt=debt, 
                    annual_rate=interest, 
                    years=loan_years,
                    yearly_add_on=yearly_add_on,
                    top_up_params=baseline_params
                )
                
                # Calculate current scenario (with top-up payments)
                df, monthly_payment = calculate_standard_mortgage_schedule(
                    start_year=DEFAULT_START_YEAR, 
                    start_month=DEFAULT_START_MONTH, 
                    debt=debt, 
                    annual_rate=interest, 
                    years=loan_years,
                    yearly_add_on=yearly_add_on,
                    top_up_params=top_up_params
                )

                # Render results with baseline comparison
                total_interest, total_principal = render_summary_metrics(df, debt, baseline_df)
                render_visualizations(df, mode="standard")

            except Exception as e:
                st.error(f"Error in calculation: {str(e)}")
                st.error("Please check your input parameters.")
    else:
        st.warning("Please enter a house price greater than your down payment to see calculations.")
        
else:
    # Variable rates standard mortgage
    # st.markdown("### Variable Interest Rates (Years 1,2,3,4,5,6+)")
    
    # Collect 6 interest rates
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        rate1 = st.number_input("Year 1 (%)", value=config_variable_rates[0], step=0.001, format="%.3f", key="std_rate_1")
    with col2:
        rate2 = st.number_input("Year 2 (%)", value=config_variable_rates[1], step=0.001, format="%.3f", key="std_rate_2")
    with col3:
        rate3 = st.number_input("Year 3 (%)", value=config_variable_rates[2], step=0.001, format="%.3f", key="std_rate_3")
    with col4:
        rate4 = st.number_input("Year 4 (%)", value=config_variable_rates[3], step=0.001, format="%.3f", key="std_rate_4")
    with col5:
        rate5 = st.number_input("Year 5 (%)", value=config_variable_rates[4], step=0.001, format="%.3f", key="std_rate_5")
    with col6:
        rate6 = st.number_input("Year 6+ (%)", value=config_variable_rates[5], step=0.001, format="%.3f", key="std_rate_6")
    
    rates = [rate1/100, rate2/100, rate3/100, rate4/100, rate5/100, rate6/100]
    
    # Calculate and display the initial monthly payment
    if debt > 0:
        initial_payment = calculate_monthly_payment(debt, rates[0], loan_years)
        # st.info(f"**Initial Monthly Payment (Year 1): ฿{initial_payment:,.2f}** (Payment will be recalculated each year)")
    
    # Top up payment strategies
    top_up_params = render_top_up_section(key_prefix="topup", default_minimum=config_minimum_payment, default_additional=config_additional_amount)
    
    yearly_add_on = 0  # No additional payments for standard mortgage

    # st.markdown("---")

    # Calculate and display results
    if debt > 0:
        with st.spinner('Calculating variable rate mortgage schedule...'):
            try:
                # Calculate baseline (no top-up payments)
                baseline_params = {"minimum_payment": 0, "additional_amount": 0}
                baseline_df = calculate_variable_rate_mortgage_schedule(
                    start_year=DEFAULT_START_YEAR, 
                    start_month=DEFAULT_START_MONTH, 
                    debt=debt, 
                    interest_rates_list=rates, 
                    years=loan_years,
                    yearly_add_on=yearly_add_on,
                    top_up_params=baseline_params
                )
                
                # Calculate current scenario (with top-up payments)
                df = calculate_variable_rate_mortgage_schedule(
                    start_year=DEFAULT_START_YEAR, 
                    start_month=DEFAULT_START_MONTH, 
                    debt=debt, 
                    interest_rates_list=rates, 
                    years=loan_years,
                    yearly_add_on=yearly_add_on,
                    top_up_params=top_up_params
                )

                # Render results with baseline comparison
                total_interest, total_principal = render_summary_metrics(df, debt, baseline_df)
                render_visualizations(df, mode="variable_standard")

            except Exception as e:
                st.error(f"Error in calculation: {str(e)}")
                st.error("Please check your input parameters.")
    else:
        st.warning("Please enter a house price greater than your down payment to see calculations.")

