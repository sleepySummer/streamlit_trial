# mortgage_calculator.py
import streamlit as st
import pandas as pd
#import matplotlib.pyplot as plt
import math
from datetime import datetime

def show_calculator():
    st.title("mortage calculator")
    st.write("### Input Data")
    col1, col2 = st.columns(2)

    home_value = col1.number_input(
        "Home Value",
        min_value=0,
        value=6000000)
    deposit = col1.number_input(
        "Deposit",
        min_value=0,
        value=1000000)
    interest_rate = col2.number_input(
        "Interest Rate (in %)",
        min_value=0.0,
        value=4.0,)
    loan_term = col2.number_input(
        "Loan Term (in years)",
        min_value=1,
        value=30,)

    # Calculate repayments
    loan_amount = home_value - deposit
    monthly_interest_rate = (interest_rate / 100) / 12
    number_of_payments = loan_term * 12

    # Standard mortgage payment formula 
    # M = P × [ r(1 + r)^n ] / [ (1 + r)^n − 1 ]
    monthly_payment = (
        loan_amount
        * (monthly_interest_rate * (1 + monthly_interest_rate) ** number_of_payments)
        / ((1 + monthly_interest_rate) ** number_of_payments - 1)
    )

    total_payments = monthly_payment * number_of_payments
    total_interest = total_payments - loan_amount

    # ────────────────────────────────────────────────
    # Display section
    st.write("### Repayments")
    col1, col2, col3 = st.columns(3)
    col1.metric(
        label="Monthly Repayment",
        value=f"${monthly_payment:,.2f}") #.2f for decimal places
    col1.metric(
        label="Loan Amount",
        value=f"${loan_amount:,.0f}") #.0f for no decimal places
    col2.metric(
        label="Total Repayments",
        value=f"${total_payments:,.0f}") # :, for thousands separator
    col2.metric(
        label="Total Interest",
        value=f"${total_interest:,.0f}")
    col3.metric(
        label="Interest as % of Loan",
        value=f"{(total_interest/loan_amount*100):.2f}%")
    # Build amortization schedule
    schedule = []
    remaining_balance = loan_amount

    for i in range(1, number_of_payments + 1):
        interest_payment = remaining_balance * monthly_interest_rate
        principal_payment = monthly_payment - interest_payment
    
        remaining_balance -= principal_payment
    
        # Prevent tiny negative balance due to floating-point precision
        if remaining_balance < 0:
            remaining_balance = 0
    
        year = math.ceil(i / 12) # .ceil 13/12 = 2 
    
        schedule.append({
            'Month': i,
            'Payment': monthly_payment,
            'Principal': principal_payment,
            'Interest': interest_payment,
            'Remaining Balance': remaining_balance,
            'Year': year
        })

    df = pd.DataFrame(
        schedule,
        columns=['Month', 'Payment', 'Principal', 'Interest', 'Remaining Balance', 'Year'])

    #df.to_csv("mortgage_full_schedule.csv", index=False) ## add
    # after df creation
    today_date = datetime.now().strftime("%Y%m%d")
    with st.sidebar:
        st.download_button(
            label="download (CSV)",
            data=df.to_csv(index=False).encode('utf-8'),
            file_name=f"mortgage_schedule_full_{today_date}.csv",
            mime="text/csv" # mime represents the file type
        )
    st.markdown("---")

    with st.sidebar:
        st.header("Sidebar")
        st.selectbox("Filter", ["All", "Type A", "Type B"])

    # Display amortization schedule as chart
    st.write("### Payment Schedule")
    payments_df = df[["Year", "Remaining Balance"]].groupby("Year").min() # take the last period of each year
    #payments_df.to_csv("mortgage_yearly_schedule_.csv") ## add
    st.line_chart(payments_df)

    st.dataframe(payments_df, use_container_width=True)   # interactive table
