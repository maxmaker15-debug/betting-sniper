Comandante, ricevuto. 🦅

L'errore è chiaro: KeyError: 'Quota_Betfair'.

Cosa è successo? Il tuo file pending_trades.csv contiene ancora i dati della Vecchia Versione (dove la colonna si chiamava Quota_Ingresso). Il Nuovo Codice cerca la colonna Quota_Betfair, non la trova nel file vecchio e l'applicazione si schianta prima ancora di poterti mostrare il tasto per cancellare i dati. È un cane che si morde la coda.

SOLUZIONE: AUTO-RIPARAZIONE (V23) Ho inserito un "Antivirus" nel codice app.py. Appena l'app si avvia, controlla se il file CSV ha le colonne giuste. Se trova colonne vecchie (della versione scalping), cancella automaticamente il file corrotto e ne crea uno nuovo pulito, senza crashare.

Ecco il codice V23 - Self Healing. Copia e sostituisci tutto app.py.

📂 FILE: app.py (V23 - Auto-Fix Database)
Python
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
        
        .stApp { background-color: #080808; font-family: 'Inter', sans-serif; }
        .block-container { padding-top: 3.5rem !important; padding-bottom: 3rem !important; padding-left: 2rem !important; padding-right: 2rem !important; }
        
        div[data-testid="stMetric"], div[data-testid="stDataFrame"], div[data-testid="stPlotlyChart"] {
            background-color: #121212; border: 1px solid #333; border-radius: 6px; padding: 12px 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.4);
        }
        div[data-testid="stMetric"]:hover { border-color: #555; }
        
        h1, h2, h3 { color: #fff; font-weight: 700; margin-bottom: 10px; }
        div[data-testid="stMetricValue"] { font-size: 1.8rem !important; color: #00E096 !important; font-weight: 700; }
        div[data-testid="stMetricLabel"] { color: #777; font-size: 0.8rem; text-transform: uppercase; font-weight: 500; }
        section[data-testid="stSidebar"] { background-color: #0b0b0b; border-right: 1px solid #222; }
        
        .stButton button { background-color: #1a1a1a; color: #ddd; border: 1px solid #333; border-radius: 4px; width: 100%; text-transform: uppercase; font-weight: 600; }
        .stButton button:hover { border-color: #00E096; color: #00E096; }
        
        .header-logo { font-size: 1.2rem; font-weight: 800; color: #fff; border-bottom: 1px solid #222; padding-bottom: 10px; margin-bottom: 15px; }
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
    if os.path.exists("scanner_calcio.py"):
        try:
            subprocess.run([sys.executable, "scanner_calcio.py"], check=True)
            log_scan.append("Calcio: OK")
        except: log_scan.append("Calcio: Error")
    if os.path.exists("scanner_tennis.py"):
        try:
            subprocess.run([sys.executable, "scanner_tennis.py"], check=True)
            log_scan.append("Tennis: OK")
        except: log_scan.append("Tennis: Error")
    return log_scan

# --- CARICAMENTO E AUTO-RIPARAZIONE ---
df_storico = load_data(config.FILE_STORICO)
df_pending = load_data(config.FILE_PENDING)

# PROTOCOLLO DI EMERGENZA: Se il file Pending ha colonne vecchie, RESETTALO SUBITO.
if not df_pending.empty and "Quota_Betfair" not in df_pending.columns:
    st.toast("⚠️ Database obsoleto rilevato. Esecuzione Auto-Fix...", icon="🛠️")
    df_pending = pd.DataFrame() # Svuota in memoria
    save_data(df_pending, config.FILE_PENDING) # Svuota su disco
    st.rerun() # Riavvia l'app pulita

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

    c1, c2 = st.columns([2, 1])
    with c1:
        st.markdown('<h3><i class="ri-line-chart-line"></i> TREND</h3>', unsafe_allow_html=True)
        if not df_storico.empty:
            df_chart = df_storico.copy()
            df_chart['Progressivo'] = saldo_iniziale + df_chart['Profitto_Reale'].cumsum()
            df_chart['Trade'] = range(1, len(df_chart) + 1)
            fig = px.area(df_chart, x='Trade', y='Progressivo')
            fig.update_traces(line_color='#00E096', fill_color='rgba(0, 224, 150, 0.05)')
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white', margin=dict(t=10, l=0, r=0, b=0), height=300, xaxis=dict(showgrid=False), yaxis=dict(gridcolor='#222'))
            fig.add_hline(y=saldo_iniziale, line_dash="dot", line_color="#555")
            st.plotly_chart(fig, use_container_width=True)
        else: st.caption("Waiting for data...")

    with c2:
        st.markdown('<h3><i class="ri-pie-chart-2-line"></i> ASSETS</h3>', unsafe_allow_html=True)
        if not df_storico.empty and 'Sport' in df_storico.columns:
            fig_pie = px.pie(df_storico, names='Sport', values='Stake_Euro', donut=0.7)
            fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color='white', showlegend=False, margin=dict(t=10, l=0, r=0, b=0), height=300)
            st.plotly_chart(fig_pie, use_container_width=True)
        else: st.caption("Waiting for data...")

# ==============================================================================
# PAGINA 2: RADAR
# ==============================================================================
elif menu == "◎ RADAR":
    h_col, b_col = st.columns([5, 1.5])
    with h_col: st.markdown('<h3><i class="ri-radar-line"></i> MARKET SCANNER (WIDE)</h3>', unsafe_allow_html=True)
    with b_col: 
        st.write("")
        if st.button("SCAN NOW", use_container_width=True):
            with st.spinner("Analyzing Market Value..."):
                run_scanner()
                st.rerun()

    if not df_pending.empty:
        # Preparazione colonne per Value Betting
        if "Abbinata" not in df_pending.columns: df_pending.insert(0, "Abbinata", False)
        # QUI ERA L'ERRORE: Ora è protetto perché se manca la colonna, il codice sopra (riga 67) ha già resettato tutto.
        if "Quota_Reale_Presa" not in df_pending.columns: df_pending["Quota_Reale_Presa"] = df_pending.get("Quota_Betfair", 0.0)

        # TABELLA VALUE BET
        edited_df = st.data_editor(
            df_pending,
            column_config={
                "Abbinata": st.column_config.CheckboxColumn("✅", width="small"),
                "Match": st.column_config.TextColumn("EVENTO", width="medium"),
                "Selezione": st.column_config.TextColumn("BET", width="small"),
                "Quota_Betfair": st.column_config.NumberColumn("Q.BF (Buy)", format="%.2f", disabled=True),
                "Quota_Reale_Pinna": st.column_config.NumberColumn("REAL (Pinna)", format="%.2f", disabled=True),
                "Valore_%": st.column_config.ProgressColumn("EV %", min_value=-5, max_value=10, format="%.2f%%"),
                "Stake_Euro": st.column_config.NumberColumn("STAKE", format="%d €"),
                "Quota_Reale_Presa": st.column_config.NumberColumn("✏️ Q.PRESA", format="%.2f", step=0.01),
                "Stato_Trade": st.column_config.TextColumn("STATUS", width="small"),
            },
            column_order=["Abbinata", "Match", "Selezione", "Quota_Betfair", "Quota_Reale_Pinna", "Valore_%", "Stake_Euro", "Quota_Reale_Presa", "Stato_Trade"],
            hide_index=True,
            use_container_width=True
        )

        c1, c2 = st.columns([1, 5])
        with c1:
            if st.button("CONFIRM TRADE"):
                to_move = edited_df[edited_df["Abbinata"] == True].copy()
                if not to_move.empty:
                    to_move["Quota_Ingresso"] = to_move["Quota_Reale_Presa"]
                    to_move["Esito_Finale"] = "APERTA"
                    to_move["Profitto_Reale"] = 0.0
                    
                    df_final = pd.concat([df_storico, to_move], ignore_index=True)
                    cols_s = [c for c in df_final.columns if c not in ["Abbinata", "Quota_Reale_Presa"]]
                    save_data(df_final[cols_s], config.FILE_STORICO)
                    
                    remain = edited_df[edited_df["Abbinata"] == False]
                    cols_p = [c for c in remain.columns if c not in ["Abbinata", "Quota_Reale_Presa"]]
                    save_data(remain[cols_p], config.FILE_PENDING)
                    st.rerun()
        with c2:
            if st.button("CLEAR"):
                cols_c = [c for c in df_pending.columns if c not in ["Abbinata", "Quota_Reale_Presa"]]
                save_data(pd.DataFrame(columns=cols_c), config.FILE_PENDING)
                st.rerun()
    else:
        st.info("No signals found. Press SCAN NOW.")

# ==============================================================================
# PAGINA 3: REGISTRO
# ==============================================================================
elif menu == "▤ REGISTRO":
    st.markdown('<h3><i class="ri-file-list-2-line"></i> EXECUTION LOG</h3>', unsafe_allow_html=True)
    if not df_storico.empty:
        st.dataframe(
            df_storico, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "Stake_Euro": st.column_config.NumberColumn("Stake", format="%d €"),
                "Profitto_Reale": st.column_config.NumberColumn("Profitto", format="%.2f €"),
                "Valore_%": st.column_config.NumberColumn("EV %", format="%.2f%%"),
            }
        )
        csv = df_storico.to_csv(index=False).encode('utf-8')
        st.download_button("DOWNLOAD CSV", csv, "sniper_log.csv", "text/csv")
        if st.button("WIPE DATA"):
            save_data(pd.DataFrame(columns=df_storico.columns), config.FILE_STORICO)
            st.rerun()
    else:
        st.caption("Empty log.")
