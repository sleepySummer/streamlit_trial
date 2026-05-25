# stock_option_calculator.py
import streamlit as st
import pandas as pd
import math
import numpy as np
import plotly.graph_objects as go

def norm_cdf(x):
    """計算標準常態分配累積機率 (CDF)"""
    return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0

def norm_pdf(x):
    """計算標準常態分配機率密度 (PDF)"""
    return math.exp(-0.5 * x**2) / math.sqrt(2.0 * math.pi)

@st.cache_data
def calculate_bsm_option(spot, strike, dte, risk_free_rate, div_yield, iv):
    """
    使用 Black-Scholes-Merton 模型計算股票/ETF期權的理論價格與 Greeks
    """
    T = dte / 365.0
    r = risk_free_rate / 100.0
    q = div_yield / 100.0
    sigma = iv / 100.0
    
    # 避免到期日為 0 的除以零錯誤
    if T <= 0:
        T = 1e-5
        
    d1 = (math.log(spot / strike) + (r - q + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    
    # 折現與股息因子
    exp_rT = math.exp(-r * T)
    exp_qT = math.exp(-q * T)
    
    # 理論價格計算
    call_price = spot * exp_qT * norm_cdf(d1) - strike * exp_rT * norm_cdf(d2)
    put_price = strike * exp_rT * norm_cdf(-d2) - spot * exp_qT * norm_cdf(-d1)
    
    # Greeks 計算 (以 Put 為主，對齊截圖)
    # Delta
    call_delta = exp_qT * norm_cdf(d1)
    put_delta = exp_qT * (norm_cdf(d1) - 1)
    
    # Gamma (Call 與 Put 相同)
    gamma = (exp_qT * norm_pdf(d1)) / (spot * sigma * math.sqrt(T))
    
    # Vega (通常除以 100，表示 1% IV 變動的影響)
    vega = (spot * exp_qT * norm_pdf(d1) * math.sqrt(T)) / 100.0
    
    # Theta (通常除以 365，表示 1 天的時間流逝影響)
    term1 = -(spot * sigma * exp_qT * norm_pdf(d1)) / (2 * math.sqrt(T))
    call_theta = (term1 - r * strike * exp_rT * norm_cdf(d2) + q * spot * exp_qT * norm_cdf(d1)) / 365.0
    put_theta = (term1 + r * strike * exp_rT * norm_cdf(-d2) - q * spot * exp_qT * norm_cdf(-d1)) / 365.0
    
    # Rho (通常除以 100，表示 1% 利率變動的影響)
    call_rho = (strike * T * exp_rT * norm_cdf(d2)) / 100.0
    put_rho = (-strike * T * exp_rT * norm_cdf(-d2)) / 100.0
    
    return {
        "call_price": call_price, "put_price": put_price,
        "put_delta": put_delta, "gamma": gamma,
        "put_theta": put_theta, "vega": vega, "put_rho": put_rho
    }

def show_stock_option_calculator():
    st.title("Stock/ETF Option Calculator")
    st.caption("驗證基準：VOO 465 Put (Long Put)")
    
    st.write("### Inputs (對齊截圖數據)")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        spot = st.number_input("Underlying Price (Spot)", value=517.825, step=1.0, format="%.3f")
        strike = st.number_input("Strike Price", value=465.00, step=1.0, format="%.2f")
    
    with col2:
        iv = st.number_input("Implied Volatility (%)", value=28.07, step=0.1, format="%.2f")
        # 由於截圖中沒有明確的 DTE (Days to Expiration)，我們設一個預設值，你可以微調來對齊 Greeks
        dte = st.number_input("Days to Expiration (DTE)", value=270, step=1)
        
    with col3:
        # VOO 的預估股息與當前無風險利率
        risk_free_rate = st.number_input("Risk-Free Rate (%)", value=5.25, step=0.1)
        div_yield = st.number_input("Dividend Yield (%)", value=1.35, step=0.1)

    # 用戶實際支付的 Premium (從 Ask Price 取得)
    market_premium = st.number_input("Market Premium Paid (e.g. Ask Price)", value=3.40, step=0.01)

    # 執行運算
    bsm = calculate_bsm_option(spot, strike, dte, risk_free_rate, div_yield, iv)
    
    st.markdown("---")
    
    # ──────────────Risk & Reward 區塊 (模擬右側面板)───────────
    st.write("### Risk & Reward Profile (1 Contract = 100 Shares)")
    max_loss = market_premium * 100
    breakeven = strike - market_premium
    max_profit = breakeven * 100
    
    r1, r2, r3 = st.columns(3)
    r1.metric("Max Profit", f"${max_profit:,.0f}")
    r2.metric("Breakeven", f"${breakeven:,.2f}")
    r3.metric("Max Loss", f"${max_loss:,.2f}")
    
    # ──────────────Greeks 區塊───────────
    st.write("### Greeks (Theoretical)")
    st.caption("提示：由於截圖未顯示確切的交易日與無風險利率，你可以微調上方 DTE 與 Rate 來讓以下數值完美吻合截圖 (-0.12, 0.0039, 等)。")
    
    g1, g2, g3, g4, g5 = st.columns(5)
    g1.metric("Delta", f"{bsm['put_delta']:.4f}")
    g2.metric("Gamma", f"{bsm['gamma']:.4f}")
    g3.metric("Theta", f"{bsm['put_theta']:.4f}")
    g4.metric("Vega", f"{bsm['vega']:.4f}")
    g5.metric("Rho", f"{bsm['put_rho']:.4f}")

    st.markdown("---")
    
    # ──────────────圖表視覺化區塊───────────
    st.write("### Long Put Payoff at Expiration")
    
    # 產生情境分析資料 (以 Strike 點上下 20% 區間)
    spot_range = np.linspace(strike * 0.7, spot * 1.1, 100)
    
    # Long Put 到期損益
    put_payoff = np.maximum(strike - spot_range, 0) - market_premium
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=spot_range, y=put_payoff,
        mode='lines',
        name='Put Net Payoff',
        line=dict(color='#E53935', width=3) # 使用紅色表示 Bearish Strategy
    ))
    
    # 標示 Break-even 與 Strike
    fig.add_vline(x=breakeven, line_dash="dash", line_color="black", annotation_text="Breakeven")
    fig.add_vline(x=strike, line_dash="dot", line_color="#002B5E", annotation_text="Strike")
    fig.add_hline(y=0, line_color="black", line_width=1)
    
    fig.update_layout(
        xaxis_title="VOO Price at Expiration",
        yaxis_title="Net Payoff ($ per share)",
        hovermode="x unified",
        margin=dict(l=0, r=0, t=30, b=0)
    )
    
    st.plotly_chart(fig, use_container_width=True)