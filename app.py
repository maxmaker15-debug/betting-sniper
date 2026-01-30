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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    /* SFONDO */
    .stApp {
        background-color: #0b1120;
        background-image: radial-gradient(at 50% 0%, #172a46 0px, transparent 50%);
    }
    
    /* SIDEBAR */
    section[data-testid="stSidebar"] {
        background-color: #0f172a;
        border-right: 1px solid #1e293b;
    }
    
    /* CARDS & TABLES */
    div[data-testid="stMetric"], div[data-testid="stDataFrame"] {
        background-color: #1e293b;
        padding: 20px;
        border-radius: 16px;
        border: 1px solid #334155;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
    }
    
    /* TESTI */
    div[data-testid="stMetricLabel"] {
        color: #94a3b8;
        font-size: 0.9rem;
        font-weight: 600;
        text-transform: uppercase;
    }
    div[data-testid="stMetricValue"] {
        color: #f8fafc;
        font-weight: 800;
    }
    
    /* BOTTONI */
    .stButton>button {
        width: 100%;
        height: 50px;
        border-radius: 12px;
        font-weight: 700;
        background: linear-gradient(135deg, #0ea5e9 0%, #10b981 100%);
        color: white;
        border: none;
        transition: all 0.3s ease;
    }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(16, 185, 129, 0.6); }
    
    /* TITOLI */
    h1 {
        background: linear-gradient(90deg, #38bdf8, #818cf8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
    }
    h2, h3 { color: #e2e8f0; }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONI ---
def load_data(f): 
    if os.path.isfile(f):
        try: return pd.read_csv(f)
        except: return pd.DataFrame()
    return pd.DataFrame()

def test_telegram_connection():
    TOKEN = "8145327630:AAHJC6vDjvGUyPT0pKw63fyW53hTl_F873U"
    CHAT_ID = "5562163433"
    try:
        requests.get(f"https://api.telegram.org/bot{TOKEN}/sendMessage", params={"chat_id": CHAT_ID, "text": "🦅 PING: Sistema Operativo."})
        return True
    except: return False

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/7269/7269877.png", width=60)
    st.title("SNIPER PRO")
    st.markdown("<div style='font-size: 12px; color: #64748b; margin-top: -15px;'>V. 3.0 - FIX COLONNE</div>", unsafe_allow_html=True)
    st.markdown("---")
    page = st.radio("MENU", ["📊 Dashboard", "📡 Radar Mercati", "📝 Diario Ordini", "⚙️ Sistema"])
    st.markdown("---")
    if st.button("🔔 PING TELEGRAM"):
        if test_telegram_connection(): st.success("OK")
        else: st.error("KO")

# --- DASHBOARD ---
if page == "📊 Dashboard":
    st.title("Panoramica Finanziaria")
    df = load_data(config.FILE_PENDING)
    
    # KPI Init
    profit = 0.0
    active = 0
    closed = 0
    win_rate = 0.0
    cap_exposed = 0.0
    
    if not df.empty:
        if 'Profitto_Reale' in df.columns:
            df['Profitto_Reale'] = pd.to_numeric(df['Profitto_Reale'], errors='coerce').fillna(0)
            profit = df['Profitto_Reale'].sum()
        if 'Stato_Trade' in df.columns:
            active = df[df['Stato_Trade'] == 'APERTO'].shape[0]
            closed_df = df[df['Stato_Trade'].str.contains("CHIUSO", na=False)]
            closed = closed_df.shape[0]
            wins = closed_df[closed_df['Profitto_Reale'] > 0].shape[0]
            if closed > 0: win_rate = (wins / closed) * 100
            
            # Calcolo capitale esposto (solo se la colonna Stake esiste)
            if active > 0 and 'Stake_Euro' in df.columns:
                try:
                    op = df[df['Stato_Trade'] == 'APERTO'].copy()
                    # Convertiamo in numero, gestendo eventuali errori
                    op['Stake_Euro'] = pd.to_numeric(op['Stake_Euro'], errors='coerce').fillna(0)
                    cap_exposed = op['Stake_Euro'].sum()
                except: pass

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Profitto Netto", f"{profit:+.2f} €", delta="Totale")
    c2.metric("Win Rate", f"{win_rate:.1f}%", delta="Performance")
    c3.metric("Capitale Esposto", f"{cap_exposed:.0f} €", delta=f"{active} attivi", delta_color="off")
    c4.metric("Chiusi", str(closed))

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Charts
    g1, g2 = st.columns([2, 1])
    with g1:
        st.subheader("📈 Trend Bankroll")
        if closed > 0:
            closed_df = df[df['Stato_Trade'].str.contains("CHIUSO", na=False)].copy()
            closed_df['N'] = range(1, len(closed_df)+1)
            closed_df['Cum'] = closed_df['Profitto_Reale'].cumsum()
            fig = px.area(closed_df, x='N', y='Cum', markers=True)
            fig.update_traces(line_color='#0ea5e9', fillcolor='rgba(14, 165, 233, 0.2)')
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#cbd5e1', xaxis_title="Trade", yaxis_title="€", showlegend=False, margin=dict(l=20,r=20,t=20,b=20))
            st.plotly_chart(fig, use_container_width=True)
        else: st.info("Nessun dato storico.")
        
    with g2:
        st.subheader("🎯 Mix Sport")
        if not df.empty and 'Sport' in df.columns:
            sc = df['Sport'].value_counts()
            # FIX: Usiamo px.pie correttamente
            fig2 = px.pie(values=sc.values, names=sc.index, hole=0.6, color_discrete_sequence=['#0ea5e9', '#10b981'])
            fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#cbd5e1', showlegend=True, margin=dict(t=20,b=20,l=20,r=20), legend=dict(orientation="h", y=-0.2))
            st.plotly_chart(fig2, use_container_width=True)

# --- RADAR ---
elif page == "📡 Radar Mercati":
    st.title("Radar Operativo")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🎾 SCANSIONA TENNIS"):
            with st.spinner("..."): scanner_tennis.scan_tennis()
            st.success("OK"); st.rerun()
    with c2:
        if st.button("⚽ SCANSIONA CALCIO"):
            with st.spinner("..."): scanner_calcio.scan_calcio()
            st.success("OK"); st.rerun()
            
    st.markdown("---")
    df = load_data(config.FILE_PENDING)
    if not df.empty:
        df_view = df[df['Stato_Trade'] == 'APERTO'] if 'Stato_Trade' in df.columns else df
        if not df_view.empty:
            st.subheader(f"⚡ Opportunità: {len(df_view)}")
            
            # NUOVE COLONNE CORRETTE
            cols = ['Orario_Match', 'Match', 'Selezione', 'Quota_Ingresso', 'Target_Scalping', 'Quota_Sniper_Target', 'Stake_Euro', 'Valore_%']
            final = [c for c in cols if c in df_view.columns]
            
            st.dataframe(df_view[final], use_container_width=True, hide_index=True, height=400,
                column_config={
                    "Quota_Ingresso": st.column_config.NumberColumn("Ingresso", format="%.2f"),
                    "Target_Scalping": st.column_config.NumberColumn("🎯 Exit Scalp", format="%.2f"),
                    "Quota_Sniper_Target": st.column_config.NumberColumn("🔫 Target Sniper", format="%.2f", help="Se è 0, entra subito. Se > 0, attendi questa quota."),
                    "Stake_Euro": st.column_config.NumberColumn("💰 Stake (€)", format="%d €"),
                    "Valore_%": st.column_config.ProgressColumn("Value", min_value=0, max_value=20, format="%f%%")
                })
        else: st.success("Nessun trade pendente.")
    else: st.info("Radar vuoto.")

# --- DIARIO ---
elif page == "📝 Diario Ordini":
    st.title("Diario")
    df = load_data(config.FILE_PENDING)
    if not df.empty:
        edited = st.data_editor(df, num_rows="dynamic", use_container_width=True,
            column_config={
                "Stato_Trade": st.column_config.SelectboxColumn("Stato", options=["APERTO", "CHIUSO (Scalping)", "CHIUSO (Stop Loss)", "CHIUSO (Value Bet Vinta)", "CHIUSO (Value Bet Persa)"], required=True, width="medium"),
                "Profitto_Reale": st.column_config.NumberColumn("P/L (€)", format="%.2f €")
            })
        if st.button("💾 SALVA"):
            edited.to_csv(config.FILE_PENDING, index=False)
            st.success("Salvato!"); st.rerun()
    else: st.warning("Vuoto.")

# --- SISTEMA ---
elif page == "⚙️ Sistema":
    st.title("Sistema")
    if st.button("🗑️ RESET DATABASE"):
        if os.path.exists(config.FILE_PENDING): os.remove(config.FILE_PENDING)
        st.warning("Database Resettato! Fai una nuova scansione."); st.rerun()
    st.info(f"Bankroll: {config.BANKROLL_TOTALE}€ | Stake Max: {config.STAKE_MASSIMO}€")
