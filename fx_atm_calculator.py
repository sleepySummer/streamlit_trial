# fx_atm_calculator.py
import streamlit as st
import pandas as pd
import math
import numpy as np
import plotly.graph_objects as go

def norm_cdf(x):
    """計算標準常態分配累積機率 (代替 scipy.stats.norm.cdf 以減少依賴)"""
    return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0

@st.cache_data
def calculate_fx_option(spot, forward_points, vol_pct, days, risk_free_rate, notional, atm_convention):
    """
    計算 FX ATM Option 的 Strike 與 Premium
    """
    # 基礎變數轉換 (以 JPY 慣例為例，1 pip = 0.01)
    T = days / 365.0
    sigma = vol_pct / 100.0
    r = risk_free_rate / 100.0
    
    # 計算 Forward (F)
    forward = spot + (forward_points / 100.0)
    
    # 根據定義決定 Strike (K)
    if atm_convention == "Spot ATM (ATMS)":
        K = spot
    elif atm_convention == "Forward ATM (ATMF)":
        K = forward
    elif atm_convention == "Delta-Neutral ATM (DNS)":
        # DNS 公式: K = F * exp(0.5 * sigma^2 * T)
        K = forward * math.exp(0.5 * (sigma ** 2) * T)
    else:
        K = forward
        
    # Black-76 定價邏輯
    if T > 0 and sigma > 0:
        d1 = (math.log(forward / K) + 0.5 * (sigma ** 2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)
        
        # 折現因子 (Discount Factor)
        DF = math.exp(-r * T)
        
        # Call & Put Value (以報價貨幣計價的點數)
        call_pips = DF * (forward * norm_cdf(d1) - K * norm_cdf(d2))
        put_pips = DF * (K * norm_cdf(-d2) - forward * norm_cdf(-d1))
    else:
        call_pips = max(0, forward - K)
        put_pips = max(0, K - forward)
        
    # 計算現金價值 (Cash Premium)
    call_cash = (call_pips / spot) * notional if spot > 0 else 0
    put_cash = (put_pips / spot) * notional if spot > 0 else 0
    
    return {
        "Forward": forward,
        "Strike": K,
        "Call Pips": call_pips,
        "Put Pips": put_pips,
        "Call Cash": call_cash,
        "Put Cash": put_cash
    }

def show_atm_calculator():
    st.title("FX ATM Option Calculator")
    st.write("### Market Inputs")
    
    # 使用欄位排列輸入區塊 (對齊你其他模組的風格)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        spot = st.number_input("Spot Rate (e.g. USD/JPY)", min_value=0.0, value=150.00, step=0.1, format="%.2f")
        notional = st.number_input("Notional Amount (Base CCY)", min_value=0, value=10000000, step=1000000)
    
    with col2:
        vol_pct = st.number_input("ATM Volatility (%)", min_value=0.1, value=8.50, step=0.1)
        days = st.number_input("Tenor (Days to Expiry)", min_value=1, value=90)
        
    with col3:
        forward_points = st.number_input("Forward Points (pips)", value=-160.0, step=1.0)
        risk_free_rate = st.number_input("Domestic Rate (%)", min_value=0.0, value=5.0, step=0.1)

    st.write("### Option Specifications")
    atm_convention = st.selectbox(
        "Select ATM Convention",
        ["Delta-Neutral ATM (DNS)", "Spot ATM (ATMS)", "Forward ATM (ATMF)"],
        help="DNS 是外匯市場最常見的基準，令 Call 與 Put 的 Delta 互相抵銷。"
    )

    # 執行運算
    results = calculate_fx_option(spot, forward_points, vol_pct, days, risk_free_rate, notional, atm_convention)

    # ──────────────結果顯示區塊───────────
    st.markdown("---")
    st.write("### Pricing Results")
    
    # 運用 st.metric 呈現報價核心變數 (對齊 mortgage_calculator 的風格)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Calculated Strike", f"{results['Strike']:.4f}")
    c2.metric("Outright Forward", f"{results['Forward']:.4f}")
    c3.metric("Call Premium (pips)", f"{results['Call Pips']:.2f}")
    c4.metric("Put Premium (pips)", f"{results['Put Pips']:.2f}")

    # 顯示現金成本
    st.info(f"**Premium Cash Amount:** Call costs **${results['Call Cash']:,.0f}** | Put costs **${results['Put Cash']:,.0f}**")

    # ──────────────圖表視覺化區塊───────────
    st.write("### Straddle Payoff at Maturity")
    
    # 產生情境分析資料 (以 Strike 點上下 5% 區間)
    strike = results['Strike']
    spot_range = np.linspace(strike * 0.95, strike * 1.05, 100)
    
    # Straddle (同時買入 Call 與 Put) 到期損益
    call_payoff = np.maximum(spot_range - strike, 0) - results['Call Pips']
    put_payoff = np.maximum(strike - spot_range, 0) - results['Put Pips']
    straddle_payoff = call_payoff + put_payoff
    
    fig = go.Figure()
    
    # 繪製 Straddle 損益曲線 (對齊 fx_forward_calculator 的配色邏輯)
    fig.add_trace(go.Scatter(
        x=spot_range, y=straddle_payoff,
        mode='lines',
        name='Straddle Net Payoff',
        line=dict(color='#00AEEF', width=3)
    ))
    
    # 標示 Strike 點
    fig.add_vline(x=strike, line_dash="dash", line_color="#002B5E", annotation_text="Strike")
    # 標示損益兩平線
    fig.add_hline(y=0, line_color="black", line_width=1)
    
    fig.update_layout(
        xaxis_title="Spot Rate at Expiry",
        yaxis_title="Net Payoff (pips)",
        hovermode="x unified",
        margin=dict(l=0, r=0, t=30, b=0)
    )
    
    st.plotly_chart(fig, use_container_width=True)

    # 匯出資料表 (對齊 mortgage_calculator 的互動表格)
    with st.expander("View Payoff Matrix"):
        df_payoff = pd.DataFrame({
            "Spot at Expiry": spot_range,
            "Call Payoff (pips)": call_payoff,
            "Put Payoff (pips)": put_payoff,
            "Straddle Net (pips)": straddle_payoff
        })