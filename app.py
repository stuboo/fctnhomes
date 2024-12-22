import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Page configuration
st.set_page_config(
    page_title="Homebuilding Business Simulator",
    page_icon="🏠",
    layout="wide"
)

# Title
st.title("🏠 Homebuilding Business Simulator")

# Sidebar inputs
with st.sidebar:
    st.header("Input Parameters")
    
    initial_loan = st.number_input(
        "Initial Loan Amount ($)",
        min_value=0,
        max_value=1000000,
        value=320000,
        step=10000
    )
    
    construction_cost_sqft = st.number_input(
        "Construction Cost ($/sq ft)",
        min_value=0,
        max_value=500,
        value=175,
        step=5
    )
    
    selling_price_sqft = st.number_input(
        "Selling Price ($/sq ft)",
        min_value=0,
        max_value=1000,
        value=250,
        step=5
    )
    
    house_size = st.number_input(
        "House Size (sq ft)",
        min_value=0,
        max_value=10000,
        value=2000,
        step=100
    )
    
    construction_months = st.number_input(
        "Construction Timeline (months)",
        min_value=1,
        max_value=24,
        value=5,
        step=1
    )
    
    simulation_months = st.number_input(
        "Simulation Duration (months)",
        min_value=1,
        max_value=120,
        value=24,
        step=1
    )
    
    max_simultaneous_builds = st.number_input(
        "Maximum Simultaneous Builds",
        min_value=1,
        max_value=10,
        value=1,
        step=1,
        help="Maximum number of houses that can be under construction at the same time"
    )

def run_simulation(params):
    """
    Run the homebuilding business simulation with given parameters
    """
    # Initialize tracking variables
    cash_on_hand = params['initial_loan']
    loan_balance = params['initial_loan']
    construction_cost = params['house_size'] * params['construction_cost_sqft']
    selling_price = params['house_size'] * params['selling_price_sqft']
    profit_per_house = selling_price - construction_cost
    
    # Initialize results tracking
    results = []
    current_date = datetime.now()
    houses_completed = 0
    
    # Track multiple builds
    active_builds = []  # List of (start_date, construction_months) tuples
    
    for month in range(params['simulation_months']):
        current_month = current_date + timedelta(days=30*month)
        
        # Check existing builds for completion
        completed_builds = []
        for i, (start_date, _) in enumerate(active_builds):
            months_in_construction = (current_month - start_date).days // 30
            if months_in_construction >= params['construction_months']:
                # House is complete - realize profit
                cash_on_hand += selling_price
                houses_completed += 1
                completed_builds.append(i)
        
        # Remove completed builds (in reverse order to not affect indices)
        for i in sorted(completed_builds, reverse=True):
            active_builds.pop(i)
        
        # Start new construction if possible
        while len(active_builds) < params['max_simultaneous_builds']:
            if cash_on_hand < construction_cost:
                # Need to borrow
                needed_amount = construction_cost - cash_on_hand
                loan_balance += needed_amount
                cash_on_hand += needed_amount
            
            if cash_on_hand >= construction_cost:
                # Start new construction
                cash_on_hand -= construction_cost
                active_builds.append((current_month, params['construction_months']))
            else:
                break  # Can't afford more builds
        
        # Pay down loan if possible
        if loan_balance > 0 and cash_on_hand > 0:
            payment = min(cash_on_hand, loan_balance)
            loan_balance -= payment
            cash_on_hand -= payment
        
        # Record monthly state
        results.append({
            'Month': current_month.strftime('%Y-%m'),
            'Cash': cash_on_hand,
            'Loan Balance': loan_balance,
            'Under Construction': len(active_builds),
            'Houses Completed': houses_completed
        })
    
    return pd.DataFrame(results)

# Run simulation with current parameters
params = {
    'initial_loan': initial_loan,
    'construction_cost_sqft': construction_cost_sqft,
    'selling_price_sqft': selling_price_sqft,
    'house_size': house_size,
    'construction_months': construction_months,
    'simulation_months': simulation_months,
    'max_simultaneous_builds': max_simultaneous_builds
}

df = run_simulation(params)

# Display metrics
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Final Cash", f"${df['Cash'].iloc[-1]:,.2f}")
with col2:
    st.metric("Final Loan Balance", f"${df['Loan Balance'].iloc[-1]:,.2f}")
with col3:
    st.metric("Houses Completed", int(df['Houses Completed'].iloc[-1]))
with col4:
    profit_per_house = (selling_price_sqft - construction_cost_sqft) * house_size
    st.metric("Profit per House", f"${profit_per_house:,.2f}")

# Create visualizations
st.subheader("Financial Metrics Over Time")
tab1, tab2 = st.tabs(["📈 Charts", "📊 Data"])

with tab1:
    # Cash and Loan Balance
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=df['Month'], y=df['Cash'],
                             name='Cash on Hand', line=dict(color='green')))
    fig1.add_trace(go.Scatter(x=df['Month'], y=df['Loan Balance'],
                             name='Loan Balance', line=dict(color='red')))
    fig1.update_layout(title='Cash and Loan Balance Over Time',
                      xaxis_title='Month',
                      yaxis_title='Amount ($)')
    st.plotly_chart(fig1, use_container_width=True)
    
    # Construction and Completion
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=df['Month'], y=df['Under Construction'],
                             name='Under Construction', line=dict(color='orange')))
    fig2.add_trace(go.Scatter(x=df['Month'], y=df['Houses Completed'],
                             name='Houses Completed', line=dict(color='blue')))
    fig2.update_layout(title='Construction Progress Over Time',
                      xaxis_title='Month',
                      yaxis_title='Number of Houses')
    st.plotly_chart(fig2, use_container_width=True)

with tab2:
    st.dataframe(df)
    
    # Download button for the data
    csv = df.to_csv(index=False)
    st.download_button(
        label="Download simulation data as CSV",
        data=csv,
        file_name="homebuilding_simulation.csv",
        mime="text/csv"
    )
