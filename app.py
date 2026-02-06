import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import subprocess
import sys
import config

# --- 1. CONFIGURAZIONE PAGINA & STILE ---
st.set_page_config(
    page_title="Sniper Betting Suite",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS "PRO TRADER" (Layout scuro, metriche grandi, tabelle pulite)
st.markdown("""
    <style>
        .stApp { background-color: #0e1117; }
        
        /* Contenitori Cards */
        .css-1r6slb0, .stDataFrame, .stPlotlyChart {
            background-color: #1a1c24;
            border: 1px solid #2d2f36;
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }
        
        /* Titoli e Testi */
        h1, h2, h3 { font-family: 'Segoe UI', sans-serif; color: #f0f0f0; }
        .stCaption { color: #888; font-size: 14px; }
        
        /* Metriche Dashboard */
        div[data-testid="stMetricValue"] {
            font-size: 2rem !important;
            color: #00CC96 !important; /* Verde Trading */
            font-weight: 700;
        }
        div[data-testid="stMetricLabel"] { color: #a0a0a0; font-size: 1rem; }
        
        /* Sidebar */
        section[data-testid="stSidebar"] { background-color: #111; }
        
        /* Pulsanti */
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
    """Esegue lo scanner come processo esterno"""
    try:
        subprocess.run([sys.executable, "scanner_calcio.py"], check=True)
        return True
    except Exception as e:
        st.error(f"Errore Scanner: {e}")
        return False

# --- CARICAMENTO DATI ---
df_storico = load_data(config.FILE_STORICO)
df_pending = load_data(config.FILE_PENDING)

# --- CALCOLI KPI AVANZATI (IL CUORE MATEMATICO) ---
saldo_iniziale = config.BANKROLL_TOTALE
profitto_totale = 0.0
volume_giocato = 0.0
roi = 0.0
roe = 0.0
rotazione_capitale = 0.0
n_ops = 0

if not df_storico.empty:
    # Normalizzazione colonne
    if 'Profitto_Reale' not in df_storico.columns: df_storico['Profitto_Reale'] = 0.0
    if 'Stake_Euro' not in df_storico.columns: df_storico['Stake_Euro'] = 0.0
    
    profitto_totale = df_storico['Profitto_Reale'].sum()
    volume_giocato = df_storico['Stake_Euro'].sum()
    n_ops = len(df_storico)
    
    # 1. ROI (Return on Investment) - Resa sul fatturato
    if volume_giocato > 0:
        roi = (profitto_totale / volume_giocato) * 100
        
    # 2. ROE (Return on Equity) - Resa sul capitale iniziale
    if saldo_iniziale > 0:
        roe = (profitto_totale / saldo_iniziale) * 100
        
    # 3. VELOCITÀ DI ROTAZIONE - Efficienza uso capitale
    if saldo_iniziale > 0:
        rotazione_capitale = volume_giocato / saldo_iniziale

saldo_attuale = saldo_iniziale + profitto_totale

# ==============================================================================
# SIDEBAR (NAVIGAZIONE)
# ==============================================================================
with st.sidebar:
    st.title("🦅 SNIPER SUITE")
    st.caption("AI Trading Assistant")
    st.markdown("---")
    
    menu = st.radio(
        "NAVIGAZIONE",
        ["📊 DASHBOARD ANALYTICS", "📡 RADAR OPERATIVO", "📜 REGISTRO STORICO"]
    )
    
    st.markdown("---")
    st.info(f"🏦 Bankroll: {config.BANKROLL_TOTALE}€")
    if st.button("🔄 REFRESH APP"):
        st.rerun()

# ==============================================================================
# PAGINA 1: DASHBOARD ANALYTICS (La versione completa)
# ==============================================================================
if menu == "📊 DASHBOARD ANALYTICS":
    st.title("📊 Financial Dashboard")
    st.markdown("Analisi avanzata delle performance e della gestione del rischio.")
    
    # RIGA 1: KPI FINANZIARI PRIMARI
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("💰 BANKROLL ATTUALE", f"{saldo_attuale:.2f} €", delta=f"{profitto_totale:.2f} €")
    kpi2.metric("💸 PROFITTO NETTO", f"{profitto_totale:.2f} €")
    kpi3.metric("📈 ROI (Yield)", f"{roi:.2f} %", help="Profitto / Volume Giocato")
    kpi4.metric("🚀 ROE (Growth)", f"{roe:.2f} %", help="Profitto / Capitale Iniziale")

    st.markdown("---")

    # RIGA 2: METRICHE DI EFFICIENZA (Rotazione)
    eff1, eff2, eff3, eff4 = st.columns(4)
    eff1.metric("🔄 ROTAZIONE CAPITALE", f"{rotazione_capitale:.2f}x", help="Quante volte hai girato l'intero bankroll")
    eff2.metric("📦 VOLUME MOSSO", f"{volume_giocato:.0f} €")
    eff3.metric("🎯 TRADE CHIUSI", n_ops)
    eff4.metric("⚖️ STAKE MEDIO", f"{volume_giocato/n_ops:.1f} €" if n_ops > 0 else "0 €")

    st.markdown("---")

    # RIGA 3: GRAFICI PROFESSIONALI
    if not df_storico.empty:
        g1, g2 = st.columns([2, 1])
        
        with g1:
            st.subheader("📈 Equity Curve (Trend Bankroll)")
            df_chart = df_storico.copy()
            df_chart['Progressivo'] = saldo_iniziale + df_chart['Profitto_Reale'].cumsum()
            df_chart['Trade_ID'] = range(1, len(df_chart) + 1)
            
            fig = px.area(df_chart, x='Trade_ID', y='Progressivo')
            fig.update_traces(line_color='#00CC96', fill_color='rgba(0, 204, 150, 0.1)')
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white', margin=dict(t=10, l=10, r=10, b=10))
            fig.add_hline(y=saldo_iniziale, line_dash="dot", line_color="white", annotation_text="Start")
            st.plotly_chart(fig, use_container_width=True)
            
        with g2:
            st.subheader("🍰 Asset Allocation")
            if 'Torneo' in df_chart.columns:
                fig_pie = px.pie(df_chart, names='Torneo', values='Stake_Euro', donut=0.6)
                fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color='white', showlegend=False, margin=dict(t=10, l=10, r=10, b=10))
                fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("Dati torneo non disponibili per il grafico.")
    else:
        st.info("⚠️ Nessuna operazione nello storico. Completa i primi trade nel Radar per attivare i grafici.")

# ==============================================================================
# PAGINA 2: RADAR OPERATIVO (Scansione & Gestione)
# ==============================================================================
elif menu == "📡 RADAR OPERATIVO":
    
    # Intestazione con Tasto Scansione
    col_head, col_btn = st.columns([3, 1])
    with col_head:
        st.title("📡 Radar Tattico")
        st.caption("Sala operativa: Scansiona, Modifica quote, Conferma giocate.")
    with col_btn:
        st.write("") # Spacer
        if st.button("🔄 AVVIA SCANSIONE MANUALE", type="primary"):
            with st.spinner("🛰️ Il drone sta scansionando i mercati..."):
                if run_scanner():
                    st.success("Scansione Completata!")
                    st.rerun()

    # Tabella Operativa
    if not df_pending.empty:
        # Prepariamo colonne per l'editor
        if "Abbinata" not in df_pending.columns: df_pending.insert(0, "Abbinata", False)
        if "Quota_Reale_Presa" not in df_pending.columns: df_pending["Quota_Reale_Presa"] = df_pending["Quota_Ingresso"]

        st.markdown("##### 📋 Segnali in Attesa")
        
        edited_df = st.data_editor(
            df_pending,
            column_config={
                "Abbinata": st.column_config.CheckboxColumn("✅ PRESA", width="small", help="Spunta se hai piazzato la bet"),
                "Match": st.column_config.TextColumn("Evento", width="medium"),
                "Valore_%": st.column_config.ProgressColumn("EV %", min_value=0, max_value=5, format="%.2f%%"),
                "Quota_Ingresso": st.column_config.NumberColumn("Quota Bot", format="%.2f", disabled=True),
                "Quota_Reale_Presa": st.column_config.NumberColumn("✏️ Quota Reale", format="%.2f", step=0.01, help="Modifica qui se la quota presa è diversa"),
                "Stake_Euro": st.column_config.NumberColumn("Stake", format="%d €"),
                "Target_Scalping": st.column_config.NumberColumn("Target Uscita", format="%.2f"),
            },
            column_order=["Abbinata", "Match", "Selezione", "Valore_%", "Quota_Ingresso", "Quota_Reale_Presa", "Stake_Euro", "Target_Scalping", "Torneo", "Orario_Match"],
            hide_index=True,
            use_container_width=True,
            num_rows="dynamic",
            key="radar_editor_main"
        )

        st.markdown("---")
        
        # Pulsantiera Azioni
        c1, c2 = st.columns([1, 4])
        with c1:
            if st.button("💾 CONFERMA SELEZIONATE", type="primary", use_container_width=True):
                # Filtra le righe spuntate
                to_move = edited_df[edited_df["Abbinata"] == True].copy()
                
                if not to_move.empty:
                    # Prepara per storico
                    to_move["Quota_Ingresso"] = to_move["Quota_Reale_Presa"]
                    to_move["Esito_Finale"] = "APERTA"
                    to_move["Profitto_Reale"] = 0.0
                    
                    # Unione sicura allo storico
                    df_final = pd.concat([df_storico, to_move], ignore_index=True)
                    # Pulizia colonne tecniche prima di salvare nello storico
                    cols_to_save = [c for c in df_final.columns if c not in ["Abbinata", "Quota_Reale_Presa"]]
                    save_data(df_final[cols_to_save], config.FILE_STORICO)
                    
                    # Rimuovi dal pending
                    remain = edited_df[edited_df["Abbinata"] == False]
                    cols_pending = [c for c in remain.columns if c not in ["Abbinata", "Quota_Reale_Presa"]]
                    save_data(remain[cols_pending], config.FILE_PENDING)
                    
                    st.success(f"✅ {len(to_move)} Operazioni registrate nel Registro!")
                    st.rerun()
                else:
                    st.warning("⚠️ Nessuna riga selezionata.")
        
        with c2:
            if st.button("🗑️ PULISCI RADAR (RESET)", type="secondary"):
                # Resetta il file pending mantenendo le colonne
                cols_reset = [c for c in df_pending.columns if c not in ["Abbinata", "Quota_Reale_Presa"]]
                save_data(pd.DataFrame(columns=cols_reset), config.FILE_PENDING)
                st.rerun()

    else:
        st.info("🦅 Nessun segnale attivo. Premi 'AVVIA SCANSIONE MANUALE' per cercare occasioni.")

# ==============================================================================
# PAGINA 3: REGISTRO STORICO (Consultazione)
# ==============================================================================
elif menu == "📜 REGISTRO STORICO":
    st.title("📜 Registro Operazioni")
    st.caption("Archivio storico di tutte le operazioni confermate.")

    if not df_storico.empty:
        # Visualizzazione Tabellare
        st.dataframe(
            df_storico,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Stake_Euro": st.column_config.NumberColumn("Stake", format="%d €"),
                "Profitto_Reale": st.column_config.NumberColumn("Profitto", format="%.2f €"),
                "Valore_%": st.column_config.NumberColumn("EV Orig.", format="%.2f%%"),
            }
        )
        
        st.markdown("---")
        
        # Strumenti Export
        col_exp1, col_exp2 = st.columns(2)
        with col_exp1:
            csv_data = df_storico.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 SCARICA CSV (Excel)",
                data=csv_data,
                file_name="sniper_registro.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col_exp2:
            with st.expander("⚠️ ZONA PERICOLO"):
                if st.button("🔥 CANCELLA TUTTO LO STORICO", type="primary", use_container_width=True):
                    save_data(pd.DataFrame(columns=df_storico.columns), config.FILE_STORICO)
                    st.error("Database cancellato.")
                    st.rerun()
    else:
        st.info("Il Registro è ancora vuoto. Conferma le prime operazioni dal Radar.")
