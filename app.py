import streamlit as st
import pandas as pd
import os
import requests
import config
import scanner_calcio
import scanner_tennis

# --- CONFIGURAZIONE GRAFICA ---
st.set_page_config(page_title="Betting AI Sniper", page_icon="🦅", layout="wide")
st.markdown("<style>.stApp {background-color: #0E1117;} h1,h2,h3 {color: #FAFAFA;} .stButton>button {width: 100%; border-radius: 5px; font-weight: bold;}</style>", unsafe_allow_html=True)

# --- FUNZIONE TEST TELEGRAM ---
def test_telegram_connection():
    TOKEN = "8145327630:AAHJC6vDjvGUyPT0pKw63fyW53hTl_F873U"
    CHAT_ID = "5562163433"
    msg = "🔔 TEST RIUSCITO! Il Comandante è connesso alla War Room."
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        resp = requests.get(url, params={"chat_id": CHAT_ID, "text": msg})
        return resp.json()
    except Exception as e:
        return {"ok": False, "error": str(e)}

st.sidebar.title("🦅 Sniper Room")
st.sidebar.markdown("---")
# PULSANTE DI TEST
if st.sidebar.button("🔔 TEST NOTIFICA"):
    res = test_telegram_connection()
    if res.get("ok"):
        st.sidebar.success("Inviato! Controlla Telegram.")
    else:
        st.sidebar.error(f"Errore: {res}")

st.sidebar.markdown("---")
page = st.sidebar.radio("MENU", ["📡 Radar Mercati", "📝 Registro", "📊 Stats"])

def load_data(f): return pd.read_csv(f) if os.path.isfile(f) else pd.DataFrame()

if page == "📡 Radar Mercati":
    st.title("📡 Radar Mercati (Live)")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎾 SCANSIONA TENNIS"):
            with st.spinner("Analisi Tennis Sniper..."): scanner_tennis.scan_tennis()
            st.success("Fatto!")
            st.rerun()
    with col2:
        if st.button("⚽ SCANSIONA CALCIO"):
            with st.spinner("Analisi Calcio Sniper..."): scanner_calcio.scan_calcio()
            st.success("Fatto!")
            st.rerun()

    st.write("---")
    df_pend = load_data(config.FILE_PENDING)
    
    if not df_pend.empty and 'Valore_%' in df_pend.columns:
        mask_sniper = df_pend['Valore_%'].astype(str).str.contains("ATTESA", na=False)
        df_sniper = df_pend[mask_sniper]
        df_value = df_pend[~mask_sniper]

        st.subheader("🟢 PRONTE (Punta Subito)")
        if not df_value.empty:
            st.dataframe(df_value[['Sport','Match','Selezione','Quota_Netta','Valore_%']], use_container_width=True, hide_index=True)
        else: st.info("Nessuna Value Bet immediata.")

        st.subheader("🟡 ZONA SNIPER (Richiedi Quota)")
        if not df_sniper.empty:
            view_sniper = df_sniper[['Sport','Match','Selezione','Quota_Netta','Stake_Euro']].rename(columns={'Stake_Euro': '🎯 QUOTA_TARGET'})
            st.dataframe(view_sniper, use_container_width=True, hide_index=True)
        else: st.info("Nessun target Sniper al momento.")
    else:
        st.info("Radar vuoto. Premi uno dei pulsanti sopra per scansionare.")

elif page == "📝 Registro":
    st.title("📝 Gestione Ordini")
    df = load_data(config.FILE_PENDING)
    if not df.empty:
        edited = st.data_editor(df, num_rows="dynamic", use_container_width=True)
        if st.button("💾 SALVA MODIFICHE"):
            edited.to_csv(config.FILE_PENDING, index=False)
            st.success("Salvato!")
    else: st.info("Nessun ordine.")

elif page == "📊 Stats":
    st.title("Statistiche")
    st.write("Presto disponibile con storico.")
