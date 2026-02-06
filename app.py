import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import subprocess
import sys
import config

# --- 1. CONFIGURAZIONE PAGINA & STILE 2026 ---
st.set_page_config(
    page_title="Sniper Betting Suite",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# INIEZIONE LIBRERIA ICONE + CSS AVANZATO
st.markdown("""
    <link href="https://cdn.jsdelivr.net/npm/remixicon@3.5.0/fonts/remixicon.css" rel="stylesheet">
    
    <style>
        /* FONTS & BACKGROUND */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        
        .stApp {
            background-color: #050505; /* Nero Profondo */
            font-family: 'Inter', sans-serif;
        }

        /* CARD SEMI-TRASPARENTI (Glassmorphism 2.0) */
        .css-1r6slb0, .stDataFrame, .stPlotlyChart {
            background: rgba(20, 20, 20, 0.7);
            backdrop-filter: blur(10px);
            border: 1px solid #333;
            border-radius: 12px;
            padding: 20px;
        }

        /* TITOLI CON ICONE */
        h1, h2, h3 { 
            color: #ffffff; 
            font-weight: 800; 
            letter-spacing: -1px;
        }
        
        /* ICONE REMIX */
        i { vertical-align: middle; margin-right: 8px; }

        /* METRICHE (NUMERI GIGANTI E PULITI) */
        div[data-testid="stMetricValue"] {
            font-size: 2.4rem !important;
            color: #00E096 !important; /* Verde Neon Moderno */
            font-weight: 800;
            text-shadow: 0 0 20px rgba(0, 224, 150, 0.3);
        }
        div[data-testid="stMetricLabel"] {
            color: #888;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        /* SIDEBAR */
        section[data-testid="stSidebar"] { background-color: #0a0a0a; border-right: 1px solid #222; }
        
        /* PULSANTI FUTURISTICI */
        .stButton button {
            background-color: #222;
            color: white;
            border: 1px solid #444;
            border-radius: 8px;
            text-transform: uppercase;
            font-size: 0.8rem;
            letter-spacing: 1px;
            transition: all 0.3s ease;
        }
        .stButton button:hover {
            border-color: #00E096;
            color: #00E096;
            box-shadow: 0 0 15px rgba(0, 224, 150, 0.2);
        }
        
        /* HEADER LOGO */
        .header-logo {
            font-size: 1.5rem;
            font-weight: 900;
            color: #fff;
            border-bottom: 1px solid #333;
            padding-bottom: 15px;
            margin-bottom: 20px;
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
    # 1. SCANSIONE CALCIO
    if os.path.exists("scanner_calcio.py"):
        try:
            subprocess.run([sys.executable, "scanner_calcio.py"], check=True)
            log_scan.append("Calcio: OK")
        except Exception as e: log_scan.append(f"Calcio: Error")
    
    # 2. SCANSIONE TENNIS
    if os.path.exists("scanner_tennis.py"):
        try:
            subprocess.run([sys.executable, "scanner_tennis.py"], check=True)
            log_scan.append("Tennis: OK")
        except Exception as e: log_scan.append(f"Tennis: Error")
            
    return log_scan

# --- CARICAMENTO DATI ---
df_storico = load_data(config.FILE_STORICO)
df_pending = load_data(config.FILE_PENDING)

# --- KPI ENGINE ---
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
    
    if volume_giocato > 0: roi = (profitto_totale / volume_giocato) * 100
    if saldo_iniziale > 0: roe = (profitto_totale / saldo_iniziale) * 100
    if saldo_iniziale > 0: rotazione_capitale = volume_giocato / saldo_iniziale

saldo_attuale = saldo_iniziale + profitto_totale

# ==============================================================================
# SIDEBAR NAVIGATION
# ==============================================================================
with st.sidebar:
    # Logo HTML personalizzato
    st.markdown('<div class="header-logo"><i class="ri-focus-3-line highlight"></i> SNIPER<span class="highlight">ELITE</span></div>', unsafe_allow_html=True)
    
    # Menu con simboli geometrici minimali (no emoji cartoon)
    menu = st.radio(
        "SISTEMA DI NAVIGAZIONE",
        ["◈ DASHBOARD", "◎ RADAR OPERATIVO", "▤ REGISTRO"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.markdown(f"**CAPITALE:** <span style='color:white'>{config.BANKROLL_TOTALE}€</span>", unsafe_allow_html=True)
    st.markdown(f"**LIMIT:** <span style='color:white'>{config.STAKE_MASSIMO}€</span>", unsafe_allow_html=True)
    st.markdown("---")
    if st.button("REBOOT SYSTEM"): st.rerun()

# ==============================================================================
# PAGINA 1: DASHBOARD
# ==============================================================================
if menu == "◈ DASHBOARD":
    st.markdown('<h1><i class="ri-dashboard-line"></i> FINANCIAL HUB</h1>', unsafe_allow_html=True)
    st.caption("Real-time Performance Analytics")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # RIGA 1: KPI PRINCIPALI
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("CURRENT BANKROLL", f"{saldo_attuale:.2f} €", delta=f"{profitto_totale:.2f} €")
    k2.metric("NET PROFIT", f"{profitto_totale:.2f} €")
    k3.metric("ROI (YIELD)", f"{roi:.2f} %")
    k4.metric("ROE (GROWTH)", f"{roe:.2f} %")

    st.markdown("<br>", unsafe_allow_html=True)

    # RIGA 2: EFFICIENZA
    e1, e2, e3, e4 = st.columns(4)
    e1.metric("VELOCITY", f"{rotazione_capitale:.2f}x")
    e2.metric("TOTAL VOLUME", f"{volume_giocato:.0f} €")
    e3.metric("CLOSED TRADES", n_ops)
    e4.metric("AVG STAKE", f"{volume_giocato/n_ops:.1f} €" if n_ops > 0 else "0 €")

    st.markdown("---")

    # GRAFICI
    if not df_storico.empty:
        c1, c2 = st.columns([2, 1])
        with c1:
            st.markdown('<h3><i class="ri-line-chart-line"></i> EQUITY CURVE</h3>', unsafe_allow_html=True)
            df_chart = df_storico.copy()
            df_chart['Progressivo'] = saldo_iniziale + df_chart['Profitto_Reale'].cumsum()
            df_chart['Trade'] = range(1, len(df_chart) + 1)
            
            fig = px.area(df_chart, x='Trade', y='Progressivo')
            fig.update_traces(line_color='#00E096', fill_color='rgba(0, 224, 150, 0.1)')
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white', margin=dict(t=20, l=0, r=0, b=0))
            fig.add_hline(y=saldo_iniziale, line_dash="dot", line_color="#444")
            st.plotly_chart(fig, use_container_width=True)
        
        with c2:
            st.markdown('<h3><i class="ri-pie-chart-line"></i> ASSETS</h3>', unsafe_allow_html=True)
            if 'Sport' in df_chart.columns:
                fig_pie = px.pie(df_chart, names='Sport', values='Stake_Euro', donut=0.6)
                fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color='white', showlegend=False, margin=dict(t=20, l=0, r=0, b=0))
                fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_pie, use_container_width=True)

# ==============================================================================
# PAGINA 2: RADAR
# ==============================================================================
elif menu == "◎ RADAR OPERATIVO":
    
    # Header con Bottone Scansione Integrato
    c_head, c_btn = st.columns([3, 1])
    with c_head:
        st.markdown('<h1><i class="ri-radar-line"></i> LIVE RADAR</h1>', unsafe_allow_html=True)
    with c_btn:
        st.write("")
        if st.button("SCAN MARKETS"):
            with st.spinner("SCANNING..."):
                logs = run_scanner()
                st.success("SCAN COMPLETE")
                st.rerun()

    if not df_pending.empty:
        if "Abbinata" not in df_pending.columns: df_pending.insert(0, "Abbinata", False)
        if "Quota_Reale_Presa" not in df_pending.columns: df_pending["Quota_Reale_Presa"] = df_pending["Quota_Ingresso"]

        edited_df = st.data_editor(
            df_pending,
            column_config={
                "Abbinata": st.column_config.CheckboxColumn("CONFIRM", width="small"),
                "Match": st.column_config.TextColumn("EVENT", width="medium"),
                "Valore_%": st.column_config.ProgressColumn("EV", min_value=0, max_value=5, format="%.2f%%"),
                "Quota_Ingresso": st.column_config.NumberColumn("Q.BOT", format="%.2f", disabled=True),
                "Quota_Reale_Presa": st.column_config.NumberColumn("Q.REAL", format="%.2f", step=0.01),
                "Stake_Euro": st.column_config.NumberColumn("STAKE", format="%d €"),
                "Target_Scalping": st.column_config.NumberColumn("EXIT", format="%.2f"),
            },
            column_order=["Abbinata", "Sport", "Match", "Selezione", "Valore_%", "Quota_Ingresso", "Quota_Reale_Presa", "Stake_Euro", "Target_Scalping"],
            hide_index=True,
            use_container_width=True,
            num_rows="dynamic"
        )

        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("EXECUTE TRADE"):
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
        with col2:
            if st.button("CLEAR RADAR"):
                cols_c = [c for c in df_pending.columns if c not in ["Abbinata", "Quota_Reale_Presa"]]
                save_data(pd.DataFrame(columns=cols_c), config.FILE_PENDING)
                st.rerun()
    else:
        st.info("NO ACTIVE SIGNALS. WAITING FOR SCAN...")

# ==============================================================================
# PAGINA 3: REGISTRO
# ==============================================================================
elif menu == "▤ REGISTRO":
    st.markdown('<h1><i class="ri-file-list-3-line"></i> TRADE LOG</h1>', unsafe_allow_html=True)
    if not df_storico.empty:
        st.dataframe(df_storico, use_container_width=True, hide_index=True)
        csv = df_storico.to_csv(index=False).encode('utf-8')
        st.download_button("DOWNLOAD CSV", csv, "sniper_log.csv", "text/csv")
        if st.button("FACTORY RESET (DATA WIPE)"):
            save_data(pd.DataFrame(columns=df_storico.columns), config.FILE_STORICO)
            st.rerun()
    else:
        st.info("LOG IS EMPTY.")
