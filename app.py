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
    
    # 1. ROI (Return on Investment): Quanto rendono le tue scommesse
    if volume_giocato > 0:
        roi = (profitto_totale / volume_giocato) * 100
        
    # 2. ROE (Return on Equity): Quanto è cresciuto il Bankroll Iniziale
    if saldo_iniziale > 0:
        roe = (profitto_totale / saldo_iniziale) * 100
        
    # 3. VELOCITÀ DI ROTAZIONE: Quante volte hai "girato" il capitale
    if saldo_iniziale > 0:
        rotazione_capitale = volume_giocato / saldo_iniziale

saldo_attuale = saldo_iniziale + profitto_totale

# ==============================================================================
# SEZIONE 1: DASHBOARD ANALITICA (Tornata come la volevi)
# ==============================================================================
st.title("🦅 Sniper Financial Dashboard")

# RIGA 1: I 4 PILASTRI
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("💰 BANKROLL", f"{saldo_attuale:.2f} €", delta=f"{profitto_totale:.2f} €")
kpi2.metric("💸 PROFITTO NETTO", f"{profitto_totale:.2f} €")
kpi3.metric("📊 ROI (Yield)", f"{roi:.2f} %", help="Rendimento sul volume giocato")
kpi4.metric("🚀 ROE (Growth)", f"{roe:.2f} %", help="Crescita del capitale iniziale")

# RIGA 2: METRICHE DI EFFICIENZA
stat1, stat2, stat3, stat4 = st.columns(4)
stat1.metric("🔄 ROTAZIONE CAPITALE", f"{rotazione_capitale:.2f}x", help="Quante volte hai reinvestito il bankroll")
stat2.metric("📦 VOLUME TOTALE", f"{volume_giocato:.0f} €")
stat3.metric("🎯 TRADE CHIUSI", n_ops)
stat4.metric("⚖️ STAKE MEDIO", f"{volume_giocato/n_ops:.1f} €" if n_ops > 0 else "0 €")

st.markdown("---")

# RIGA 3: I GRAFICI (Bankroll Trend + Asset Allocation)
if not df_storico.empty:
    chart_row1, chart_row2 = st.columns([2, 1])
    
    with chart_row1:
        st.subheader("📈 Bankroll Trend")
        # Creiamo un trend temporale simulato
        df_chart = df_storico.copy()
        df_chart['Progressivo'] = saldo_iniziale + df_chart['Profitto_Reale'].cumsum()
        df_chart['Trade_ID'] = range(1, len(df_chart) + 1)
        
        # Grafico ad Area/Linea
        fig_trend = px.area(df_chart, x='Trade_ID', y='Progressivo', title=None)
        fig_trend.update_traces(line_color='#00CC96', fill_color='rgba(0, 204, 150, 0.1)')
        fig_trend.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white', margin=dict(l=0, r=0, t=0, b=0))
        # Linea del bankroll iniziale
        fig_trend.add_hline(y=saldo_iniziale, line_dash="dot", line_color="white", annotation_text="Start")
        st.plotly_chart(fig_trend, use_container_width=True)
    
    with chart_row2:
        st.subheader("🍰 Asset Allocation")
        # Grafico a Torta (Per Sport o Campionato)
        if 'Torneo' in df_chart.columns:
            fig_pie = px.pie(df_chart, names='Torneo
