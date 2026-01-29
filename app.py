import streamlit as st
import pandas as pd
import os
import requests
import plotly.express as px
import plotly.graph_objects as go
import config
import scanner_calcio
import scanner_tennis

# --- CONFIGURAZIONE PAGINA & TEMA ---
st.set_page_config(page_title="Sniper Finance Terminal", page_icon="🦅", layout="wide")

# --- CSS "FILA FINANCE" STYLE ---
st.markdown("""
<style>
    /* IMPORT FONT */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* SFONDO GENERALE */
    .stApp {
        background-color: #0b1120;
        background-image: radial-gradient(at 50% 0%, #172a46 0px, transparent 50%);
    }

    /* SIDEBAR */
    section[data-testid="stSidebar"] {
        background-color: #0f172a;
        border-right: 1px solid #1e293b;
    }

    /* CARDS (Riquadri KPI) */
    div[data-testid="stMetric"], div[data-testid="stDataFrame"] {
        background-color: #1e293b;
        padding: 20px;
        border-radius: 16px;
        border: 1px solid #334155;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
        transition: transform 0.2s;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 25px rgba(0, 201, 255, 0.15);
        border-color: #00c9ff;
    }

    /* TESTI KPI */
    div[data-testid="stMetricLabel"] {
        color: #94a3b8;
        font-size: 0.9rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    div[data-testid="stMetricValue"] {
        color: #f8fafc;
        font-weight: 800;
        text-shadow: 0 0 10px rgba(255,255,255,0.1);
    }

    /* BOTTONI STYLE */
    .stButton>button {
        width: 100%;
        height: 50px;
        border-radius: 12px;
        font-weight: 700;
        font-size: 16px;
        background: linear-gradient(135deg, #0ea5e9 0%, #10b981 100%);
        color: white;
        border: none;
        box-shadow: 0 4px 15px rgba(14, 165, 233, 0.4);
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(16, 185, 129, 0.6);
    }

    /* TITOLI */
    h1 {
        background: linear-gradient(90deg, #38bdf8, #818cf8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
    }
    h2, h3 {
        color: #e2e8f0;
    }

    /* MOBILE RESPONSIVE */
    @media (max-width: 640px) {
        .stButton>button { margin-bottom: 10px; }
        div[data-testid="stMetric"] { margin-bottom: 15px; }
    }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONI CARICAMENTO DATI ---
def load_data(f): 
    if os.path.isfile(f):
        try: return pd.read_csv(f)
        except: return pd.DataFrame()
    return pd.DataFrame()

def test_telegram_connection():
    TOKEN = "8145327630:AAHJC6vDjvGUyPT0pKw63fyW53hTl_F873U"
    CHAT_ID = "5562163433"
    try:
        requests.get(f"https://api.telegram.org/bot{TOKEN}/sendMessage", params={"chat_id": CHAT_ID, "text": "🦅 TERMINAL CHECK: Connessione stabile."})
        return True
    except: return False

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/7269/7269877.png", width=60)
    st.title("SNIPER PRO")
    st.markdown("<div style='font-size: 12px; color: #64748b; margin-top: -15px;'>V. 2.1 - FIX CHART</div>", unsafe_allow_html=True)
    st.markdown("---")
    
    selected_page = st.radio(
        "NAVIGAZIONE", 
        ["📊 Dashboard", "📡 Radar Mercati", "📝 Diario Ordini", "⚙️ Sistema"], 
        index=0
    )
    
    st.markdown("---")
    if st.button("🔔 PING TELEGRAM"):
        if test_telegram_connection(): st.success("ONLINE")
        else: st.error("OFFLINE")

# --- PAGINA 1: DASHBOARD ---
if selected_page == "📊 Dashboard":
    st.title("Panoramica Finanziaria")
    st.markdown("Benvenuto nella War Room, Comandante.")
    
    df = load_data(config.FILE_PENDING)
    
    # KPI INIT
    total_profit = 0.0
    active_trades = 0
    closed_trades = 0
    win_rate = 0.0
    invested_capital = 0.0
    
    if not df.empty:
        if 'Profitto_Reale' in df.columns:
            df['Profitto_Reale'] = pd.to_numeric(df['Profitto_Reale'], errors='coerce').fillna(0)
            total_profit = df['Profitto_Reale'].sum()
        
        if 'Stato_Trade' in df.columns:
            active_trades = df[df['Stato_Trade'] == 'APERTO'].shape[0]
            closed_trades_df = df[df['Stato_Trade'].str.contains("CHIUSO", na=False)]
            closed_trades = closed_trades_df.shape[0]
            
            wins = closed_trades_df[closed_trades_df['Profitto_Reale'] > 0].shape[0]
            if closed_trades > 0:
                win_rate = (wins / closed_trades) * 100
        
        if 'Stake_Euro' in df.columns and active_trades > 0:
            try:
                open_df = df[df['Stato_Trade'] == 'APERTO'].copy()
                open_df['Stake_Clean'] = open_df['Stake_Euro'].astype(str).str.extract(r'(\d+)').astype(float)
                invested_capital = open_df['Stake_Clean'].sum()
            except: pass

    # KPI CARDS
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("Profitto Netto", f"{total_profit:+.2f} €", delta="Totale")
    with col2: st.metric("Win Rate", f"{win_rate:.1f}%", delta="Performance")
    with col3: st.metric("Capitale Esposto", f"{invested_capital:.0f} €", delta=f"{active_trades} Aperti", delta_color="off")
    with col4: st.metric("Trade Chiusi", str(closed_trades), delta="Storico")

    st.markdown("<br>", unsafe_allow_html=True)

    # GRAFICI
    c_chart1, c_chart2 = st.columns([2, 1])
    
    with c_chart1:
        st.subheader("📈 Crescita Bankroll")
        if closed_trades > 0:
            df_closed = df[df['Stato_Trade'].str.contains("CHIUS
