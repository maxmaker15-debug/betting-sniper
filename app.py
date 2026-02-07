import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import subprocess
import sys
import config

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="Sniper Betting Suite",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS 2026 ---
st.markdown("""
    <link href="https://cdn.jsdelivr.net/npm/remixicon@3.5.0/fonts/remixicon.css" rel="stylesheet">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap');
        
        .stApp {
            background-color: #080808;
            font-family: 'Inter', sans-serif;
        }

        /* FIX IMPAGINAZIONE */
        .block-container {
            padding-top: 3.5rem !important; 
            padding-bottom: 3rem !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
        }

        /* CARD STYLE */
        div[data-testid="stMetric"], div[data-testid="stDataFrame"], div[data-testid="stPlotlyChart"] {
            background-color: #121212;
            border: 1px solid #333;
            border-radius: 6px;
            padding: 12px 15px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.4);
            transition: border-color 0.3s ease;
        }
        div[data-testid="stMetric"]:hover { border-color: #555; }

        /* TITOLI */
        h1, h2, h3 { color: #fff; font-weight: 700; margin-bottom: 10px; }
        
        /* METRICHE */
        div[data-testid="stMetricValue"] {
            font-size: 1.8rem !important;
            color: #00E096 !important;
            font-weight: 700;
        }
        div[data-testid="stMetricLabel"] {
            color: #777;
            font-size: 0.8rem;
            text-transform: uppercase;
            font-weight: 500;
        }

        /* SIDEBAR */
        section[data-testid="stSidebar"] { background-color: #0b0b0b; border-right: 1px solid #222; }
        
        /* PULSANTI */
        .stButton button {
            background-color: #1a1a1a;
            color: #ddd;
            border: 1px solid #333;
            border-radius: 4px;
            text-transform: uppercase;
            font-weight: 600;
            padding: 0.5rem 1rem;
            width: 100%;
        }
        .stButton button:hover { border-color: #00E096; color: #00E096; }

        /* HEADER LOGO */
        .header-logo {
            font-size: 1.2rem;
            font-weight: 800;
            color: #fff;
            border-bottom: 1px solid #222;
            padding-bottom: 10px;
            margin-bottom: 15px;
            letter-spacing: 1px;
        }
        .highlight { color: #00E096; }
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
    log_scan = []
    # 1. Calcio
    if os.path.exists("scanner_calcio.py"):
        try:
            subprocess.run([sys.executable, "scanner_calcio.py"], check=True)
            log_scan.append("Calcio: OK")
        except: log_scan.append("Calcio: Error")
    # 2. Tennis
    if os.path.exists("scanner_tennis.py"):
        try:
            subprocess.run([sys.executable, "scanner_tennis.py"], check=True)
            log_scan.append("Tennis: OK")
        except: log_scan.append("Tennis: Error")
    return log_scan

# --- CARICAMENTO ---
df_storico = load_data(config.FILE_STORICO)
df_pending = load_data(config.FILE_PENDING)

# --- KPI ENGINE ---
saldo_iniziale = config.BANKROLL_TOTALE
profitto_totale = 0.0
volume_giocato = 0.0
roi = 0.0
roe = 0.0
rotazione = 0.0
n_ops = 0

if not df_storico.empty:
    if 'Profitto_Reale' not in df_storico.columns: df_storico['Profitto_Reale'] = 0.0
    if 'Stake_Euro' not in df_storico.columns: df_storico['Stake_Euro'] = 0.0
    profitto_totale = df_storico['Profitto_Reale'].sum()
    volume_giocato = df_storico['Stake_Euro'].sum()
    n_ops = len(df_storico)
    if volume_giocato > 0: roi = (profitto_totale / volume_giocato) * 100
    if saldo_iniziale > 0: roe = (profitto_totale / saldo_iniziale) * 100
    if saldo_iniziale > 0: rotazione = volume_giocato / saldo_iniziale

saldo_attuale = saldo_iniziale + profitto_totale

# ==============================================================================
# SIDEBAR
# ==============================================================================
with st.sidebar:
    st.markdown('<div class="header-logo"><i class="ri-crosshair-2-line highlight"></i> SNIPER<span class="highlight">SUITE</span></div>', unsafe_allow_html=True)
    
    # QUI C'ERA L'ERRORE - FIXATO
    menu = st.radio("MENU", ["◈ DASHBOARD", "◎ RADAR", "▤ REGISTRO"], label_visibility="collapsed")
    
    st.markdown("---")
    c1, c2 = st.columns(2)
    c1.metric("BANKROLL", f"{config.BANKROLL_TOTALE/1000:.0f}k")
    c2.metric("LIMIT", f"{config.STAKE_MASSIMO}€")
    st.markdown("---")
    if st.button("REBOOT"): st.rerun()

# ==============================================================================
# PAGINA 1: DASHBOARD
# ==============================================================================
if menu == "◈ DASHBOARD":
    st.markdown('<h3><i class="ri-dashboard-3-line"></i> PERFORMANCE ANALYTICS</h3>', unsafe_allow_html=True)
    st.write("")
    
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("BANKROLL", f"{saldo_attuale:.2f} €", delta=f"{profitto_totale:.2f} €")
    k2.metric("NET PROFIT", f"{profitto_totale:.2f} €")
    k3.metric("ROI", f"{roi:.2f} %")
    k4.metric("ROE", f"{roe:.2f} %")
    
    st.markdown("<br>", unsafe_allow_html=True)

    e1, e2, e3, e4 = st.columns(4)
    e1.metric("VELOCITY", f"{rotazione:.2f}x")
    e2.metric("VOLUME", f"{volume_giocato:.0f} €")
    e3.metric("TRADES", n_ops)
    e4.metric("AVG STAKE", f"{volume_giocato/n_ops:.0f} €" if n_ops>0 else "0")

    st.markdown("---")

    c1
