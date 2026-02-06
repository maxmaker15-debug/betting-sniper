import streamlit as st
import pandas as pd
import os
import sys
import config

# --- 1. AVVIO SICURO ---
st.set_page_config(layout="wide", page_title="Sniper Debug Mode")

st.title("🦅 Sniper System Check")
st.text("Avvio sistema in corso...")

# --- 2. CONTROLLO LIBRERIE ---
try:
    import plotly.express as px
    import plotly.graph_objects as go
    st.success("✅ Librerie Grafiche Caricate")
except ImportError as e:
    st.error(f"❌ Errore Librerie: {e}")
    st.stop()

# --- 3. FUNZIONI DI AUTO-RIPARAZIONE DATABASE ---
def load_data_safe(filename, expected_columns=None):
    if not os.path.exists(filename):
        return pd.DataFrame()
    
    try:
        # Prova a leggere il file
        df = pd.read_csv(filename)
        return df
    except Exception as e:
        st.warning(f"⚠️ File {filename} corrotto o illeggibile ({e}). Eseguo RESET automatico.")
        # Se fallisce, resetta il file
        if expected_columns:
            df_new = pd.DataFrame(columns=expected_columns)
            df_new.to_csv(filename, index=False)
            return df_new
        else:
            # Se non sappiamo le colonne, creiamo un file vuoto generico o cancelliamo
            os.remove(filename)
            return pd.DataFrame()

def save_data(df, filename):
    df.to_csv(filename, index=False)

# --- 4. CARICAMENTO DATI ---
st.text("Caricamento Database...")

# Colonne previste per evitare errori
cols_pending = ["Sport", "Data_Scan", "Orario_Match", "Torneo", "Match", "Selezione", "Bookmaker", "Quota_Ingresso", "Pinnacle_Iniziale", "Target_Scalping", "Quota_Sniper_Target", "Valore_%", "Stake_Euro", "Stato_Trade", "Esito_Finale", "Profitto_Reale"]
cols_storico = cols_pending # Usiamo la stessa struttura base

df_pending = load_data_safe(config.FILE_PENDING, cols_pending)
df_storico = load_data_safe(config.FILE_STORICO, cols_storico)

st.success(f"✅ Database Caricati. Pending: {len(df_pending)} righe | Storico: {len(df_storico)} righe")

# --- 5. LOGICA DI DASHBOARD (SEMPLIFICATA PER TEST) ---

# Calcoli
saldo_iniziale = config.BANKROLL_TOTALE
profitto_totale = 0.0
volume_giocato = 0.0
roi = 0.0
roe = 0.0
rotazione = 0.0

if not df_storico.empty:
    if 'Profitto_Reale' not in df_storico.columns: df_storico['Profitto_Reale'] = 0.0
    if 'Stake_Euro' not in df_storico.columns: df_storico['Stake_Euro'] = 0.0
    
    profitto_totale = df_storico['Profitto_Reale'].sum()
    volume_giocato = df_storico['Stake_Euro'].sum()
    if volume_giocato > 0: roi = (profitto_totale / volume_giocato) * 100
    if saldo_iniziale > 0: roe = (profitto_totale / saldo_iniziale) * 100

saldo_attuale = saldo_iniziale + profitto_totale

st.markdown("---")

# KPI
k1, k2, k3, k4 = st.columns(4)
k1.metric("BANKROLL", f"{saldo_attuale:.2f} €")
k2.metric("PROFITTO", f"{profitto_totale:.2f} €")
k3.metric("ROI", f"{roi:.2f} %")
k4.metric("ROE", f"{roe:.2f} %")

st.markdown("---")

# RADAR
st.subheader("📡 RADAR OPERATIVO")
col_scan, col_reset = st.columns([1, 4])
with col_scan:
    if st.button("🔄 SCANSIONE MANUALE"):
        st.info("Esecuzione Scanner...")
        import subprocess
        try:
            subprocess.run([sys.executable, "scanner_calcio.py"], check=True)
            st.success("Scanner Completato! Ricarica la pagina.")
            st.rerun()
        except Exception as e:
            st.error(f"Errore Scanner: {e}")

if not df_pending.empty:
    # Preparazione Editor
    if "Abbinata" not in df_pending.columns: df_pending.insert(0, "Abbinata", False)
    if "Quota_Reale_Presa" not in df_pending.columns: df_pending["Quota_Reale_Presa"] = df_pending["Quota_Ingresso"]

    edited_df = st.data_editor(
        df_pending,
        column_config={
            "Abbinata": st.column_config.CheckboxColumn("✅", width="small"),
            "Valore_%": st.column_config.ProgressColumn("EV", min_value=0, max_value=5, format="%.2f"),
        },
        use_container_width=True,
        hide_index=True
    )

    if st.button("💾 CONFERMA E ARCHIVIA"):
        to_move = edited_df[edited_df["Abbinata"] == True].copy()
        if not to_move.empty:
            to_move["Quota_Ingresso"] = to_move["Quota_Reale_Presa"]
            to_move["Esito_Finale"] = "APERTA"
            to_move["Profitto_Reale"] = 0.0
            
            # Unione sicura
            # Rimuoviamo colonne helper prima di salvare
            cols_clean = [c for c in to_move.columns if c not in ["Abbinata", "Quota_Reale_Presa"]]
            to_move_clean = to_move[cols_clean]
            
            # Assicuriamoci che lo storico abbia le stesse colonne
            df_storico_clean = df_storico.dropna(axis=1, how='all') # Pulizia preventiva
            
            df_final = pd.concat([df_storico, to_move_clean], ignore_index=True)
            save_data(df_final, config.FILE_STORICO)
            
            # Pulizia Pending
            remain = edited_df[edited_df["Abbinata"] == False]
            cols_remain = [c for c in remain.columns if c not in ["Abbinata", "Quota_Reale_Presa"]]
            save_data(remain[cols_remain], config.FILE_PENDING)
            
            st.success("Archiviato!")
            st.rerun()
else:
    st.info("Nessun match in attesa.")

# GRAFICI (Proviamo a caricarli per ultimi per evitare blocchi)
st.markdown("---")
st.subheader("📊 GRAFICI")
if not df_storico.empty:
    try:
        df_chart = df_storico.copy()
        df_chart['Progressivo'] = saldo_iniziale + df_chart['Profitto_Reale'].cumsum()
        fig = px.line(df_chart, y='Progressivo', title="Trend")
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.warning(f"Impossibile generare grafico: {e}")
