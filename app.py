# app.py
import streamlit as st
import pandas as pd
import math
from datetime import datetime

# 引入兩個計算機模組
from mortgage_calculator import show_calculator
from fx_forward_calculator import show_fx_calculator 
from fx_atm_calculator import show_atm_calculator 
from stock_option_calculator import show_stock_option_calculator
from fx_vanilla_calculator import show_vanilla_calculator

# ──────────────登入系統模組───────────
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

authenticator.login(
    location='main',
    fields={
        'Form name': '登入系統',
        'Username': '使用者名稱',
        'Password': '密碼',
        'Login': '登入',
        'Invalid credentials': '帳號或密碼錯誤，請重試'
    }
)

if st.session_state["authentication_status"]:
    # 登入成功
    st.sidebar.success(f"歡迎回來 {st.session_state['name']}")
    authenticator.logout('登出', 'sidebar')

    # ──────────────導航切換區塊───────────
    st.sidebar.markdown("---")
    st.sidebar.header("Tool Navigation")
    
    # 建立應用程式選單
    app_mode = st.sidebar.radio(
        "請選擇你要使用的計算機：",
        [
            "Mortgage Calculator", 
            "FX Forward Calculator", 
            "FX ATM Option Calculator",
            "FX Vanilla Option Calculator",
            "Stock/ETF Option Calculator"
        ]
    )

    st.sidebar.markdown("---")

    # 根據使用者的選擇，呼叫對應的函式
    if app_mode == "Mortgage Calculator":
        show_calculator()
    elif app_mode == "FX Forward Calculator":
        show_fx_calculator()
    elif app_mode == "FX ATM Option Calculator":
        show_atm_calculator()
    elif app_mode == "Stock/ETF Option Calculator":
        show_stock_option_calculator()
    elif app_mode == "FX Vanilla Option Calculator":
        show_vanilla_calculator()
elif st.session_state["authentication_status"] is False:
    st.error('帳號或密碼錯誤')
elif st.session_state["authentication_status"] is None:
    st.warning('請輸入帳號與密碼')