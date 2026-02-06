import streamlit as st
import pandas as pd
import plotly.express as px
import os
import config

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="Sniper Betting V5",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS PERSONALIZZATO (LAYOUT COMPATTO) ---
st.markdown("""
    <style>
        .block-container { padding-top: 1rem !important; padding-bottom: 3rem !important; }
        .stDataFrame { border: 1px solid #444; border-radius: 5px; }
        div[data-testid="stMetricValue"] { font-size: 1.6rem !important; color: #4CAF50; }
        h3 { border-bottom: 2px solid #333; padding-bottom: 5px; margin-top: 20px;}
    </style>
""", unsafe_allow_html=True)

# --- FUNZIONI DATI ---
def load_data(filename):
    if not os.path.exists(filename): return pd.DataFrame()
    try: return pd.read_csv(filename)
    except: return pd.DataFrame()

def save_data(df, filename):
    df.to_csv(filename, index=False)

# --- CALCOLO STATISTICHE DASHBOARD ---
def calcola_kpi(df_storico):
    if df_storico.empty:
        return 0, 0, 0, pd.DataFrame()
    
    # Se mancano colonne chiave, le creiamo
    if 'Profitto_Reale' not in df_storico.columns: df_storico['Profitto_Reale'] = 0.0
    if 'Esito_Finale' not in df_storico.columns: df_storico['Esito_Finale'] = 'PENDING'

    # Calcoli
    volume_totale = df_storico['Stake_Euro'].sum()
    profitto_totale = df_storico['Profitto_Reale'].sum()
    roi = (profitto_totale / volume_totale * 100) if volume_totale > 0 else 0
    
    # Simulazione andamento bankroll
    df_storico['Bankroll_Trend'] = config.BANKROLL_TOTALE + df_storico['Profitto_Reale'].cumsum()
    
    return volume_totale, profitto_totale, roi, df_storico

# --- SIDEBAR ---
with st.sidebar:
    st.title("🦅 COMMAND V5")
    page = st.radio("Menu", ["📊 DASHBOARD & RADAR", "⚙️ SETTINGS"])
    st.markdown("---")
    if st.button("🔄 REFRESH DATI"): st.rerun()

# ==============================================================================
# PAGINA PRINCIPALE: DASHBOARD + RADAR
# ==============================================================================
if page == "📊 DASHBOARD & RADAR":
    
    # 1. CARICAMENTO DATI
    df_pending = load_data(config.FILE_PENDING)
    df_storico = load_data(config.FILE_STORICO)
    
    # 2. SEZIONE KPI (IN ALTO)
    vol, prof, roi, df_trend = calcola_kpi(df_storico)
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("💰 Bankroll Attuale", f"{config.BANKROLL_TOTALE + prof:.2f} €", delta=f"{prof:.2f} €")
    col2.metric("📊 Profitto Netto", f"{prof:.2f} €", delta_color="normal")
    col3.metric("📈 ROI %", f"{roi:.2f} %")
    col4.metric("🎯 Operazioni Chiuse", len(df_storico))

    # 3. GRAFICI (SE CI SONO DATI)
    if not df_trend.empty:
        with st.expander("📉 ANALISI GRAFICA (Clicca per espandere)", expanded=True):
            chart_col1, chart_col2 = st.columns([2, 1])
            with chart_col1:
                fig_line = px.line(df_trend, y="Bankroll_Trend", title="Andamento Bankroll")
                fig_line.update_traces(line_color='#00CC96', line_width=3)
                st.plotly_chart(fig_line, use_container_width=True)
            with chart_col2:
                # Distribuzione Stake o Sport (se presente)
                if 'Sport' in df_trend.columns:
                    fig_pie = px.pie(df_trend, names='Sport', values='Stake_Euro', title='Allocazione Stake')
                    st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("---")

    # 4. RADAR OPERATIVO (INTERATTIVO)
    st.subheader("📡 RADAR OPERATIVO (Pending)")
    
    if not df_pending.empty:
        # Preparazione colonne editor
        if "Abbinata" not in df_pending.columns: df_pending.insert(0, "Abbinata", False)
        if "Quota_Reale_Presa" not in df_pending.columns: df_pending["Quota_Reale_Presa"] = df_pending["Quota_Ingresso"]

        cols_view = [c for c in ["Abbinata", "Match", "Selezione", "Valore_%", "Quota_Ingresso", "Quota_Reale_Presa", "Stake_Euro", "Target_Scalping", "Torneo", "Orario_Match"] if c in df_pending.columns]

        # EDITOR
        edited_df = st.data_editor(
            df_pending[cols_view],
            column_config={
                "Abbinata": st.column_config.CheckboxColumn("✅ Presa?", width="small"),
                "Valore_%": st.column_config.ProgressColumn("EV %", format="%.2f", min_value=0, max_value=5),
                "Quota_Reale_Presa": st.column_config.NumberColumn("Quota Presa", step=0.01, format="%.2f"),
                "Stake_Euro": st.column_config.NumberColumn("Stake (€)", format="%d €"),
            },
            hide_index=True,
            use_container_width=True,
            num_rows="dynamic",
            key="radar_editor"
        )

        c1, c2 = st.columns([1, 4])
        with c1:
            # LOGICA CONFERMA E SPOSTAMENTO
            if st.button("💾 CONFERMA SELEZIONI", type="primary"):
                # Filtra le righe spuntate
                # Nota tecnica: Streamlit data_editor restituisce il dataframe modificato
                to_move = edited_df[edited_df["Abbinata"] == True].copy()
                
                if not to_move.empty:
                    # Prepara per storico
                    to_move["Quota_Ingresso"] = to_move["Quota_Reale_Presa"]
                    to_move["Esito_Finale"] = "APERTA" # Stato iniziale nello storico
                    to_move["Profitto_Reale"] = 0.0
                    
                    # Salva in storico
                    df_final_storico = pd.concat([df_storico, to_move], ignore_index=True)
                    # Assicuriamoci che tutte le colonne combacino, riempiendo NaN se serve
                    save_data(df_final_storico, config.FILE_STORICO)
                    
                    # Rimuovi dal pending
                    remain_pending = edited_df[edited_df["Abbinata"] == False]
                    # Rimuovi colonne temporanee
                    if "Abbinata" in remain_pending.columns: remain_pending = remain_pending.drop(columns=["Abbinata"])
                    if "Quota_Reale_Presa" in remain_pending.columns: remain_pending = remain_pending.drop(columns=["Quota_Reale_Presa"])
                    
                    save_data(remain_pending, config.FILE_PENDING)
                    
                    st.success("Operazioni registrate! Aggiorno...")
                    st.rerun()
                else:
                    st.toast("Nessuna riga selezionata.")
        
        with c2:
            if st.button("🗑️ PULISCI RADAR"):
                # Crea dataframe vuoto mantenendo le colonne originali
                cols_orig = [c for c in df_pending.columns if c not in ["Abbinata", "Quota_Reale_Presa"]]
                save_data(pd.DataFrame(columns=cols_orig), config.FILE_PENDING)
                st.warning("Radar pulito.")
                st.rerun()

    else:
        st.info("Nessun segnale attivo. Il drone è in volo... 🦅")

    st.markdown("---")
    
    # 5. REGISTRO VELOCE (Ultimi 5 movimenti)
    st.subheader("📜 ULTIME OPERAZIONI REGISTRATE")
    if not df_storico.empty:
        st.dataframe(df_storico.tail(5), use_container_width=True, hide_index=True)
    else:
        st.caption("Il registro è vuoto.")

# ==============================================================================
# PAGINA SETTINGS
# ==============================================================================
elif page == "⚙️ SETTINGS":
    st.title("⚙️ Parametri Attivi")
    st.json({
        "Bankroll": config.BANKROLL_TOTALE,
        "Stake Max": config.STAKE_MASSIMO,
        "Soglia Value": config.SOGLIA_VALUE_CALCIO,
        "Soglia Scalp": config.SOGLIA_SNIPER_CALCIO
    })
    
    st.markdown("### 🛠️ Gestione Database")
    if st.button("🔥 RESET TOTALE STORICO"):
        save_data(pd.DataFrame(columns=df_storico.columns), config.FILE_STORICO)
        st.error("Storico resettato.")
