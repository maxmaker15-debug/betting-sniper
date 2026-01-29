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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp {
        background-color: #0b1120;
        background-image: radial-gradient(at 50% 0%, #172a46 0px, transparent 50%);
    }
    section[data-testid="stSidebar"] {
        background-color: #0f172a;
        border-right: 1px solid #1e293b;
    }
    div[data-testid="stMetric"], div[data-testid="stDataFrame"] {
        background-color: #1e293b;
        padding: 20px;
        border-radius: 16px;
        border: 1px solid #334155;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
    }
    div[data-testid="stMetricLabel"] {
        color: #94a3b8;
        font-size: 0.9rem;
        font-weight: 600;
        text-transform: uppercase;
    }
    div[data-testid="stMetricValue"] {
        color: #f8fafc;
        font-weight: 800;
    }
    .stButton>button {
        width: 100%;
        height: 50px;
        border-radius: 12px;
        font-weight: 700;
        background: linear-gradient(135deg, #0ea5e9 0%, #10b981 100%);
        color: white;
        border: none;
        transition: all 0.3s ease;
    }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(16, 185, 129, 0.6); }
    h1 {
        background: linear-gradient(90deg, #38bdf8, #818cf8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
    }
    h2, h3 { color: #e2e8f0; }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONI ---
def load_data(f): 
    if os.path.isfile(f):
        try: return pd.read_csv(f)
        except: return pd.DataFrame()
    return pd.DataFrame()

def test_telegram_connection():
    TOKEN = "8145327630:AAHJC6vDjvGUyPT0pKw63fyW53hTl_F873U"
    CHAT_ID = "5562163433"
    try:
        requests.get(f"https://api.telegram.org/bot{TOKEN}/sendMessage", params={"chat_id": CHAT_ID, "text": "🦅 PING: Sistema Operativo."})
        return True
    except: return False

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/7269/7269877.png", width=60)
    st.title("SNIPER PRO")
    st.markdown("<div style='font-size: 12px; color: #64748b; margin-top: -15px;'>V. 2.2 - STABLE</div>", unsafe_allow_html=True)
    st.markdown("---")
    page = st.radio("MENU", ["📊 Dashboard", "📡 Radar Mercati", "📝 Diario Ordini", "⚙️ Sistema"])
    st.markdown("---")
    if st.button("🔔 PING TELEGRAM"):
        if test_telegram_connection(): st.success("OK")
        else: st.error("KO")

# --- DASHBOARD ---
if page == "📊 Dashboard":
    st.title("Panoramica Finanziaria")
    df = load_data(config.FILE_PENDING)
    
    # KPI Init
    profit = 0.0
    active = 0
    closed = 0
    win_rate = 0.0
    cap_exposed = 0.0
    
    if not df.empty:
        if 'Profitto_Reale' in df.columns:
            df['Profitto_Reale'] = pd.to_numeric(df['Profitto_Reale'], errors='coerce').fillna(0)
            profit = df['Profitto_Reale'].sum()
        if 'Stato_Trade' in df.columns:
            active = df[df['Stato_Trade'] == 'APERTO'].shape[0]
            closed_df = df[df['Stato_Trade'].str.contains("CHIUSO", na=False)]
            closed = closed_df.shape[0]
            wins = closed_df[closed_df['Profitto_Reale'] > 0].shape[0]
            if closed > 0: win_rate = (wins / closed) * 100
            
            if active > 0 and 'Stake_Euro' in df.columns:
                try:
                    op = df[df['Stato_Trade'] == 'APERTO'].copy()
                    op['Stake_Clean'] = op['Stake_Euro'].astype(str).str.extract(r'(\d+)').astype(float)
                    cap_exposed = op['Stake_Clean'].sum()
                except: pass

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Profitto Netto", f"{profit:+.2f} €", delta="Totale")
    c2.metric("Win Rate", f"{win_rate:.1f}%", delta="Performance")
    c3.metric("Capitale Esposto", f"{cap_exposed:.0f} €", delta=f"{active} attivi", delta_color="off")
    c4.metric("Chiusi", str(closed))

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Charts
    g1, g2 = st.columns([2, 1])
    with g1:
        st.subheader("📈 Trend Bankroll")
        if closed > 0:
            closed_df = df[df['Stato_Trade'].str.contains("CHIUSO", na=False)].copy()
            closed_df['N'] = range(1, len(closed_df)+1)
            closed_df['Cum'] = closed_df['Profitto_Reale'].cumsum()
            fig = px.area(closed_df, x='N', y='Cum', markers=True)
            fig.update_traces(line_color='#0ea5e9', fillcolor='rgba(14, 165, 233, 0.2)')
            fig.update_layout(paper_bgcolor='
