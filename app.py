import streamlit as st
import pandas as pd
import plotly.express as px
import os
import subprocess
import sys
import config

# --- 1. CONFIGURAZIONE PAGINA E STILE MODERNO ---
st.set_page_config(
    page_title="Sniper Betting Elite",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="collapsed" # Sidebar chiusa per focus totale
)

# --- CSS: UI/UX 2025 (Glassmorphism & Clean Layout) ---
st.markdown("""
    <style>
        /* Sfondo e Font */
        .stApp {
            background-color: #0e1117;
            font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        }
        
        /* Card Container (Effetto Vetro) */
        .css-1r6slb0, .stDataFrame, .stPlotlyChart {
            background-color: #1e2130;
            border-radius: 12px;
            padding: 15px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            border: 1px solid #2e3345;
        }

        /* Titoli e Metriche */
        h1, h2, h3 { color: #e0e0e0; font-weight: 600; }
        div[data-testid="stMetricValue"] {
            font-size: 2rem !important;
            color: #00CC96 !important; /* Verde Cyberpunk */
            font-weight: 700;
        }
        div[data-testid="stMetricLabel"] { color: #a0a0a0; }

        /* Pulsanti Personalizzati */
        .stButton button {
            border-radius: 8px;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        
        /* Separatori */
        hr { border-color: #2e3345; margin: 2rem 0; }
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
    """Esegue lo script scanner_calcio.py come processo esterno"""
    try:
        # Usa l'interprete Python corrente
        subprocess.run([sys.executable, "scanner_calcio.py"], check=True)
        return True
    except Exception as e:
        st.error(f"Errore scansione: {e}")
        return False

# --- CARICAMENTO DATI ---
df_storico = load_data(config.FILE_STORICO)
df_pending = load_data(config.FILE_PENDING)

# --- CALCOLI KPI LIVE ---
saldo_iniziale = config.BANKROLL_TOTALE
profitto_totale = 0.0
roi = 0.0
n_ops = 0

if not df_storico.empty:
    if 'Profitto_Reale' not in df_storico.columns: df_storico['Profitto_Reale'] = 0.0
    profitto_totale = df_storico['Profitto_Reale'].sum()
    volume_giocato = df_storico['Stake_Euro'].sum()
    if volume_giocato > 0: roi = (profitto_totale / volume_giocato) * 100
    n_ops = len(df_storico)

saldo_attuale = saldo_iniziale + profitto_totale

# ==============================================================================
# SEZIONE 1: DASHBOARD STRATEGICA (TOP)
# ==============================================================================
st.title("🦅 Sniper Elite Dashboard")

# 1.1 KPI CARDS
col1, col2, col3, col4 = st.columns(4)
col1.metric("💰 BANKROLL", f"{saldo_attuale:.2f} €", delta=f"{profitto_totale:.2f} €")
col2.metric("📈 ROI ATTUALE", f"{roi:.2f} %")
col3.metric("💸 PROFITTO NETTO", f"{profitto_totale:.2f} €")
col4.metric("🎯 TRADE CHIUSI", n_ops)

# 1.2 GRAFICI (Layout a 2 colonne)
if not df_storico.empty:
    c_chart1, c_chart2 = st.columns([2, 1])
    
    with c_chart1:
        # Grafico Linea Bankroll
        df_chart = df_storico.copy()
        df_chart['Bankroll_Trend'] = saldo_iniziale + df_chart['Profitto_Reale'].cumsum()
        df_chart['Trade_Num'] = range(1, len(df_chart) + 1)
        
        fig_line = px.line(df_chart, x='Trade_Num', y='Bankroll_Trend', title="<b>CRESCITA CAPITALE</b>")
        fig_line.update_traces(line_color='#00CC96', line_width=4)
        fig_line.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white', margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_line, use_container_width=True)
    
    with c_chart2:
        # Grafico Torta Sport
        if 'Sport' in df_chart.columns:
            fig_pie = px.pie(df_chart, names='Sport', values='Stake_Euro', donut=0.5, title="<b>ALLOCAZIONE ASSET</b>")
            fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color='white', margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_pie, use_container_width=True)

st.markdown("---")

# ==============================================================================
# SEZIONE 2: RADAR OPERATIVO (MIDDLE)
# ==============================================================================
col_radar_title, col_radar_btn = st.columns([3, 1])
with col_radar_title:
    st.subheader("📡 RADAR OPERATIVO")
    st.caption("Gestione Live: Modifica quota reale, spunta 'Abbinata' e conferma.")

with col_radar_btn:
    # --- TASTO SCANSIONE MANUALE ---
    if st.button("🔄 LANCIA SCANSIONE ORA", type="primary", use_container_width=True):
        with st.spinner("🛰️ Il drone sta scansionando i mercati..."):
            success = run_scanner()
            if success:
                st.success("Scansione completata!")
                st.rerun()

if not df_pending.empty:
    # Preparazione Colonne Editor
    if "Abbinata" not in df_pending.columns: df_pending.insert(0, "Abbinata", False)
    if "Quota_Reale_Presa" not in df_pending.columns: df_pending["Quota_Reale_Presa"] = df_pending["Quota_Ingresso"]

    # EDITOR DI TABELLA MODERNO
    edited_df = st.data_editor(
        df_pending,
        column_config={
            "Abbinata": st.column_config.CheckboxColumn("✅", width="small", help="Conferma esecuzione"),
            "Match": st.column_config.TextColumn("Evento", width="medium"),
            "Selezione": st.column_config.TextColumn("Bet", width="small"),
            "Valore_%": st.column_config.ProgressColumn("EV %", min_value=0, max_value=5, format="%.2f%%"),
            "Quota_Ingresso": st.column_config.NumberColumn("Q. Bot", format="%.2f", disabled=True),
            "Quota_Reale_Presa": st.column_config.NumberColumn("✏️ Q. Presa", format="%.2f", step=0.01),
            "Stake_Euro": st.column_config.NumberColumn("Stake", format="%d €"),
            "Target_Scalping": st.column_config.NumberColumn("Target", format="%.2f"),
        },
        column_order=["Abbinata", "Match", "Selezione", "Valore_%", "Quota_Ingresso", "Quota_Reale_Presa", "Stake_Euro", "Target_Scalping", "Torneo", "Orario_Match"],
        hide_index=True,
        use_container_width=True,
        num_rows="dynamic",
        key="radar_editor"
    )

    # BARRA AZIONI RADAR
    act_col1, act_col2 = st.columns([1, 4])
    
    with act_col1:
        if st.button("💾 CONFERMA E ARCHIVIA", type="primary", use_container_width=True):
            to_move = edited_df[edited_df["Abbinata"] == True].copy()
            if not to_move.empty:
                # Logica Spostamento
                to_move["Quota_Ingresso"] = to_move["Quota_Reale_Presa"]
                to_move["Esito_Finale"] = "APERTA"
                to_move["Profitto_Reale"] = 0.0
                
                # Merge e Save
                df_final = pd.concat([df_storico, to_move], ignore_index=True)
                cols_clean = [c for c in df_final.columns if c not in ["Abbinata", "Quota_Reale_Presa"]]
                save_data(df_final[cols_clean], config.FILE_STORICO)
                
                # Clean Pending
                remain = edited_df[edited_df["Abbinata"] == False]
                cols_pending = [c for c in remain.columns if c not in ["Abbinata", "Quota_Reale_Presa"]]
                save_data(remain[cols_pending], config.FILE_PENDING)
                
                st.toast(f"✅ {len(to_move)} Trade archiviati con successo!")
                st.rerun()
            else:
                st.warning("Nessuna riga selezionata.")

    with act_col2:
        if st.button("🗑️ RESET RADAR", type="secondary"):
            save_data(pd.DataFrame(columns=[c for c in df_pending.columns if c not in ["Abbinata", "Quota_Reale_Presa"]]), config.FILE_PENDING)
            st.rerun()

else:
    st.info("🦅 Nessun segnale attivo. Clicca 'LANCIA SCANSIONE ORA' per cercare occasioni.")

st.markdown("---")

# ==============================================================================
# SEZIONE 3: REGISTRO STORICO (BOTTOM)
# ==============================================================================
st.subheader("📜 REGISTRO OPERAZIONI")

if not df_storico.empty:
    st.dataframe(
        df_storico,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Stake_Euro": st.column_config.NumberColumn("Stake", format="%d €"),
            "Profitto_Reale": st.column_config.NumberColumn("Profitto", format="%.2f €"),
        }
    )
    
    # Export e Reset
    with st.expander("🛠️ Opzioni Registro"):
        xc1, xc2 = st.columns(2)
        with xc1:
            csv_data = df_storico.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Export CSV", csv_data, "sniper_log.csv", "text/csv")
        with xc2:
            if st.button("🔥 FORMATTA DATABASE"):
                save_data(pd.DataFrame(columns=df_storico.columns), config.FILE_STORICO)
                st.rerun()
else:
    st.caption("Il registro è vuoto.")
