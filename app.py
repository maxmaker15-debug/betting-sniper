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
    page_title="Sniper V60 Hybrid", 
    page_icon="🦅", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- CSS (Mantenuto Identico) ---
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
        # Mappatura colonne per sicurezza (V60 Output -> Display)
        # Il V60 scrive già header corretti, ma per sicurezza:
        rename_map = {
            "Quota_Betfair": "Q_Betfair", 
            "Quota_Target": "Q_Target", 
            "Quota_Reale_Pinna": "Q_Reale", 
            "Valore_%": "EV_%", 
            "Stake_Euro": "Stake_Ready"
        }
        df = df.rename(columns=rename_map)
        
        # Conversione FLOAT (Escludiamo Trend che è stringa)
        cols_float = ["Q_Betfair", "Q_Target", "Q_Reale", "EV_%", "Profitto"]
        for c in cols_float: 
            if c in df.columns: 
                df[c] = df[c].astype(str).apply(clean_num)
                df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0.0)
        
        # Conversione INT
        cols_int = ["Stake_Ready", "Stake_Limit"]
        for c in cols_int:
            if c in df.columns: 
                df[c] = df[c].astype(str).apply(clean_num)
                df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0).astype(int)
        
        # Defaults
        if "Trend" not in df.columns: df["Trend"] = "➖"
        if "Abbinata" not in df.columns: df["Abbinata"] = False
        if "Stato" not in df.columns: df["Stato"] = "WATCH"
        
        # LOGICA V60 PER IL RATING VISIVO
        def get_rating(row):
            s = row.get("Stato", "")
            if s == "READY": return "🟢 EXECUTE" # Value Bet piena
            if s == "QUASI": return "🟡 LIMIT"   # Quasi Value Bet
            if row.get("EV_%", 0) > 1.0: return "🟡 GOOD"
            return "⚪ WATCH"

        df["Rating"] = df.apply(get_rating, axis=1)

        return df
    except: return df

def load_data(f):
    if not os.path.exists(f): return pd.DataFrame()
    try: return enforce_schema(pd.read_csv(f))
    except: return pd.DataFrame()

def save_data(df, f): df.to_csv(f, index=False)

def run_scanner():
    # --- UPDATE V60: Nomi file aggiornati ---
    for s in ["scan_calcio.py", "scan_tennis.py"]:
        if os.path.exists(s): subprocess.run([sys.executable, s], check=False)

# --- CONFIGURAZIONE FILE ---
FILE_STORICO = getattr(config, 'FILE_STORICO', 'registro_operazioni.csv')
FILE_PENDING = getattr(config, 'FILE_PENDING', 'radar_pending.csv')

# --- DATI ---
df_hist = load_data(FILE_STORICO)
df_pend = load_data(FILE_PENDING)

bankroll_start = getattr(config, 'BANKROLL_TOTALE', 5000.0)
profit = df_hist['Profitto'].sum() if not df_hist.empty else 0.0
curr_bank = bankroll_start + profit

# --- SIDEBAR ---
with st.sidebar:
    st.markdown('<div class="header-logo">🦅 SNIPER<span class="highlight">V60</span></div>', unsafe_allow_html=True)
    if "nav" not in st.session_state: st.session_state.nav = "DASHBOARD"
    menu = st.radio("NAVIGAZIONE", ["DASHBOARD", "RADAR ZONE", "REGISTRO"], label_visibility="collapsed")
    st.markdown("---")
    c1, c2 = st.columns(2)
    c1.metric("BANKROLL", f"{curr_bank:.0f}€")
    c2.metric("PROFIT", f"{profit:.2f}€", delta_color="normal")
    st.markdown("---")
    if st.button("🔄 REBOOT SYSTEM"): st.rerun()

# --- PAGINA 1: DASHBOARD ---
if menu == "DASHBOARD":
    st.markdown("### 📊 DASHBOARD ANALYTICS")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("NET PROFIT", f"{profit:.2f} €")
    
    roi = 0.0
    win_rate = 0.0
    trades = 0
    if not df_hist.empty:
        vol = df_hist['Stake_Ready'].sum() if 'Stake_Ready' in df_hist.columns else 0
        trades = len(df_hist)
        if vol > 0: roi = (profit / vol) * 100
        wins = len(df_hist[df_hist['Profitto'] > 0])
        if trades > 0: win_rate = (wins / trades) * 100

    k2.metric("ROI %", f"{roi:.2f}%")
    k3.metric("WIN RATE", f"{win_rate:.0f}%")
    k4.metric("TRADES", trades)
    st.markdown("---")
    
    g1, g2 = st.columns([2, 1])
    with g1:
        st.markdown("#### 📈 PERFORMANCE TREND")
        if not df_hist.empty:
            df_chart = df_hist.copy()
            df_chart['Progressivo'] = bankroll_start + df_chart['Profitto'].cumsum()
            df_chart['Trade_ID'] = range(1, len(df_chart) + 1)
            fig = px.area(df_chart, x='Trade_ID', y='Progressivo', template="plotly_dark")
            fig.update_traces(line_color='#00E096', fill_color='rgba(0, 224, 150, 0.1)')
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(t=10, l=0, r=0, b=0), height=300)
            st.plotly_chart(fig, use_container_width=True)
        else: st.info("In attesa di dati storici...")
    with g2:
        st.markdown("#### 🍰 ASSET ALLOCATION")
        if not df_hist.empty and 'Sport' in df_hist.columns:
            fig_pie = px.pie(df_hist, names='Sport', values='Stake_Ready', donut=0.6, template="plotly_dark")
            fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', showlegend=False, margin=dict(t=0, l=0, r=0, b=0), height=300)
            st.plotly_chart(fig_pie, use_container_width=True)
        else: st.info("Nessun dato.")

# --- PAGINA 2: RADAR ---
elif menu == "RADAR ZONE":
    c1, c2 = st.columns([4, 1])
    c1.markdown("### 📡 ACTIVE TARGETS (V60 RULES)")
    if c2.button("SCAN NOW", type="primary"):
        with st.spinner("Scanning Markets..."):
            run_scanner()
            time.sleep(0.5)
            st.rerun()

    if not df_pend.empty and len(df_pend) > 0:
        # Colonne richieste
        req_cols = ["Abbinata", "Match", "Selezione", "Q_Betfair", "Rating", "Q_Target", "Trend", "EV_%", "Stake_Ready", "Stake_Limit"]
        
        # Assicuriamoci che esistano tutte
        for c in req_cols:
            if c not in df_pend.columns:
                if c == "Abbinata": df_pend[c] = False
                elif c == "Trend": df_pend[c] = "➖"
                elif c in ["Stake_Ready", "Stake_Limit"]: df_pend[c] = 0
                else: df_pend[c] = 0.0

        edited = st.data_editor(
            df_pend,
            column_config={
                "Abbinata": st.column_config.CheckboxColumn("✅", width="small"),
                "Match": st.column_config.TextColumn("EVENTO", width="medium"),
                "Selezione": st.column_config.TextColumn("BET", width="small"),
                "Q_Betfair": st.column_config.NumberColumn("Q.ATTUALE", format="%.2f", help="Quota disponibile ora"),
                "Rating": st.column_config.TextColumn("ACTION", width="small"),
                "Q_Target": st.column_config.NumberColumn("🎯 LIMIT", format="%.2f", help="Prezzo Target per Limit Order"),
                "Trend": st.column_config.TextColumn("TREND", width="small"),
                "EV_%": st.column_config.ProgressColumn("VALUE", min_value=-5, max_value=15, format="%.2f%%"),
                "Stake_Ready": st.column_config.NumberColumn("💶 STAKE", format="%d€"),
                "Stake_Limit": st.column_config.NumberColumn("✋ LIMIT STAKE", format="%d€"),
            },
            column_order=req_cols,
            hide_index=True,
            use_container_width=True,
            key=f"editor_{int(time.time())}"
        )
        
        act1, act2 = st.columns([1, 4])
        if act1.button("CONFIRM TRADE"):
            moved = edited[edited["Abbinata"]==True].copy()
            if not moved.empty:
                moved["Esito"] = "PENDING"
                moved["Profitto"] = 0.0
                save_data(pd.concat([df_hist, moved], ignore_index=True), FILE_STORICO)
                save_data(edited[edited["Abbinata"]==False], FILE_PENDING)
                st.rerun()
        if act2.button("WIPE RADAR"):
            save_data(pd.DataFrame(), FILE_PENDING)
            st.rerun()
    else:
        st.info("Nessun target trovato. Controlla che 'scan_calcio.py' e 'scan_tennis.py' siano nella cartella.")
        if st.button("FORCE RESET"):
            save_data(pd.DataFrame(), FILE_PENDING)
            st.rerun()

# --- PAGINA 3: REGISTRO ---
elif menu == "REGISTRO":
    st.markdown("### 📝 LOG OPERATIVO")
    if not df_hist.empty:
        st.dataframe(df_hist, use_container_width=True, hide_index=True)
        st.download_button("SCARICA CSV", df_hist.to_csv(index=False), "sniper_log.csv"
