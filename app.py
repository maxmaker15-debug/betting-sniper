import streamlit as st
import pandas as pd
import plotly.express as px
import os
import subprocess
import sys
import config
import time
from io import StringIO

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="Sniper V53 Diagnostic", 
    page_icon="🦅", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- CSS ---
st.markdown("""
    <link href="https://cdn.jsdelivr.net/npm/remixicon@3.5.0/fonts/remixicon.css" rel="stylesheet">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        .stApp { background-color: #050505; font-family: 'Inter', sans-serif; color: #e0e0e0; }
        .block-container { padding-top: 4rem !important; }
        div[data-testid="stMetric"], div[data-testid="stDataFrame"], div[data-testid="stPlotlyChart"] { 
            background-color: #111; border: 1px solid #333; border-radius: 8px; padding: 15px;
        }
        h1, h2, h3 { color: #fff; font-weight: 800; margin-bottom: 15px; }
        .header-logo { font-size: 1.5rem; font-weight: 900; color: #fff; border-bottom: 1px solid #333; padding-bottom: 20px; margin-bottom: 20px; text-align: center; }
        .highlight { color: #00E096; }
        .stButton button { background-color: #222; color: #fff; border: 1px solid #444; font-weight: 600; width: 100%; transition: all 0.2s; }
        .stButton button:hover { border-color: #00E096; color: #00E096; transform: scale(1.02); }
    </style>
""", unsafe_allow_html=True)

def clean_num(x):
    if isinstance(x, str): return x.replace(',', '.').replace('€', '').replace('%', '').strip()
    return x

def enforce_schema(df):
    if df.empty: return df
    try:
        rename = {"Quota_Betfair": "Q_Betfair", "Quota_Target": "Q_Target", "Quota_Reale_Pinna": "Q_Reale", "Valore_%": "EV_%", "Stake_Euro": "Stake_Ready"}
        df = df.rename(columns=rename)
        
        cols_float = ["Q_Betfair", "Q_Target", "Q_Reale", "EV_%", "Profitto"]
        for c in cols_float: 
            if c in df.columns: df[c] = df[c].astype(str).apply(clean_num).apply(pd.to_numeric, errors='coerce').fillna(0.0)
        
        cols_int = ["Stake_Ready", "Stake_Limit"]
        for c in
