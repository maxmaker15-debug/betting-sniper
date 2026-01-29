import streamlit as st
import pandas as pd
import os
import requests
import plotly.express as px
import plotly.graph_objects as go
import config
import scanner_calcio
import scanner_tennis

# --- CONFIGURAZIONE PAGINA & TEMA ---
st.set_page_config(page_title="Sniper Finance Terminal", page_icon="🦅", layout="wide")

# --- CSS "FILA FINANCE" STYLE ---
st.markdown("""
<style>
    /* IMPORT FONT (Opzionale, usa quello di sistema se fallisce) */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* SFONDO GENERALE (Dark Midnight) */
    .stApp {
        background-color: #0b1120;
        background-image: radial-gradient(at 50% 0%, #172a46 0px, transparent 50%);
    }

    /* STYLE SIDEBAR */
    section[data-testid="stSidebar"] {
        background-color: #0f172a;
        border-right: 1px solid #1e293b;
    }

    /* CARDS (Riquadri KPI e Grafici) */
    div[data-testid="stMetric"], div[data-testid="stDataFrame"] {
        background-color: #1e293b; /* Slate 800 */
        padding: 20px;
        border-radius: 16px;
        border: 1px solid #334155;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
        transition: transform 0.2s;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 25px rgba(0, 201, 255, 0.15);
        border-color: #00c9ff;
    }

    /* TITOLI KPI */
    div[data-testid="stMetricLabel"] {
        color: #94a3b8; /* Slate 400 */
        font-size: 0.9rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    /* VALORI KPI */
    div[data-testid="stMetricValue"] {
        color: #f8fafc;
        font-weight: 800;
        text-shadow: 0 0 10px rgba(255,255,255,0.1);
    }

    /* BOTTONI PRINCIPALI (Gradiente Fila) */
    .stButton>button {
        width: 100%;
        height: 50px;
        border-radius: 12px;
        font-weight: 700;
        font-size: 16px;
        background: linear-gradient(135deg, #0ea5e9 0%, #10b981 100%); /* Blue to Green */
        color: white;
        border: none;
        box-shadow: 0 4px 15px rgba(14, 165, 233, 0.4);
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(16, 185, 129, 0.6);
    }

    /* TABELLE (Dataframe) */
    [data-testid="stDataFrame"] {
        background-color: #1e293b;
    }
    
    /* TITOLI PAGINA */
    h1 {
        background: linear-gradient(90deg, #38bdf8, #818cf8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
    }
    h2, h3 {
        color: #e2e8f0;
    }

    /* RESPONSIVE MOBILE FIX */
    @media (max-width: 640px) {
        .stButton>button {
            margin-bottom: 10px;
        }
        div[data-testid="stMetric"] {
            margin-bottom: 15px;
        }
    }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONI CARICAMENTO DATI ---
def load_data(f): 
    if os.path.isfile(f):
        try: return pd.read_csv(f)
        except: return pd.DataFrame()
    return pd.DataFrame()

def test_telegram_connection():
    # I TUOI DATI TELEGRAM
    TOKEN = "8145327630:AAHJC6vDjvGUyPT0pKw63fyW53hTl_F873U"
    CHAT_ID = "5562163433"
    try:
        requests.get(f"https://api.telegram.org/bot{TOKEN}/sendMessage", params={"chat_id": CHAT_ID, "text": "🦅 TERMINAL CHECK: Connessione stabile."})
        return True
    except: return False

# --- MENU LATERALE (SIDEBAR) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/7269/7269877.png", width=60) # Icona Finance
    st.title("SNIPER PRO")
    st.markdown("<div style='font-size: 12px; color: #64748b; margin-top: -15px;'>V. 2.0 - FINANCE EDITION</div>", unsafe_allow_html=True)
    st.markdown("---")
    
    selected_page = st.radio(
        "NAVIGAZIONE", 
        ["📊 Dashboard", "📡 Radar Mercati", "📝 Diario Ordini", "⚙️ Sistema"], 
        index=0
    )
    
    st.markdown("---")
    # Quick Action Sidebar
    if st.button("🔔 PING TELEGRAM"):
        if test_telegram_connection(): st.success("ONLINE")
        else: st.error("OFFLINE")

# --- PAGINA 1: DASHBOARD (War Room) ---
if selected_page == "📊 Dashboard":
    st.title("Panoramica Finanziaria")
    st.markdown("Benvenuto nella War Room, Comandante.")
    
    df = load_data(config.FILE_PENDING)
    
    # --- CALCOLO KPI ---
    total_profit = 0.0
    active_trades = 0
    closed_trades = 0
    win_rate = 0.0
    invested_capital = 0.0
    
    if not df.empty:
        if 'Profitto_Reale' in df.columns:
            df['Profitto_Reale'] = pd.to_numeric(df['Profitto_Reale'], errors='coerce').fillna(0)
            total_profit = df['Profitto_Reale'].sum()
        
        if 'Stato_Trade' in df.columns:
            active_trades = df[df['Stato_Trade'] == 'APERTO'].shape[0]
            closed_trades_df = df[df['Stato_Trade'].str.contains("CHIUSO", na=False)]
            closed_trades = closed_trades_df.shape[0]
            
            wins = closed_trades_df[closed_trades_df['Profitto_Reale'] > 0].shape[0]
            if closed_trades > 0:
                win_rate = (wins / closed_trades) * 100
        
        # Calcolo capitale esposto (somma stake aperti)
        if 'Stake_Euro' in df.columns and active_trades > 0:
            # Pulizia stringhe tipo "45€" -> 45
            try:
                open_df = df[df['Stato_Trade'] == 'APERTO'].copy()
                open_df['Stake_Clean'] = open_df['Stake_Euro'].astype(str).str.extract(r'(\d+)').astype(float)
                invested_capital = open_df['Stake_Clean'].sum()
            except: pass

    # --- KPI CARDS (ROW 1) ---
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(label="Profitto Netto", value=f"{total_profit:+.2f} €", delta="Totale")
    with col2:
        st.metric(label="Win Rate", value=f"{win_rate:.1f}%", delta="Performance")
    with col3:
        st.metric(label="Capitale Esposto", value=f"{invested_capital:.0f} €", delta=f"{active_trades} Trade Aperti", delta_color="off")
    with col4:
        st.metric(label="Trade Chiusi", value=str(closed_trades), delta="Storico")

    st.markdown("<br>", unsafe_allow_html=True) # Spaziatore

    # --- GRAFICI (ROW 2) ---
    c_chart1, c_chart2 = st.columns([2, 1])
    
    with c_chart1:
        st.subheader("📈 Crescita Bankroll")
        if closed_trades > 0:
            df_closed = df[df['Stato_Trade'].str.contains("CHIUSO", na=False)].copy()
            df_closed['Trade_Num'] = range(1, len(df_closed) + 1)
            df_closed['Cum_Profit'] = df_closed['Profitto_Reale'].cumsum()
            
            # Grafico Area Moderno con sfumatura
            fig = px.area(df_closed, x='Trade_Num', y='Cum_Profit', markers=True)
            fig.update_traces(line_color='#0ea5e9', fillcolor='rgba(14, 165, 233, 0.2)')
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', 
                plot_bgcolor='rgba(0,0,0,0)', 
                font_color='#cbd5e1',
                xaxis_title="Numero Operazioni",
                yaxis_title="Profitto Cumulativo (€)",
                showlegend=False,
                margin=dict(l=20, r=20, t=20, b=20)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Chiudi il tuo primo trade per vedere il grafico di crescita.")

    with c_chart2:
        st.subheader("🎯 Distribuzione")
        if not df.empty and 'Sport' in df.columns:
            sport_counts = df['Sport'].value_counts()
            fig2 = px.donut(values=sport_counts.values, names=sport_counts.index, hole=0.6, color_discrete_sequence=['#0ea5e9', '#10b981', '#6366f1'])
            fig2.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', 
                plot_bgcolor='rgba(0,0,0,0)',
                font_color='#cbd5e1',
                showlegend=True,
                margin=dict(t=20, b=20, l=20, r=20),
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig2, use_container_width=True)

# --- PAGINA 2: RADAR ---
elif selected_page == "📡 Radar Mercati":
    st.title("Radar Operativo")
    
    # Bottoni Scansione Grandi
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🎾 SCANSIONA TENNIS LIVE"):
            with st.spinner("Analisi Tennis in corso..."): scanner_tennis.scan_tennis()
            st.success("Scansione Completata")
            st.rerun()
    with c2:
        if st.button("⚽ SCANSIONA CALCIO LIVE"):
            with st.spinner("Analisi Calcio in corso..."): scanner_calcio.scan_calcio()
            st.success("Scansione Completata")
            st.rerun()
            
    st.markdown("---")
    
    df = load_data(config.FILE_PENDING)
    if not df.empty:
        # Filtro Aperti
        if 'Stato_Trade' in df.columns:
            df_open = df[df['Stato_Trade'] == 'APERTO']
        else:
            df_open = df
            
        if not df_open.empty:
            st.subheader(f"⚡ Opportunità Attive: {len(df_open)}")
            
            # Selezione colonne smart
            cols_ok = ['Orario_Match', 'Match', 'Selezione', 'Quota_Ingresso', 'Pinnacle_Iniziale', 'Target_Scalping', 'Stake_Euro', 'Valore_%']
            final_cols = [c for c in cols_ok if c in df_open.columns]
            
            # Dataframe con stile
            st.dataframe(
                df_open[final_cols],
                use_container_width=True,
                hide_index=True,
                height=400,
                column_config={
                    "Quota_Ingresso": st.column_config.NumberColumn("Ingresso", format="%.2f"),
                    "Target_Scalping": st.column_config.NumberColumn("🎯 Exit", format="%.2f"),
                    "Pinnacle_Iniziale": st.column_config.NumberColumn("📉 Pinna", format="%.2f"),
                    "Stake_Euro": st.column_config.TextColumn("💰 Stake"),
                    "Valore_%": st.column_config.ProgressColumn("Qualità", min_value=0, max_value=20, format="%f%%")
                }
            )
        else:
            st.success("Nessun trade pendente. Radar libero.")
    else:
        st.info("Nessun dato nel radar.")

# --- PAGINA 3: DIARIO ---
elif selected_page == "📝 Diario Ordini":
    st.title("Registro Operazioni")
    
    df = load_data(config.FILE_PENDING)
    if not df.empty:
        st.markdown("Aggiorna qui lo stato delle tue operazioni.")
        
        edited_df = st.data_editor(
            df,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "Stato_Trade": st.column_config.SelectboxColumn(
                    "Stato",
                    options=["APERTO", "CHIUSO (Scalping)", "CHIUSO (Stop Loss)", "CHIUSO (Value Bet Vinta)", "CHIUSO (Value Bet Persa)"],
                    required=True,
                    width="medium"
                ),
                "Profitto_Reale": st.column_config.NumberColumn(
                    "P/L (€)",
                    format="%.2f €",
                    help="Inserisci il profitto o la perdita netta"
                )
            }
        )
        
        if st.button("💾 SALVA MODIFICHE DIARIO"):
            edited_df.to_csv(config.FILE_PENDING, index=False)
            st.balloons()
            st.success("Diario Aggiornato!")
            st.rerun()
    else:
        st.warning("Il diario è vuoto.")

# --- PAGINA 4: SISTEMA ---
elif selected_page == "⚙️ Sistema":
    st.title("Manutenzione Sistema")
    
    c_danger, c_info = st.columns(2)
    
    with c_danger:
        st.error("Area Pericolosa")
        st.markdown("Se il database si corrompe o vuoi ricominciare da zero:")
        if st.button("🗑️ RESET DATABASE (CANCELLA TUTTO)"):
            if os.path.exists(config.FILE_PENDING):
                os.remove(config.FILE_PENDING)
                st.warning("Database eliminato. Riavviare scansioni.")
                st.rerun()

    with c_info:
        st.info("Parametri Attuali")
        st.markdown(f"""
        - **Bankroll:** {config.BANKROLL_TOTALE} €
        - **Stake Max:** {config.STAKE_MASSIMO} €
        - **Kelly Fraction:** {config.KELLY_FRACTION}
        - **Commissione:** {config.COMMISSIONE_BETFAIR * 100}%
        """)
