# 🏠 House Loan Planning Calculator - Multipage Structure

This project has been reorganized into a multipage Streamlit application for better organization and user experience.

## 📁 Project Structure

```
housing/
├── app.py                           # Main entry point and home page
├── pages/                          # Individual calculator pages
│   ├── 1_Simple_Calculator.py      # Manual payment with fixed rate
│   ├── 2_Variable_Rate_Calculator.py # Manual payment with variable rates
│   ├── 3_Standard_Mortgage.py      # Traditional mortgage calculator
│   └── 4_Loan_Comparison.py        # Compare multiple scenarios
├── utils/                          # Shared utilities
│   ├── __init__.py
│   ├── constants.py                # Default values and constants
│   ├── calculations.py             # All loan calculation functions
│   └── visualizations.py           # Shared UI components
├── housing_combined.py             # Original single-page version (backup)
└── pyproject.toml                  # Project dependencies
```

## 🚀 Getting Started

### Running the Application

```bash
# Install dependencies
pip install -r requirements.txt
# or if using uv
uv sync

# Run the multipage app
streamlit run app.py

# Or run the original single-page version
streamlit run housing_combined.py
```

### Navigation

The application automatically creates a sidebar navigation menu with the following pages:

1. **Home** (`app.py`): Welcome page with overview and navigation
2. **Simple Calculator**: Fixed interest rate with manual payment input
3. **Variable Rate Calculator**: Different rates and payments by year
4. **Standard Mortgage**: Traditional mortgage with calculated payments
5. **Loan Comparison**: Side-by-side scenario comparison

## 📊 Calculator Types

### 1. Simple Calculator
- **Use Case**: Basic loan analysis with fixed parameters
- **Features**: 
  - Fixed interest rate throughout loan term
  - Manual monthly payment input
  - Optional yearly add-on payments
  - Daily interest calculation

### 2. Variable Rate Calculator
- **Use Case**: Complex scenarios with changing rates/payments
- **Features**:
  - Different interest rates for different years
  - Different payment amounts for different years
  - Dynamic year configuration (add/remove years)
  - Flexible "onwards" rate for remaining years

### 3. Standard Mortgage Calculator
- **Use Case**: Traditional mortgage calculations
- **Features**:
  - Calculated payments using mortgage formula
  - Fixed or variable rate options (6 periods)
  - Top-up payment strategies
  - Standard banking formulas

### 4. Loan Comparison Tool
- **Use Case**: Compare multiple loan scenarios
- **Features**:
  - Add multiple scenarios
  - Side-by-side comparison table
  - Detailed scenario cards
  - Key metrics analysis

## 🔧 Shared Components

### Constants (`utils/constants.py`)
- Default values for all calculators
- Centralized configuration

### Calculations (`utils/calculations.py`)
- `calculate_loan_schedule_simple()`: Basic loan calculation
- `calculate_loan_schedule_variable_rates()`: Variable rates calculation
- `calculate_standard_mortgage_schedule()`: Fixed rate mortgage
- `calculate_variable_rate_mortgage_schedule()`: Variable rate mortgage
- `calculate_monthly_payment()`: Standard mortgage payment formula
- `calculate_top_up_amount()`: Top-up payment calculations

### Visualizations (`utils/visualizations.py`)
- `render_summary_metrics()`: Summary statistics display
- `render_visualizations()`: Payment schedule tables
- `render_property_info_form()`: Property information input
- `render_top_up_section()`: Top-up payment configuration

## 🎨 Features

### ✅ User Interface
- **Responsive Design**: Works on desktop and mobile
- **Theme Support**: Automatic light/dark theme detection
- **Professional Styling**: Custom CSS for better appearance
- **Intuitive Navigation**: Clear page organization

### ✅ Calculations
- **Multiple Methods**: Simple, variable rate, and standard mortgage
- **Accurate Formulas**: Industry-standard calculations
- **Flexible Parameters**: Customizable rates, payments, and terms
- **Error Handling**: Graceful handling of invalid inputs

### ✅ Data Management
- **Session State**: Maintains data across page navigation
- **Caching**: Optimized performance with Streamlit caching
- **Export Ready**: Results can be copied for external analysis

## 🔄 Migration from Single Page

The original `housing_combined.py` file has been kept as a backup. All functionality has been preserved and reorganized into the new structure:

- **Property Information**: Shared component across all calculators
- **Calculation Logic**: Moved to dedicated functions in `utils/calculations.py`
- **Visualization**: Standardized components in `utils/visualizations.py`
- **Styling**: Consistent across all pages

## 🧩 Extensibility

The modular structure makes it easy to:

- **Add New Calculators**: Create new pages in the `pages/` directory
- **Modify Calculations**: Update functions in `utils/calculations.py`
- **Enhance UI**: Add components to `utils/visualizations.py`
- **Configure Defaults**: Adjust values in `utils/constants.py`

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**: Make sure you're running from the project root directory
2. **Page Not Loading**: Check that page files are in the `pages/` directory
3. **Calculation Errors**: Verify that monthly payments can cover interest
4. **Session State**: If data isn't persisting, check browser cache

### Development

```bash
# Run with auto-reload for development
streamlit run app.py --server.runOnSave true

# Debug mode
streamlit run app.py --logger.level debug
```

## 📝 Notes

- All calculations use the same logic as the original application
- Session state is used to maintain data across page navigation
- The comparison tool allows for advanced scenario analysis
- Each page is self-contained with its own configuration and results

## 🤝 Contributing

When adding new features:

1. Add calculation functions to `utils/calculations.py`
2. Add UI components to `utils/visualizations.py`
3. Create new pages in the `pages/` directory
4. Update constants in `utils/constants.py` if needed
5. Follow the existing naming conventions and structure 