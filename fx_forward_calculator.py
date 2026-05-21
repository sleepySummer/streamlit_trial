# fx_forward_calculator.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

@st.cache_data
def calculate_fx_metrics(spot, points_dict):
    """
    計算 Outright Rate 與 Annualized Carry
    包含快取機制以優化頻繁的點數更新計算
    """
    # 市場慣例：JPY 的 point 通常為小數點後兩位 (1 pip = 0.01 JPY)
    results = []
    for tenor, data in points_dict.items():
        days = data['days']
        points = data['points']
        
        outright = spot + (points / 100)
        # 避免除以零的錯誤
        carry = (points / 100 / spot) * (360 / days) * 100 if days > 0 else 0
        
        results.append({
            "Tenor": tenor,
            "Days": days,
            "Forward Points": points,
            "Outright Rate": outright,
            "Annualized Carry (%)": carry
        })
    return pd.DataFrame(results)

def show_fx_calculator():
    st.title("USD/JPY Forward Curve Analytics")
    st.markdown("### Market Inputs")
    
    # 使用欄位排列輸入區塊
    col1, col2 = st.columns([1, 2])
    with col1:
        spot_rate = st.number_input("USD/JPY Spot Rate", min_value=0.0, value=150.00, step=0.1, format="%.2f")
    
    st.markdown("### Forward Points (in pips)")
    st.caption("Hint: 由於美元利率 > 日圓利率，正常情況下點數應為負值 (Backwardation)")
    
    c1, c2, c3, c4 = st.columns(4)
    pts_1m = c1.number_input("1M Points", value=-55.0, step=1.0)
    pts_3m = c2.number_input("3M Points", value=-160.0, step=1.0)
    pts_6m = c3.number_input("6M Points", value=-310.0, step=1.0)
    pts_1y = c4.number_input("1Y Points", value=-600.0, step=1.0)

    # 組合數據字典
    points_dict = {
        '1M': {'days': 30, 'points': pts_1m},
        '3M': {'days': 90, 'points': pts_3m},
        '6M': {'days': 180, 'points': pts_6m},
        '1Y': {'days': 360, 'points': pts_1y}
    }

    # 執行運算
    df = calculate_fx_metrics(spot_rate, points_dict)

    st.markdown("---")
    st.write("### Forward Pricing & Carry")
    
    # 格式化 DataFrame 顯示
    st.dataframe(df.style.format({
        "Forward Points": "{:.1f}",
        "Outright Rate": "{:.3f}",
        "Annualized Carry (%)": "{:.2f}%"
    }), use_container_width=True)

    # 繪製遠期曲線 (Forward Curve)
    st.write("### Forward Curve (Outright)")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["Days"], 
        y=df["Outright Rate"],
        mode='lines+markers',
        name='Outright Rate',
        line=dict(shape='spline', color='#00AEEF', width=3), # 使用 spline 讓曲線平滑
        marker=dict(size=10, color='#002B5E')
    ))
    
    fig.update_layout(
        xaxis_title="Days to Maturity",
        yaxis_title="USD/JPY Outright Rate",
        xaxis=dict(tickvals=df["Days"], ticktext=df["Tenor"]), # 強制 X 軸顯示 Tenor 名稱
        hovermode="x unified",
        margin=dict(l=0, r=0, t=30, b=0)
    )
    st.plotly_chart(fig, use_container_width=True)