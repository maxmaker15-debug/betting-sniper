import streamlit as st
import pandas as pd
import os
import config

# --- CONFIGURAZIONE PAGINA (FIX TITOLI TAGLIATI) ---
st.set_page_config(
    page_title="Sniper Betting V4",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS PERSONALIZZATO (STILE & LAYOUT) ---
st.markdown("""
    <style>
        /* Riduce lo spazio bianco in alto che tagliava i titoli */
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 1rem !important;
        }
        /* Stile Tabelle */
        .stDataFrame {
            border: 1px solid #444;
            border-radius: 5px;
        }
        /* Metriche in evidenza */
        div[data-testid="stMetricValue"] {
            font-size: 1.8rem !important;
            color: #4CAF50; /* Verde Trading */
        }
    </style>
""", unsafe_allow_html=True)

# --- FUNZIONI DI GESTIONE DATI ---
def load_data(filename):
    if not os.path.exists(filename):
        return pd.DataFrame()
    try:
        return pd.read_csv(filename)
    except:
        return pd.DataFrame()

def save_data(df, filename):
    df.to_csv(filename, index=False)

# --- SIDEBAR (NAVIGAZIONE) ---
with st.sidebar:
    st.title("🦅 SNIPER COMMAND")
    page = st.radio("Navigazione", ["📡 RADAR (Operativo)", "📜 REGISTRO (Storico)", "⚙️ Configurazione"])
    st.markdown("---")
    
    # Reload manuale
    if st.button("🔄 Aggiorna Dati"):
        st.rerun()

# ==============================================================================
# PAGINA 1: RADAR (OPERATIVO)
# ==============================================================================
if page == "📡 RADAR (Operativo)":
    st.title("📡 Radar Operativo")
    st.caption("Gestisci qui le opportunità segnalate dal Bot. Spunta 'Abbinata' per spostarle nello storico.")

    # Carica i dati pendenti
    df_pending = load_data(config.FILE_PENDING)

    if not df_pending.empty:
        # 1. Preparazione Dataframe per l'Editor
        # Aggiungiamo colonne se non esistono
        if "Abbinata" not in df_pending.columns:
            df_pending.insert(0, "Abbinata", False) # Checkbox a sinistra
        if "Quota_Reale_Presa" not in df_pending.columns:
            df_pending["Quota_Reale_Presa"] = df_pending["Quota_Ingresso"] # Default alla quota proposta

        # Ordina colonne per leggibilità
        cols_to_show = [
            "Abbinata", "Match", "Selezione", "Valore_%", 
            "Quota_Ingresso", "Quota_Reale_Presa", "Stake_Euro", 
            "Target_Scalping", "Quota_Sniper_Target", "Torneo", "Orario_Match"
        ]
        # Filtra solo colonne esistenti per evitare errori
        cols_to_show = [c for c in cols_to_show if c in df_pending.columns]
        
        # 2. EDITOR INTERATTIVO (La magia grafica)
        edited_df = st.data_editor(
            df_pending[cols_to_show],
            column_config={
                "Abbinata": st.column_config.CheckboxColumn(
                    "✅ Abbinata?",
                    help="Spunta se hai piazzato la scommessa",
                    default=False,
                ),
                "Valore_%": st.column_config.ProgressColumn(
                    "EV %",
                    help="Valore Atteso",
                    format="%f",
                    min_value=0,
                    max_value=10, # Scala barra grafica
                ),
                "Quota_Reale_Presa": st.column_config.NumberColumn(
                    "Quota Presa (Edit)",
                    help="Modifica se hai preso una quota diversa",
                    step=0.01,
                    format="%.2f"
                ),
                "Stake_Euro": st.column_config.NumberColumn(
                    "Stake (€)",
                    format="%.0f €"
                ),
                "Target_Scalping": st.column_config.NumberColumn(
                    "Target Uscita",
                    format="%.2f"
                )
            },
            hide_index=True,
            use_container_width=True,
            num_rows="dynamic"
        )

        st.markdown("---")
        col_btn1, col_btn2 = st.columns(2)

        # 3. LOGICA DI SPOSTAMENTO (Pending -> Storico)
        with col_btn1:
            if st.button("💾 CONFERMA ABBINATE E ARCHIVIA", type="primary"):
                # Filtra le righe spuntate come "Abbinata"
                abbinate = edited_df[edited_df["Abbinata"] == True].copy()
                
                if not abbinate.empty:
                    # Carica storico esistente
                    df_storico = load_data(config.FILE_STORICO)
                    
                    # Prepara le righe per lo storico
                    # Aggiorniamo la quota ingresso con quella realmente presa dall'utente
                    abbinate["Quota_Ingresso"] = abbinate["Quota_Reale_Presa"]
                    abbinate["Esito_Finale"] = "PENDING" # In attesa di risultato reale
                    abbinate["Profitto_Reale"] = 0.0
                    
                    # Rimuovi colonne temporanee (Abbinata, Quota_Reale_Presa) per pulizia se vuoi, 
                    # o tienile. Qui le puliamo per uniformità.
                    cols_finali = [c for c in df_pending.columns if c not in ["Abbinata", "Quota_Reale_Presa"]]
                    # Aggiungiamo eventuali colonne mancanti allo storico
                    
                    # Unisci e salva
                    df_combined = pd.concat([df_storico, abbinate], ignore_index=True)
                    # Assicuriamoci di salvare tutte le colonne utili
                    save_data(df_combined, config.FILE_STORICO)
                    
                    # RIMUOVI LE ABBINATE DAL PENDING (RADAR)
                    # Identifichiamo le righe NON abbinate
                    non_abbinate = edited_df[edited_df["Abbinata"] == False]
                    
                    # Ripristiniamo il formato originale per il file pending
                    # (Rimuovendo le colonne extra aggiunte dall'editor)
                    save_data(non_abbinate.drop(columns=["Abbinata", "Quota_Reale_Presa"], errors='ignore'), config.FILE_PENDING)
                    
                    st.success(f"✅ {len(abbinate)} operazioni spostate nel Registro!")
                    st.rerun()
                else:
                    st.warning("⚠️ Nessuna operazione selezionata come 'Abbinata'.")

        # 4. TASTO PULIZIA
        with col_btn2:
            if st.button("🗑️ RESETTA RADAR (Cancella Tutto)"):
                # Crea dataframe vuoto con le colonne giuste
                empty_df = pd.DataFrame(columns=df_pending.columns).drop(columns=["Abbinata", "Quota_Reale_Presa"], errors='ignore')
                save_data(empty_df, config.FILE_PENDING)
                st.warning("Radar pulito.")
                st.rerun()

    else:
        st.info("🦅 Il Radar è pulito. In attesa di segnali dal drone...")
        st.markdown("*(Controlla Telegram per nuove notifiche)*")

# ==============================================================================
# PAGINA 2: REGISTRO (STORICO)
# ==============================================================================
elif page == "📜 REGISTRO (Storico)":
    st.title("📜 Registro Ufficiale")
    
    df_storico = load_data(config.FILE_STORICO)
    
    if not df_storico.empty:
        # STATISTICHE
        col1, col2, col3 = st.columns(3)
        
        # Calcolo Profitto (Logica da implementare post-match, per ora simuliamo stake totali)
        totale_investito = df_storico["Stake_Euro"].sum()
        operazioni_totali = len(df_storico)
        
        col1.metric("Operazioni Totali", operazioni_totali)
        col2.metric("Volume Totale (€)", f"{totale_investito} €")
        
        # Qui in futuro potremo mettere il Profitto Reale se implementiamo il result check
        # col3.metric("Profitto Netto", f"{profitto} €")

        st.markdown("### 📋 Elenco Transazioni")
        
        # Visualizzazione Tabellare Pulita
        st.dataframe(
            df_storico,
            use_container_width=True,
            column_config={
                "Stake_Euro": st.column_config.NumberColumn("Stake", format="%.2f €"),
                "Valore_%": st.column_config.NumberColumn("EV %", format="%.2f %%"),
                "Orario_Match": "Data",
            },
            hide_index=True
        )
        
        # Export CSV
        csv = df_storico.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Scarica Registro Excel/CSV", csv, "registro_sniper.csv", "text/csv")
        
        # Reset Storico (Pericolo)
        with st.expander("⚠️ Zona Pericolo"):
            if st.button("🔥 CANCELLA TUTTO LO STORICO"):
                save_data(pd.DataFrame(columns=df_storico.columns), config.FILE_STORICO)
                st.error("Storico cancellato.")
                st.rerun()
    else:
        st.info("Nessuna operazione registrata finora.")

# ==============================================================================
# PAGINA 3: CONFIGURAZIONE
# ==============================================================================
elif page == "⚙️ Configurazione":
    st.title("⚙️ Parametri Sistema")
    st.markdown("Visualizza i parametri attuali caricati da `config.py`")
    
    st.code(f"""
    BANKROLL: {config.BANKROLL_TOTALE} €
    STAKE MASSIMO: {config.STAKE_MASSIMO} €
    STAKE MINIMO: {config.STAKE_MINIMO} €
    
    SOGLIA VALUE CALCIO: {config.SOGLIA_VALUE_CALCIO}%
    SOGLIA SNIPER CALCIO: {config.SOGLIA_SNIPER_CALCIO}%
    """, language="yaml")
