import streamlit as st
import pandas as pd

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

def render_property_info_form():
    """Render property information form - shared component"""
    st.markdown("### 🏡 Property Information")
    
    # Get constants to avoid circular import
    from .constants import DEFAULT_HOUSE_PRICE, DEFAULT_DOWN_PAYMENT
    
    col1, col2 = st.columns(2)
    with col1:
        house_price = st.number_input("🏠 Full House Price (฿)", value=DEFAULT_HOUSE_PRICE, step=100_000, format="%d")
    with col2:
        down = st.number_input("💰 Down Payment (฿)", value=DEFAULT_DOWN_PAYMENT, step=100_000, format="%d")
    
    debt = house_price - down
    
    # Display loan amount
    st.info(f"💳 **Loan Amount: ฿{debt:,.0f}**")
    
    return house_price, down, debt

def render_top_up_section(key_prefix=""):
    """Render top-up payment section - shared component"""
    st.markdown("### 💰 Top Up Payment")
    top_up_strategy = st.selectbox(
        "Top Up Strategy",
        options=["None", "Fixed Amount", "Additional Amount", "Percentage Increase"],
        help="Choose how to add extra payments to principal",
        key=f"{key_prefix}_strategy"
    )
    
    top_up_params = {}
    if top_up_strategy == "Fixed Amount":
        top_up_amount = st.number_input(
            "💰 Top up to at least (฿)", 
            value=20000, 
            step=1000, 
            format="%d", 
            help="If calculated payment is less than this amount, the difference goes to principal",
            key=f"{key_prefix}_fixed"
        )
        top_up_params = {"strategy": "fixed", "amount": top_up_amount}
    elif top_up_strategy == "Additional Amount":
        additional_amount = st.number_input(
            "💰 Additional amount (฿)", 
            value=5000, 
            step=1000, 
            format="%d",
            help="Add this amount to the required payment each month",
            key=f"{key_prefix}_additional"
        )
        top_up_params = {"strategy": "additional", "amount": additional_amount}
    elif top_up_strategy == "Percentage Increase":
        percentage = st.number_input(
            "💰 Percentage increase (%)", 
            value=10.0, 
            step=1.0, 
            format="%.1f",
            help="Increase the required payment by this percentage",
            key=f"{key_prefix}_percentage"
        )
        top_up_params = {"strategy": "percentage", "amount": percentage}
    else:
        top_up_params = {"strategy": "none", "amount": 0}
    
    return top_up_params 