import streamlit as st

# Page configuration
st.set_page_config(
    page_title='House Loan Planning Calculator',
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
    .sidebar-info {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        border-left: 4px solid #667eea;
    }
</style>
""", unsafe_allow_html=True)

# Main header
st.markdown("""
<div class="main-header">
    <h1 style="color: white; text-align: center; margin: 0;">
        House Loan Planning Calculator
    </h1>
    <p style="color: white; text-align: center; margin: 0.5rem 0 0 0;">
        Plan your mortgage payments with detailed analysis and visualizations
    </p>
</div>
""", unsafe_allow_html=True)

# Welcome content
st.markdown("""
## Welcome to the House Loan Planning Calculator!

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