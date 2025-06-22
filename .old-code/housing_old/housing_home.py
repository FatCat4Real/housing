import streamlit as st

# Welcome content
st.title("House Loan Planning Calculator")
st.markdown("""
This comprehensive tool helps you analyze different mortgage scenarios and plan your loan payments effectively.

### Available Calculators:

- **Home**: Overview and navigation (this page)
- **Simple Calculator**: Manual payment input with fixed interest rate
- **Variable Rate Calculator**: Manual payment input with different rates by year
- **Standard Mortgage**: Traditional mortgage calculator with payment formulas

### Getting Started:

1. **Choose a calculator** from the sidebar or pages menu
2. **Enter your property details** (house price, down payment)
3. **Configure loan parameters** (interest rates, payment amounts)
4. **Review the results** with detailed payment schedules and summaries

### Features:

- **Multiple calculation methods** to suit different scenarios
- **Variable interest rates** for more realistic planning
- **Top-up payment strategies** to reduce loan duration
- **Detailed payment schedules** with monthly breakdowns
- **Summary metrics** including total interest and effective rates
- **Export-ready data** for further analysis

---

**Navigate using the sidebar to get started with your loan calculations!**
""")

# Sidebar information
with st.sidebar:
    st.markdown("""
    ### Quick Guide

    **Simple Calculator**
    - Fixed interest rate
    - Manual payment amounts
    - Basic loan analysis

    **Variable Rate Calculator**
    - Different rates by year
    - Manual payment amounts
    - Advanced scenario planning

    **Standard Mortgage**
    - Calculated payments
    - Fixed or variable rates
    - Traditional mortgage formulas

    ---

    ### Tips
    - Start with property information
    - Consider top-up payments to save interest
    - Compare different scenarios
    - Export data for record keeping
    """)

    st.markdown("---")
    st.markdown("*Use the Pages menu above to navigate between calculators*") 