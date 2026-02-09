import streamlit as st
import pandas as pd
import plotly.express as px
import os
import subprocess
import sys
import config
import time # Aggiunto per gestire i refresh sicuri

st.set_page_config(page_title="Sniper V42 Stability", page_icon="🦅", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <link href="https://cdn.jsdelivr.net/npm/remixicon@3.5.0/fonts/remixicon.css" rel="stylesheet">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        .stApp { background-color: #050505; font-family: 'Inter', sans-serif; color: #e0e0e0; }
        .block-container { padding: 2rem !important; }
        div[data-testid="stMetric"], div[data-testid="stDataFrame"] { background-color: #111; border: 1px solid #333; border-radius: 8px; }
        h1, h2, h3 { color: #fff; font-weight: 800; }
        .header-logo { font-size: 1.4rem; font-weight: 900; color: #fff; border-bottom: 1px solid #333; padding-bottom: 15px; margin-bottom: 20px; }
        .highlight { color: #00E096; }
        .stButton button { background-color: #222; color: #fff; border: 1px solid #444; font-weight: 600; }
        .stButton button:hover { border-color: #00E096; color: #00E096; }
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
        for c in cols_int:
            if c in df.columns: df[c] = df[c].astype(str).apply(clean_num).apply(pd.to_numeric, errors='coerce').fillna(0).astype(int)
        
        if "Trend" not in df.columns: df["Trend"] = "➖"
            
        return df
    except: return df

def load_data(f):
    if not os.path.exists(f): return pd.DataFrame()
    try: return enforce_schema(pd.read_csv(f))
    except: return pd.DataFrame()

def save_data(df, f): df.to_csv(f, index=False)

def run_scanner():
    for s in ["scanner_calcio.py", "scanner_tennis.py"]:
        if os.path.exists(s): subprocess.run([sys.executable, s], check=False)

# --- CARICAMENTO ---
df_hist = load_data(config.FILE_STORICO)
df_pend = load_data(config.FILE_PENDING)

bankroll = 5000.0
profit = df_hist['Profitto'].sum() if not df_hist.empty else 0.0
curr_bank = bankroll + profit

with st.sidebar:
    st.markdown('<div class="header-logo">🦅 SNIPER<span class="highlight">V42</span></div>', unsafe_allow_html=True)
    menu = st.radio("", ["DASHBOARD", "RADAR ZONE", "REGISTRO"], label_visibility="collapsed")
    st.markdown("---")
    c1, c2 = st.columns(2)
    c1.metric("BANKROLL", f"{curr_bank:.0f}€")
    c2.metric("PROFIT", f"{profit:.2f}€", delta_color="normal")
    if st.button("🔄 REBOOT"): st.rerun()

if menu == "DASHBOARD":
    st.markdown("### 📊 COMMANDER DASHBOARD")
    k1, k2, k3 = st.columns(3)
    k1.metric("NET PROFIT", f"{profit:.2f} €")
    if not df_hist.empty and 'Stake_Ready' in df_hist.columns:
        vol = df_hist['Stake_Ready'].sum()
        roi = (profit / vol * 100) if vol > 0 else 0
        k2.metric("ROI %", f"{roi:.2f}%")
        k3.metric("TRADES", len(df_hist))

elif menu == "RADAR ZONE":
    c1, c2 = st.columns([4, 1])
    c1.markdown("### 📡 MARKET SCANNER")
    if c2.button("SCAN NOW", type="primary"):
        with st.spinner("Scanning Market..."):
            run_scanner()
            time.sleep(0.5) # Pausa tattica per dare tempo al file system
            st.rerun()
            
    # --- SAFETY CHECK (Evita il crash "removeChild") ---
    if not df_pend.empty and len(df_pend) > 0:
        
        # Preparazione colonne sicura
        req_cols = ["Abbinata", "Match", "Selezione", "Q_Betfair", "Q_Target", "Trend", "EV_%", "Stake_Ready", "Stake_Limit", "Stato"]
        for c in req_cols: 
            if c not in df_pend.columns: 
                if c == "Abbinata": df_pend[c] = False
                elif c == "Trend": df_pend[c] = "➖"
                elif c in ["Stake_Ready", "Stake_Limit"]: df_pend[c] = 0
                else: df_pend[c] = 0.0

        # Disegna la tabella SOLO se ci sono dati
        edited = st.data_editor(
            df_pend,
            column_config={
                "Abbinata": st.column_config.CheckboxColumn("✅", width="small"),
                "Match": st.column_config.TextColumn("EVENTO", width="medium"),
                "Selezione": st.column_config.TextColumn("BET", width="small"),
                "Q_Betfair": st.column_config.NumberColumn("Q.BF", format="%.2f"),
                "Q_Target": st.column_config.NumberColumn("🎯 TARGET", format="%.2f"),
                "Trend": st.column_config.TextColumn("TREND", width="small"),
                "EV_%": st.column_config.ProgressColumn("EV", min_value=-5, max_value=15, format="%.2f%%"),
                "Stake_Ready": st.column_config.NumberColumn("🔥 BUY", format="%d€"),
                "Stake_Limit": st.column_config.NumberColumn("⏳ LIM", format="%d€"),
                "Stato": st.column_config.TextColumn("STATUS", width="small"),
            },
            column_order=req_cols,
            hide_index=True,
            use_container_width=True,
            # Key dinamica: forza il refresh se i dati cambiano, evitando conflitti DOM
            key=f"editor_{len(df_pend)}_{int(time.time())}" 
        )
        
        c_act1, c_act2 = st.columns([1, 4])
        if c_act1.button("CONFIRM TRADE"):
            moved = edited[edited["Abbinata"]==True].copy()
            if not moved.empty:
                moved["Esito"] = "PENDING"
                moved["Profitto"] = 0.0
                save_data(pd.concat([df_hist, moved], ignore_index=True), config.FILE_STORICO)
                save_data(edited[edited["Abbinata"]==False], config.FILE_PENDING)
                st.rerun()
        
        if c_act2.button("WIPE RADAR"):
            save_data(pd.DataFrame(), config.FILE_PENDING)
            st.rerun()
    
    else:
        # Se vuoto, mostra un messaggio statico INVECE della tabella editabile
        st.info("Nessun segnale attivo. Premi SCAN NOW per iniziare la caccia.")
        # Se avevi bisogno di un reset manuale anche a vuoto
        if st.button("FORCE RESET"):
            save_data(pd.DataFrame(), config.FILE_PENDING)
            st.rerun()

elif menu == "REGISTRO":
    st.markdown("### 📝 STORICO OPERAZIONI")
    if not df_hist.empty:
        st.dataframe(df_hist, use_container_width=True, hide_index=True)
        st.download_button("SCARICA CSV", df_hist.to_csv(index=False), "sniper_log.csv")
