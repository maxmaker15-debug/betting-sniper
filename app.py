import streamlit as st
import pandas as pd
import os
import requests
import config
import scanner_calcio
import scanner_tennis

# --- CONFIGURAZIONE GRAFICA ---
st.set_page_config(page_title="Sniper Trading Station", page_icon="🦅", layout="wide")
st.markdown("<style>.stApp {background-color: #0E1117;} h1,h2,h3 {color: #FAFAFA;} .stButton>button {width: 100%; border-radius: 5px; font-weight: bold; background-color: #00ADB5; color: white;}</style>", unsafe_allow_html=True)

# --- FUNZIONI DI UTILITÀ ---
def load_data(f): 
    if os.path.isfile(f):
        try:
            return pd.read_csv(f)
        except:
            return pd.DataFrame()
    return pd.DataFrame()

def test_telegram_connection():
    # I tuoi dati fissi
    TOKEN = "8145327630:AAHJC6vDjvGUyPT0pKw63fyW53hTl_F873U"
    CHAT_ID = "5562163433"
    msg = "🦅 TEST SISTEMA: Il Comandante è connesso. Watchdog pronto."
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        resp = requests.get(url, params={"chat_id": CHAT_ID, "text": msg})
        return resp.json()
    except Exception as e:
        return {"ok": False, "error": str(e)}

# --- SIDEBAR (MENU LATERALE) ---
st.sidebar.title("🦅 Sniper Trading")
st.sidebar.info("Modalità: Scalping + Watchdog")

# Pulsante Test Telegram
if st.sidebar.button("🔔 TEST NOTIFICA"):
    res = test_telegram_connection()
    if res.get("ok"):
        st.sidebar.success("Inviato!")
    else:
        st.sidebar.error("Errore collegamento.")

# Pulsante Emergenza CSV (Utile se cambi le colonne e dà errore)
st.sidebar.markdown("---")
if st.sidebar.button("🗑️ RESETTA CSV (Emergenza)"):
    if os.path.exists(config.FILE_PENDING):
        os.remove(config.FILE_PENDING)
        st.sidebar.warning("File CSV cancellato. Fai una nuova scansione.")
        st.rerun()

st.sidebar.markdown("---")
page = st.sidebar.radio("SALA COMANDI", ["📡 Radar Live", "📝 Diario Trading", "📊 Statistiche"])

# --- PAGINA 1: RADAR MERCATI ---
if page == "📡 Radar Live":
    st.title("📡 Radar Mercati (Scalping & Value)")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎾 SCANSIONA TENNIS"):
            with st.spinner("Analisi Tennis + Controllo Drift..."): scanner_tennis.scan_tennis()
            st.success("Fatto!")
            st.rerun()
    with col2:
        if st.button("⚽ SCANSIONA CALCIO"):
            with st.spinner("Analisi Calcio + Controllo Drift..."): scanner_calcio.scan_calcio()
            st.success("Fatto!")
            st.rerun()

    st.write("---")
    df_pend = load_data(config.FILE_PENDING)
    
    # Verifica che il CSV non sia vuoto
    if not df_pend.empty:
        # Filtro: Mostriamo nel radar solo i trade APERTI
        # Se la colonna Stato_Trade non esiste (vecchio file), mostriamo tutto
        if 'Stato_Trade' in df_pend.columns:
             df_view = df_pend[df_pend['Stato_Trade'] == 'APERTO']
        else:
             df_view = df_pend

        st.subheader(f"🎯 Opportunità Attive ({len(df_view)})")
        
        if not df_view.empty:
            # Definiamo le colonne importanti da mostrare
            cols_target = ['Sport', 'Orario_Match', 'Match', 'Selezione', 'Quota_Ingresso', 'Pinnacle_Iniziale', 'Target_Scalping', 'Stake_Euro', 'Valore_%']
            
            # Filtriamo solo le colonne che esistono davvero nel file (per evitare errori)
            cols_existing = [c for c in cols_target if c in df_view.columns]
            
            st.dataframe(df_view[cols_existing], use_container_width=True, hide_index=True)
        else:
            st.info("Nessuna posizione aperta. Il Radar è pulito.")
    else:
        st.info("Radar vuoto. Premi 'SCANSIONA' per cercare occasioni.")

# --- PAGINA 2: DIARIO TRADING ---
elif page == "📝 Diario Trading":
    st.title("📝 Gestione Ordini & Contabilità")
    st.markdown("Aggiorna qui lo stato dei tuoi trade (Scalping riuscito, Stop Loss, ecc.)")
    
    df = load_data(config.FILE_PENDING)
    if not df.empty:
        # Configurazione delle colonne per l'editor
        column_config = {
            "Stato_Trade": st.column_config.SelectboxColumn(
                "Stato",
                help="Esito dell'operazione",
                width="medium",
                options=[
                    "APERTO",
                    "CHIUSO (Scalping)",
                    "CHIUSO (Stop Loss)",
                    "CHIUSO (Value Bet Vinta)",
                    "CHIUSO (Value Bet Persa)"
                ],
                required=True,
            ),
            "Profitto_Reale": st.column_config.NumberColumn(
                "Profitto (€)",
                help="Inserisci profitto o perdita reale",
                format="%.2f €"
            )
        }
        
        # Editor interattivo
        edited_df = st.data_editor(
            df, 
            num_rows="dynamic", 
            use_container_width=True,
            column_config=column_config
        )
        
        if st.button("💾 SALVA AGGIORNAMENTI"):
            edited_df.to_csv(config.FILE_PENDING, index=False)
            st.success("Diario salvato correttamente!")
            st.rerun()
    else:
        st.info("Nessun ordine nel registro.")

# --- PAGINA 3: STATISTICHE ---
elif page == "📊 Stats":
    st.title("📊 Performance Trading")
    df = load_data(config.FILE_PENDING)
    
    if not df.empty and 'Profitto_Reale' in df.columns:
        # Convertiamo in numeri per sicurezza
        df['Profitto_Reale'] = pd.to_numeric(df['Profitto_Reale'], errors='coerce').fillna(0)
        
        # Calcoli
        total_profit = df['Profitto_Reale'].sum()
        # Contiamo solo le righe che contengono "CHIUSO" nello stato
        if 'Stato_Trade' in df.columns:
            trades_closed = df[df['Stato_Trade'].str.contains("CHIUSO", na=False)].shape[0]
        else:
            trades_closed = 0
        
        # Metriche
        col1, col2, col3 = st.columns(3)
        col1.metric("Profitto Totale", f"{total_profit:.2f} €", delta_color="normal")
        col2.metric("Trade Chiusi", trades_closed)
        
        avg_profit = 0
        if trades_closed > 0:
            avg_profit = total_profit / trades_closed
        col3.metric("Profitto Medio", f"{avg_profit:.2f} €")
        
        st.divider()
        st.subheader("Curva dei Profitti")
        if trades_closed > 0:
            st.bar_chart(df['Profitto_Reale'])
        else:
            st.info("Chiudi qualche trade nel Diario per vedere il grafico.")
    else:
        st.info("Non ci sono ancora dati sufficienti.")
