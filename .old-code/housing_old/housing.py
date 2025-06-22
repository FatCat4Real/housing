import streamlit as st

# Page configuration
st.set_page_config(
    page_title='House Loan Planning Calculator',
    initial_sidebar_state='expanded'
)

# Define the pages using the new navigation system
pages = [
    st.Page(
        "housing_home.py",
        title="Home",
        icon=":material/home:"
    ),
    st.Page(
        "pages/01_simple_calculator.py",
        title="Simple Calculator",
        icon=":material/calculate:"
    ),
    st.Page(
        "pages/02_variable_rate_calculator.py",
        title="Variable Rate Calculator",
        icon=":material/trending_up:"
    ),
    st.Page(
        "pages/03_standard_mortgage.py",
        title="Standard Mortgage",
        icon=":material/account_balance:"
    ),
    st.Page(
        "pages/04_loan_comparison.py",
        title="Loan Comparison",
        icon=":material/compare:"
    ),
]

# Run the navigation
page = st.navigation(pages)
page.run() 