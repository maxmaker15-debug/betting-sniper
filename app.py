import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import subprocess
import sys
import config

# --- 1. CONFIGURAZIONE & STILE ---
st.set_page_config(
    page_title="Sniper Betting Elite V8",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS "Pro Trader" (Scuro, Tecnico, Pulito)
st.markdown("""
    <style>
        .stApp { background-color: #0e1117; }
        .css-1r6slb0, .stDataFrame, .stPlotlyChart {
            background-color: #1a1c24;
            border: 1px solid #2d2f36;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        h1, h2, h3, h4 { color: #e6e6e6; font-family: 'Segoe UI', sans-serif; font-weight: 600; }
        div[data-testid="stMetricValue"] { font-size: 1.8rem !important; color: #00CC96 !important; font-weight: 700; }
        div[data-testid="stMetricLabel"] { color: #909090; font-size: 0.9rem; }
        hr { border-color: #2d2f36; }
        .stButton button { width: 100%; border-radius: 6px; font-weight: 600; }
    </style>
""", unsafe_allow_html=True)

# --- FUNZIONI BACKEND ---
def load_data(filename):
    if not os.path.exists(filename): return pd.DataFrame()
    try: return pd.read_csv(filename)
    except: return pd.DataFrame()

def save_data(df, filename):
    df.to_csv(filename, index=False)

def run_scanner():
    try:
        subprocess.run([sys.executable, "scanner_calcio.py"], check=True)
        return True
    except Exception as e:
        st.error(f"Errore: {e}")
        return False

# --- CARICAMENTO DATI ---
df_storico = load_data(config.FILE_STORICO)
df_pending = load_data(config.FILE_PENDING)

# --- 🧠 IL CERVELLO ANALITICO (CALCOLI AVANZATI) ---
saldo_iniziale = config.BANKROLL_TOTALE
profitto_totale = 0.0
volume_giocato = 0.0
roi = 0.0
roe = 0.0
rotazione_capitale = 0.0
n_ops = 0

if not df_storico.empty:
    if 'Profitto_Reale' not in df_storico.columns: df_storico['Profitto_Reale'] = 0.0
    if 'Stake_Euro' not in df_storico.columns: df_storico['Stake_Euro'] = 0.0
    
    profitto_totale = df_storico['Profitto_Reale'].sum()
    volume_giocato = df_storico['Stake_Euro'].sum()
    n_ops = len(df_storico)
