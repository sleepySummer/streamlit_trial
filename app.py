# app.py
import streamlit as st
import pandas as pd
#import matplotlib.pyplot as plt
import math
from datetime import datetime
from mortgage_calculator import show_calculator

# ──────────────add login part (start)───────────
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

# login part（outside the actual app）
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# 呼叫 login()，它會自動顯示表單
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
    # 登入成功 → 顯示原本內容
    st.sidebar.success(f"歡迎回來 {st.session_state['name']}")
    authenticator.logout('登出', 'sidebar')

    # ───── 以下是你原本的全部程式碼 ─────
    show_calculator()

elif st.session_state["authentication_status"] is False:
    st.error('帳號或密碼錯誤')
elif st.session_state["authentication_status"] is None:
    st.warning('請輸入帳號與密碼')
    