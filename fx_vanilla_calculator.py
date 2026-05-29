# fx_vanilla_calculator.py
import streamlit as st
import pandas as pd
import math
import numpy as np
import plotly.graph_objects as go

def norm_cdf(x):
    return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0

def norm_pdf(x):
    return math.exp(-0.5 * x**2) / math.sqrt(2.0 * math.pi)

@st.cache_data
def calculate_fx_vanilla(spot, strike, dte, dom_rate, for_rate, iv, notional):
    T = dte / 365.0 #standardize to year fraction, 360 or 365 depending on ccy #stochastic calculus requires time in years
    r_d = dom_rate / 100.0 #quote ccy rate
    r_f = for_rate / 100.0 #base ccy rate
    sigma = iv / 100.0 #implied volatility as decimal
    
    if T <= 0: T = 1e-5
    # normalize the event by dividing by the volatility and time, which gives us a standard normal variable
    # d1 = expected good case normalized, d2 = expected bad case normalized, the difference is the volatility drag
    d1 = (math.log(spot / strike) + (r_d - r_f + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    
    exp_rd = math.exp(-r_d * T) # e^{-r_d T} # discount to PV using domestic rate for the premium, and foreign rate for the forward price, which is the expected future spot price under risk-neutral measure
    exp_rf = math.exp(-r_f * T) # e^{-r_f T} # discount to PV using foreign rate for the forward price, which is the expected future spot price under risk-neutral measure
    
    forward = spot * math.exp((r_d - r_f) * T)
    
    # N(d1) = Prob of exercising the option in a good state 
    # N(d2) = Prob of exercising the option in a bad state
    call_price_quote = spot * exp_rf * norm_cdf(d1) - strike * exp_rd * norm_cdf(d2)
    put_price_quote = strike * exp_rd * norm_cdf(-d2) - spot * exp_rf * norm_cdf(-d1)
    
    call_pct_base = (call_price_quote / spot) * 100
    put_pct_base = (put_price_quote / spot) * 100
    
    call_cash = (call_pct_base / 100) * notional
    put_cash = (put_pct_base / 100) * notional

    # Theoretical Greeks
    call_delta = exp_rf * norm_cdf(d1)
    put_delta = exp_rf * (norm_cdf(d1) - 1)
    
    gamma = (exp_rf * norm_pdf(d1)) / (spot * sigma * math.sqrt(T))
    vega = (spot * exp_rf * norm_pdf(d1) * math.sqrt(T)) / 100.0
    
    # 🌟 新增：Position / Cash Greeks (對齊銀行終端機)
    # Cash Delta
    call_delta_cash = call_delta * notional
    put_delta_cash = put_delta * notional
    
    # Cash Vega in Base CCY (USD)
    vega_cash_quote = vega * notional
    vega_cash_base = vega_cash_quote / spot
    
    # 1% Cash Gamma in Base CCY (USD)
    gamma_1pct_cash = gamma * notional * (spot * 0.01)
    
    return {
        "forward": forward,
        "call_pct_base": call_pct_base, "put_pct_base": put_pct_base,
        "call_cash": call_cash, "put_cash": put_cash,
        "call_delta": call_delta, "put_delta": put_delta,
        "call_delta_cash": call_delta_cash, "put_delta_cash": put_delta_cash,
        "gamma": gamma, "vega": vega,
        "gamma_1pct_cash": gamma_1pct_cash, "vega_cash_base": vega_cash_base,
        "call_price_quote": call_price_quote, "put_price_quote": put_price_quote,
        "d1": d1, "d2": d2,
        "N(d1)": norm_cdf(d1), "N(d2)": norm_cdf(d2), "N(-d1)": norm_cdf(-d1), "N(-d2)": norm_cdf(-d2),
        "exp_rd": exp_rd, "exp_rf": exp_rf
    }

def show_vanilla_calculator():
    st.title("FX Vanilla Option Calculator")
    st.caption("驗證基準：USD/JPY Put, Premium & Cash Greeks in USD")
    
    st.write("### Market Inputs (Mid-Price)")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        spot = st.number_input("Spot Rate (e.g. USD/JPY)", value=159.366, step=0.1, format="%.3f")
        notional = st.number_input("Notional (Base CCY)", value=100000, step=10000)
    
    with col2:
        strike = st.number_input("Strike Price", value=157.00, step=1.0, format="%.2f")
        dte = st.number_input("Days to Expiration (DTE)", value=92, step=1)
        
    with col3:
        iv = st.number_input("Implied Volatility (%)", value=7.230, step=0.1, format="%.3f")
        for_rate = st.number_input("Base CCY Rate (%)", value=3.66, step=0.1)
        dom_rate = st.number_input("Quote CCY Rate (%)", value=0.74, step=0.1)

    strategy = st.radio("Select Strategy", ["Put (e.g. USD Put / JPY Call)", "Call (e.g. USD Call / JPY Put)"], horizontal=True)

    calc = calculate_fx_vanilla(spot, strike, dte, dom_rate, for_rate, iv, notional)
    
    st.markdown("---")
    
    st.write("### Pricing Details")
    is_put = "Put" in strategy
    premium_pct = calc['put_pct_base'] if is_put else calc['call_pct_base']
    premium_cash = calc['put_cash'] if is_put else calc['call_cash']
    delta_cash = calc['put_delta_cash'] if is_put else calc['call_delta_cash']

    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Outright Forward", f"{calc['forward']:.4f}")
    r2.metric("Premium (Base CCY %)", f"{premium_pct:.4f}%")
    r3.metric("Premium (Cash Value)", f"${premium_cash:,.2f}")
    r4.metric("Delta Cash (Base CCY)", f"${delta_cash:,.0f}") 
    
    st.markdown("---")

    #################################################################################################################
    bs1, bs2, bs3 = st.columns(3)

    with bs1:
        st.metric("d1", f"{calc['d1']:.4f}")
        st.metric("N(d1)", f"{calc['N(d1)']:.4f}")
        st.metric("N(-d1)", f"{calc['N(-d1)']:.4f}")
    with bs2:
        st.metric("d2", f"{calc['d2']:.4f}")
        st.metric("N(d2)", f"{calc['N(d2)']:.4f}")
        st.metric("N(-d2)", f"{calc['N(-d2)']:.4f}")
    with bs3:
        st.metric("Exp(-r_f T)", f"{calc['exp_rf']:.4f}")
        st.metric("Exp(-r_d T)", f"{calc['exp_rd']:.4f}")

    st.markdown("---")
    st.write("### Greeks (Theoretical vs. Desk Position)")
    st.caption("Desk Position Greeks 顯示的是你**買入**此合約的曝險金額（基準貨幣），若為銀行端（賣方）則數字正負號相反。")

    # 使用欄位對照理論值與現金值
    g1, g2, g3 = st.columns(3)
    
    with g1:
        st.metric("Theoretical Delta", f"{calc['put_delta'] if is_put else calc['call_delta']:.4f}")
        st.metric("Position Delta (USD)", f"${delta_cash:,.0f}")
        
    with g2:
        st.metric("Theoretical Gamma", f"{calc['gamma']:.4f}")
        st.metric("1% Cash Gamma (USD)", f"${calc['gamma_1pct_cash']:,.0f}")
        
    with g3:
        st.metric("Theoretical Vega", f"{calc['vega']:.4f}")
        st.metric("Cash Vega (USD)", f"${calc['vega_cash_base']:,.0f}")
        
    st.markdown("---")
    
    st.write(f"### {strategy.split(' ')[0]} Payoff at Expiration")
    spot_range = np.linspace(strike * 0.9, spot * 1.05, 100)
    premium_quote = calc['put_price_quote'] if is_put else calc['call_price_quote']
    
    if is_put:
        payoff = np.maximum(strike - spot_range, 0) - premium_quote
        color = '#E53935'
    else:
        payoff = np.maximum(spot_range - strike, 0) - premium_quote
        color = '#00AEEF'
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=spot_range, y=payoff, mode='lines', name=f'{strategy.split(" ")[0]} Payoff', line=dict(color=color, width=3)))
    fig.add_vline(x=strike, line_dash="dot", line_color="#002B5E", annotation_text="Strike")
    fig.add_hline(y=0, line_color="black", line_width=1)
    
    fig.update_layout(xaxis_title="Spot Rate", yaxis_title="Net Payoff (Quote CCY)", hovermode="x unified", margin=dict(l=0, r=0, t=30, b=0))
    st.plotly_chart(fig, use_container_width=True)