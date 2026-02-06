import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import config

# --- CONFIGURAZIONE PAGINA (FIX GRAFICO E TITOLI) ---
st.set_page_config(
    page_title="Sniper Betting V6",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS PERSONALIZZATO (STILE PRO) ---
st.markdown("""
    <style>
        /* Fix Spaziatura Titoli */
        .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 2rem !important;
        }
        /* Stile Tabelle */
        .stDataFrame {
            border: 1px solid #333;
            border-radius: 5px;
        }
        /* Metriche Dashboard */
        div[data-testid="stMetricValue"] {
            font-size: 2.2rem !important;
            font-weight: 700;
            color: #00CC96; /* Verde Neon */
        }
        /* Separatori */
        hr { margin-top: 1rem; margin-bottom: 1rem; border-color: #333; }
    </style>
""", unsafe_allow_html=True)

# --- FUNZIONI DI CARICAMENTO ---
def load_data(filename):
    if not os.path.exists(filename): return pd.DataFrame()
    try: return pd.read_csv(filename)
    except: return pd.DataFrame()

def save_data(df, filename):
    df.to_csv(filename, index=False)

# --- SIDEBAR NAVIGAZIONE ---
with st.sidebar:
    st.title("🦅 SNIPER V6")
    st.markdown("---")
    # Menu di Navigazione
    page = st.radio("SALA COMANDO", ["📊 DASHBOARD (Visiva)", "📡 RADAR (Operativo)", "📜 REGISTRO (Storico)"])
    
    st.markdown("---")
    if st.button("🔄 AGGIORNA TUTTO"):
        st.rerun()

# ==============================================================================
# 1. DASHBOARD VISIVA (Il ritorno della V3 Grafica)
# ==============================================================================
if page == "📊 DASHBOARD (Visiva)":
    st.title("📊 Financial Dashboard")
    st.caption("Analisi dell'andamento in tempo reale")

    df_storico = load_data(config.FILE_STORICO)

    # Calcoli KPI
    saldo_iniziale = config.BANKROLL_TOTALE
    if not df_storico.empty:
        # Se non esiste la colonna Profitto_Reale, la creiamo
        if 'Profitto_Reale' not in df_storico.columns: df_storico['Profitto_Reale'] = 0.0
        
        profitto_totale = df_storico['Profitto_Reale'].sum()
        saldo_attuale = saldo_iniziale + profitto_totale
        volume_giocato = df_storico['Stake_Euro'].sum()
        roi = (profitto_totale / volume_giocato * 100) if volume_giocato > 0 else 0
        n_operazioni = len(df_storico)
    else:
        saldo_attuale = saldo_iniziale
        profitto_totale = 0
        volume_giocato = 0
        roi = 0
        n_operazioni = 0

    # METRICHE PRINCIPALI (BIG NUMBERS)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("💰 BANKROLL", f"{saldo_attuale:.2f} €", delta=f"{profitto_totale:.2f} €")
    col2.metric("📈 ROI", f"{roi:.2f} %")
    col3.metric("💸 PROFITTO", f"{profitto_totale:.2f} €")
    col4.metric("🎯 TRADE CHIUSI", n_operazioni)

    st.markdown("---")

    # GRAFICI
    if not df_storico.empty:
        # Creiamo un dataframe temporale per il grafico
        df_chart = df_storico.copy()
        # Simuliamo un andamento cumulativo
        df_chart['Bankroll_Progressivo'] = saldo_iniziale + df_chart['Profitto_Reale'].cumsum()
        df_chart['Index'] = range(1, len(df_chart) + 1)

        c_chart1, c_chart2 = st.columns([2, 1])
        
        with c_chart1:
            st.subheader("📈 Growth Chart")
            fig = px.line(df_chart, x='Index', y='Bankroll_Progressivo', title='Crescita Capitale', markers=True)
            fig.update_traces(line_color='#00CC96', line_width=4)
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white')
            st.plotly_chart(fig, use_container_width=True)

        with c_chart2:
            st.subheader("🍰 Asset Allocation")
            if 'Sport' in df_chart.columns:
                fig_pie = px.pie(df_chart, names='Sport', values='Stake_Euro', donut=0.4)
                fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color='white')
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("Dati sport insufficienti.")
    else:
        st.info("📡 In attesa delle prime operazioni chiuse per generare i grafici.")


# ==============================================================================
# 2. RADAR OPERATIVO (La nuova gestione richiesta)
# ==============================================================================
elif page == "📡 RADAR (Operativo)":
    st.title("📡 Radar Tattico")
    st.caption("Qui gestisci i segnali in arrivo. Modifica la quota, spunta 'Abbinata' e conferma.")

    df_pending = load_data(config.FILE_PENDING)

    if not df_pending.empty:
        # Aggiunta colonne operative se mancano
        if "Abbinata" not in df_pending.columns: df_pending.insert(0, "Abbinata", False)
        if "Quota_Reale_Presa" not in df_pending.columns: df_pending["Quota_Reale_Presa"] = df_pending["Quota_Ingresso"]

        # CONFIGURAZIONE COLONNE PER L'EDITOR
        column_settings = {
            "Abbinata": st.column_config.CheckboxColumn("✅ ABBINATA?", width="small", help="Spunta se hai piazzato la scommessa"),
            "Match": st.column_config.TextColumn("Evento", width="medium"),
            "Selezione": st.column_config.TextColumn("Bet", width="small"),
            "Valore_%": st.column_config.ProgressColumn("EV %", min_value=0, max_value=5, format="%.2f%%"),
            "Quota_Ingresso": st.column_config.NumberColumn("Quota Bot", format="%.2f", disabled=True),
            "Quota_Reale_Presa": st.column_config.NumberColumn("✏️ QUOTA PRESA", format="%.2f", step=0.01, help="Modifica qui se la quota reale è diversa"),
            "Stake_Euro": st.column_config.NumberColumn("Stake", format="%d €"),
            "Target_Scalping": st.column_config.NumberColumn("Target Uscita", format="%.2f"),
        }

        # Filtriamo le colonne da mostrare
        cols_visible = [c for c in column_settings.keys() if c in df_pending.columns]
        
        # EDITOR TABELLARE
        edited_df = st.data_editor(
            df_pending[cols_visible],
            column_config=column_settings,
            hide_index=True,
            use_container_width=True,
            num_rows="dynamic",
            key="radar_edit"
        )

        st.markdown("---")
        b1, b2 = st.columns(2)

        # LOGICA TASTO CONFERMA
        with b1:
            if st.button("💾 CONFERMA E SPOSTA IN REGISTRO", type="primary", use_container_width=True):
                to_move = edited_df[edited_df["Abbinata"] == True].copy()
                
                if not to_move.empty:
                    # Carichiamo lo storico
                    df_storico = load_data(config.FILE_STORICO)
                    
                    # Prepariamo i dati per lo storico
                    # La Quota_Ingresso nello storico diventa quella che hai realmente preso
                    to_move["Quota_Ingresso"] = to_move["Quota_Reale_Presa"]
                    to_move["Esito_Finale"] = "APERTA" # Appena spostata è aperta
                    to_move["Profitto_Reale"] = 0.0    # Ancora nessun profitto
                    
                    # Uniamo allo storico
                    # Usiamo pd.concat per unione sicura
                    df_final_storico = pd.concat([df_storico, to_move], ignore_index=True)
                    # Pulizia colonne extra non necessarie nello storico (come 'Abbinata')
                    if "Abbinata" in df_final_storico.columns: df_final_storico = df_final_storico.drop(columns=["Abbinata"])
                    if "Quota_Reale_Presa" in df_final_storico.columns: df_final_storico = df_final_storico.drop(columns=["Quota_Reale_Presa"])

                    save_data(df_final_storico, config.FILE_STORICO)
                    
                    # Puliamo il Pending (togliamo quelle spostate)
                    remain_pending = edited_df[edited_df["Abbinata"] == False]
                    # Rimuoviamo le colonne temporanee dal file pending per tenerlo pulito
                    clean_pending = remain_pending.drop(columns=["Abbinata", "Quota_Reale_Presa"], errors='ignore')
                    
                    save_data(clean_pending, config.FILE_PENDING)
                    
                    st.success(f"✅ {len(to_move)} Movimenti registrati!")
                    st.rerun()
                else:
                    st.warning("⚠️ Nessuna riga selezionata. Spunta la casella 'ABBINATA' prima di confermare.")

        # LOGICA TASTO RESET
        with b2:
            if st.button("🗑️ SVUOTA RADAR", type="secondary", use_container_width=True):
                # Crea un dataframe vuoto con le colonne originali
                cols_originali = [c for c in df_pending.columns if c not in ["Abbinata", "Quota_Reale_Presa"]]
                save_data(pd.DataFrame(columns=cols_originali), config.FILE_PENDING)
                st.warning("Radar pulito.")
                st.rerun()

    else:
        st.info("🦅 Nessun segnale nel Radar. Il sistema è in scansione...")


# ==============================================================================
# 3. REGISTRO STORICO (Sola lettura e analisi)
# ==============================================================================
elif page == "📜 REGISTRO (Storico)":
    st.title("📜 Registro Ufficiale")
    
    df_storico = load_data(config.FILE_STORICO)

    if not df_storico.empty:
        st.dataframe(
            df_storico, 
            use_container_width=True,
            hide_index=True,
            column_config={
                "Profitto_Reale": st.column_config.NumberColumn("Profitto", format="%.2f €"),
                "Stake_Euro": st.column_config.NumberColumn("Stake", format="%d €")
            }
        )
        
        st.markdown("### 🛠️ Strumenti Registro")
        c1, c2 = st.columns(2)
        with c1:
            csv = df_storico.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Scarica Excel/CSV", data=csv, file_name="registro_sniper.csv", mime="text/csv", use_container_width=True)
        with c2:
            if st.button("🔥 FORMATTAZIONE TOTALE (Cancella Tutto)", type="primary", use_container_width=True):
                save_data(pd.DataFrame(columns=df_storico.columns), config.FILE_STORICO)
                st.error("Registro formattato.")
                st.rerun()
    else:
        st.info("Il Registro è ancora vuoto.")
