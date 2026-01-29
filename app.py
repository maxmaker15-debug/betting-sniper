import streamlit as st
import pandas as pd
import os
import requests
import plotly.express as px
import config
import scanner_calcio
import scanner_tennis

# --- CONFIGURAZIONE PAGINA & TEMA ---
st.set_page_config(page_title="Sniper Terminal Pro", page_icon="🦅", layout="wide")

# --- CSS PERSONALIZZATO (LO STILE "WAR ROOM") ---
st.markdown("""
<style>
    /* Sfondo generale scuro leggermente bluastro */
    .stApp {
        background-color: #0E1117;
    }
    /* Stile Bottoni */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        font-weight: 700;
        background: linear-gradient(90deg, #00C9FF 0%, #92FE9D 100%);
        color: #002b36;
        border: none;
        transition: 0.3s;
    }
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 0 15px rgba(0, 201, 255, 0.7);
    }
    /* Stile Metriche (KPI) */
    div[data-testid="stMetric"] {
        background-color: #1A1C24;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #00C9FF;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    /* Titoli */
    h1, h2, h3 {
        font-family: 'Helvetica Neue', sans-serif;
        color: #FAFAFA;
        text-shadow: 0 0 10px rgba(255,255,255,0.1);
    }
    /* Tabelle */
    div[data-testid="stDataFrame"] {
        border-radius: 10px;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONI DI UTILITÀ ---
def load_data(f): 
    if os.path.isfile(f):
        try: return pd.read_csv(f)
        except: return pd.DataFrame()
    return pd.DataFrame()

def test_telegram_connection():
    TOKEN = "8145327630:AAHJC6vDjvGUyPT0pKw63fyW53hTl_F873U" # I TUOI DATI
    CHAT_ID = "5562163433"
    try:
        requests.get(f"https://api.telegram.org/bot{TOKEN}/sendMessage", params={"chat_id": CHAT_ID, "text": "🦅 TERMINAL CHECK: Connessione stabile."})
        return True
    except: return False

# --- SIDEBAR NAVIGAZIONE ---
with st.sidebar:
    st.title("🦅 SNIPER V.2")
    st.markdown("---")
    selected_page = st.radio("NAVIGAZIONE", ["🏠 Dashboard", "📡 Radar & Scansioni", "📝 Diario & Ordini", "⚙️ Impostazioni"], index=0)
    st.markdown("---")
    
    # Sezione stato rapido
    st.caption("STATO SISTEMA")
    if st.button("🔔 TEST CONNESSIONE"):
        if test_telegram_connection(): st.success("ONLINE")
        else: st.error("OFFLINE")

# --- PAGINA 1: DASHBOARD (HOME) ---
if selected_page == "🏠 Dashboard":
    st.title("🏠 War Room: Situazione Finanziaria")
    
    df = load_data(config.FILE_PENDING)
    
    # CALCOLO KPI
    total_profit = 0.0
    active_trades = 0
    closed_trades = 0
    win_rate = 0.0
    
    if not df.empty:
        if 'Profitto_Reale' in df.columns:
            df['Profitto_Reale'] = pd.to_numeric(df['Profitto_Reale'], errors='coerce').fillna(0)
            total_profit = df['Profitto_Reale'].sum()
        
        if 'Stato_Trade' in df.columns:
            active_trades = df[df['Stato_Trade'] == 'APERTO'].shape[0]
            closed_trades_df = df[df['Stato_Trade'].str.contains("CHIUSO", na=False)]
            closed_trades = closed_trades_df.shape[0]
            
            # Calcolo Win Rate (Consideriamo "Vinta" o "Scalping" come vittoria)
            wins = closed_trades_df[closed_trades_df['Profitto_Reale'] > 0].shape[0]
            if closed_trades > 0:
                win_rate = (wins / closed_trades) * 100

    # VISUALIZZAZIONE KPI (COLONNE)
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("💰 PROFITTO NETTO", f"{total_profit:.2f} €", delta=None)
    kpi2.metric("📊 WIN RATE", f"{win_rate:.1f} %")
    kpi3.metric("🟢 TRADE ATTIVI", active_trades)
    kpi4.metric("🏁 TRADE CHIUSI", closed_trades)

    st.markdown("---")
    
    # GRAFICI (Solo se ci sono dati chiusi)
    if closed_trades > 0:
        col_chart1, col_chart2 = st.columns([2, 1])
        
        with col_chart1:
            st.subheader("📈 Curva dei Profitti (Cumulative)")
            # Creiamo un dataframe temporaneo per il grafico cumulativo
            df_closed = df[df['Stato_Trade'].str.contains("CHIUSO", na=False)].copy()
            # Creiamo un indice fittizio cronologico (assumendo che le righe siano in ordine)
            df_closed['Trade_Num'] = range(1, len(df_closed) + 1)
            df_closed['Cum_Profit'] = df_closed['Profitto_Reale'].cumsum()
            
            fig = px.area(df_closed, x='Trade_Num', y='Cum_Profit', markers=True, 
                          title="Crescita Bankroll", line_shape='spline')
            fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="white")
            fig.update_traces(line_color='#00C9FF')
            st.plotly_chart(fig, use_container_width=True)

        with col_chart2:
            st.subheader("🍰 Distribuzione Sport")
            if 'Sport' in df.columns:
                sport_dist = df['Sport'].value_counts().reset_index()
                sport_dist.columns = ['Sport', 'Count']
                fig2 = px.pie(sport_dist, values='Count', names='Sport', hole=0.4, color_discrete_sequence=px.colors.sequential.Teal)
                fig2.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="white")
                st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("I grafici appariranno qui dopo aver chiuso i primi trade.")

# --- PAGINA 2: RADAR & SCANSIONI ---
elif selected_page == "📡 Radar & Scansioni":
    st.title("📡 Radar di Mercato")
    
    # Pulsanti di Scansione
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🎾 SCANSIONA TENNIS"):
            with st.spinner("Analisi mercati in corso..."): scanner_tennis.scan_tennis()
            st.success("Scansione Tennis Completata!")
            st.rerun()
    with c2:
        if st.button("⚽ SCANSIONA CALCIO"):
            with st.spinner("Analisi mercati in corso..."): scanner_calcio.scan_calcio()
            st.success("Scansione Calcio Completata!")
            st.rerun()
            
    st.markdown("### 🎯 Opportunità Rilevate (Aperte)")
    df = load_data(config.FILE_PENDING)
    
    if not df.empty:
        # Filtra solo aperti
        if 'Stato_Trade' in df.columns:
            df_open = df[df['Stato_Trade'] == 'APERTO']
        else:
            df_open = df
            
        if not df_open.empty:
            # Colonne da mostrare
            cols = ['Sport', 'Orario_Match', 'Match', 'Selezione', 'Quota_Ingresso', 'Pinnacle_Iniziale', 'Target_Scalping', 'Valore_%']
            final_cols = [c for c in cols if c in df_open.columns]
            
            # STYLING DATAFRAME (Evidenziazione)
            # Usiamo column_config per formattare meglio
            st.dataframe(
                df_open[final_cols],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Valore_%": st.column_config.TextColumn(
                        "Valore",
                        help="Margine matematico",
                    ),
                    "Target_Scalping": st.column_config.NumberColumn(
                        "🎯 Exit Scalp",
                        format="%.2f"
                    )
                }
            )
        else:
            st.success("Nessun trade pendente. Il radar è libero.")
    else:
        st.info("Nessun dato. Lancia una scansione.")

# --- PAGINA 3: DIARIO ---
elif selected_page == "📝 Diario & Ordini":
    st.title("📝 Registro Operativo")
    st.info("Qui aggiorni l'esito finale per alimentare le statistiche.")
    
    df = load_data(config.FILE_PENDING)
    if not df.empty:
        # Configurazione Editor
        edited_df = st.data_editor(
            df,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "Stato_Trade": st.column_config.SelectboxColumn(
                    "Stato",
                    options=["APERTO", "CHIUSO (Scalping)", "CHIUSO (Stop Loss)", "CHIUSO (Value Bet Vinta)", "CHIUSO (Value Bet Persa)"],
                    required=True
                ),
                "Profitto_Reale": st.column_config.NumberColumn(
                    "P/L (€)",
                    format="%.2f €"
                ),
                "Quota_Ingresso": st.column_config.NumberColumn(format="%.2f"),
                "Pinnacle_Iniziale": st.column_config.NumberColumn(format="%.2f"),
            }
        )
        
        if st.button("💾 SALVA MODIFICHE AL REGISTRO"):
            edited_df.to_csv(config.FILE_PENDING, index=False)
            st.balloons()
            st.success("Database aggiornato con successo.")
            st.rerun()
    else:
        st.warning("Il registro è vuoto.")

# --- PAGINA 4: IMPOSTAZIONI ---
elif selected_page == "⚙️ Impostazioni":
    st.title("⚙️ Configurazione Sistema")
    st.write("Strumenti di manutenzione.")
    
    col_dang1, col_dang2 = st.columns(2)
    with col_dang1:
        st.error("ZONA PERICOLOSA")
        if st.button("🗑️ CANCELLA TUTTO IL DATABASE (RESET)"):
            if os.path.exists(config.FILE_PENDING):
                os.remove(config.FILE_PENDING)
                st.warning("Database resettato. Riavviare scansioni.")
                st.rerun()
    with col_dang2:
        st.info("INFO SISTEMA")
        st.write(f"Bankroll Configurato: {config.BANKROLL_TOTALE} €")
        st.write(f"Stake Massimo: {config.STAKE_MASSIMO} €")
