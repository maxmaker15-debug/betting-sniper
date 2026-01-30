import streamlit as st
import pandas as pd
import os
import requests
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import config
import scanner_calcio
import scanner_tennis

# --- CONFIGURAZIONE PAGINA (LAYOUT WIDE & TITLE) ---
st.set_page_config(page_title="Sniper Terminal", page_icon="🦅", layout="wide")

# --- CSS AVANZATO (STILE "CYBER-BLOOMBERG") ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&family=JetBrains+Mono:wght@400;700&display=swap');
    
    /* 1. RESET GENERALE E FONT */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        font-size: 14px; /* Testo più piccolo e professionale */
    }
    h1, h2, h3 {
        font-family: 'Inter', sans-serif;
        letter-spacing: -0.5px;
    }
    
    /* 2. RIDUZIONE SPAZI VUOTI (COMPATTARE) */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 1rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }
    
    /* 3. SFONDO E TEMA */
    .stApp {
        background-color: #0f1116; /* Nero profondo leggermente blu */
        background-image: 
            linear-gradient(rgba(15, 17, 22, 0.9), rgba(15, 17, 22, 0.9)),
            url("https://www.transparenttextures.com/patterns/carbon-fibre.png");
    }
    
    /* 4. SIDEBAR PIÙ ELEGANTE */
    section[data-testid="stSidebar"] {
        background-color: #090a0d;
        border-right: 1px solid #1f2937;
    }
    
    /* 5. METRICHE (KPI CARDS) CUSTOM */
    /* Nascondiamo quelle default brutte e usiamo HTML custom nel codice Python, 
       ma se usiamo st.metric le stilizziamo qui */
    div[data-testid="stMetric"] {
        background-color: #161b22;
        border: 1px solid #2d3748;
        padding: 10px 15px; /* Molto meno padding */
        border-radius: 8px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    div[data-testid="stMetricLabel"] {
        font-size: 11px !important;
        color: #9ca3af !important;
        text-transform: uppercase;
        margin-bottom: 2px !important;
    }
    div[data-testid="stMetricValue"] {
        font-size: 20px !important; /* Numeri più piccoli rispetto a prima */
        font-family: 'JetBrains Mono', monospace; /* Font stile codice per i numeri */
        color: #e5e7eb !important;
    }
    
    /* 6. TABELLE (DATAFRAME) PIÙ PULITE */
    div[data-testid="stDataFrame"] {
        border: 1px solid #2d3748;
        border-radius: 8px;
        overflow: hidden;
    }
    
    /* 7. BOTTONI MODERNI (Glow Effect) */
    .stButton>button {
        background: linear-gradient(to right, #2563eb, #06b6d4);
        color: white;
        border: none;
        border-radius: 6px;
        height: 38px; /* Più bassi */
        font-size: 13px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        transition: all 0.2s;
    }
    .stButton>button:hover {
        opacity: 0.9;
        box-shadow: 0 0 15px rgba(6, 182, 212, 0.4);
        transform: scale(1.01);
    }
    
    /* 8. ALERT E BOX VARI */
    .stAlert {
        padding: 0.5rem 1rem;
        border-radius: 6px;
    }
    
    /* TITOLI HEADER */
    .header-title {
        font-size: 24px;
        font-weight: 800;
        background: -webkit-linear-gradient(0deg, #38bdf8, #818cf8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .header-subtitle {
        font-size: 12px;
        color: #6b7280;
        margin-top: -5px;
        font-family: 'JetBrains Mono', monospace;
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
    TOKEN = config.TELEGRAM_TOKEN if hasattr(config, 'TELEGRAM_TOKEN') else "8145327630:AAHJC6vDjvGUyPT0pKw63fyW53hTl_F873U"
    CHAT_ID = config.TELEGRAM_CHAT_ID if hasattr(config, 'TELEGRAM_CHAT_ID') else "5562163433"
    try:
        requests.get(f"https://api.telegram.org/bot{TOKEN}/sendMessage", params={"chat_id": CHAT_ID, "text": "🦅 PING: Terminale Operativo."})
        return True
    except: return False

# --- SIDEBAR (NAVIGAZIONE) ---
with st.sidebar:
    st.markdown("### 🦅 SNIPER PRO")
    st.caption("v. 5.0 | Build: Stable")
    st.markdown("---")
    
    # Menu con icone più pulite
    page = st.radio(
        "MENU OPERATIVO", 
        ["Dashboard", "Radar", "Diario", "Settings"],
        format_func=lambda x: f" {x.upper()}" # Rende tutto maiuscolo e pulito
    )
    
    st.markdown("---")
    
    # Sezione Stato rapido
    st.markdown("<div style='font-size: 11px; color: #4b5563; margin-bottom: 5px;'>SYSTEM STATUS</div>", unsafe_allow_html=True)
    c_ping, c_ind = st.columns([3, 1])
    with c_ping:
        if st.button("PING TELEGRAM", type="secondary"):
            if test_telegram_connection(): st.toast("Connesso", icon="✅")
            else: st.toast("Errore", icon="❌")
    with c_ind:
        st.markdown("🟢") # Indicatore finto "Online"

# --- PAGINA 1: DASHBOARD ---
if page == "Dashboard":
    # Header Compatto
    c_head1, c_head2 = st.columns([3, 1])
    with c_head1:
        st.markdown('<div class="header-title">WAR ROOM</div>', unsafe_allow_html=True)
        st.markdown('<div class="header-subtitle">FINANCIAL INTELLIGENCE UNIT</div>', unsafe_allow_html=True)
    with c_head2:
        st.markdown(f"<div style='text-align: right; color: #4b5563; font-size: 10px; font-family: monospace;'>{datetime.now().strftime('%d/%m %H:%M:%S')}</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    df = load_data(config.FILE_PENDING)
    
    # --- CALCOLO KPI (Logica identica a prima) ---
    profit = 0.0; active = 0; closed = 0; win_rate = 0.0; cap_exposed = 0.0
    roi = 0.0; velocity = 0.0; projected_annual = 0.0; total_staked_closed = 0.0

    if not df.empty:
        if 'Profitto_Reale' in df.columns:
            df['Profitto_Reale'] = pd.to_numeric(df['Profitto_Reale'], errors='coerce').fillna(0)
            profit = df['Profitto_Reale'].sum()
        
        if 'Stake_Euro' in df.columns:
            df['Stake_Clean'] = df['Stake_Euro'].astype(str).str.extract(r'(\d+)').astype(float).fillna(0)
        else: df['Stake_Clean'] = 0.0

        if 'Stato_Trade' in df.columns:
            active = df[df['Stato_Trade'] == 'APERTO'].shape[0]
            closed_df = df[df['Stato_Trade'].str.contains("CHIUSO", na=False)].copy()
            closed = closed_df.shape[0]
            if active > 0: cap_exposed = df[df['Stato_Trade'] == 'APERTO']['Stake_Clean'].sum()
            if closed > 0:
                wins = closed_df[closed_df['Profitto_Reale'] > 0].shape[0]
                win_rate = (wins / closed) * 100
                total_staked_closed = closed_df['Stake_Clean'].sum()
                if total_staked_closed > 0: roi = (profit / total_staked_closed) * 100
                velocity = total_staked_closed / config.BANKROLL_TOTALE
                if 'Data_Scan' in df.columns:
                    try:
                        df['Date_Obj'] = pd.to_datetime(df['Data_Scan'], errors='coerce')
                        first_date = df['Date_Obj'].min()
                        days_active = (datetime.now() - first_date).days
                        if days_active < 1: days_active = 1
                        projected_annual = ((profit / days_active) * 365) + config.BANKROLL_TOTALE
                    except: projected_annual = config.BANKROLL_TOTALE

    # --- KPI DISPLAY (COMPATTO SU 5 COLONNE) ---
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("PROFITTO", f"{profit:+.2f}€", delta="Netto")
    k2.metric("ROI %", f"{roi:.2f}%", delta="Yield")
    k3.metric("WIN RATE", f"{win_rate:.0f}%", delta=f"{closed} Ops")
    k4.metric("ESPOSIZIONE", f"{cap_exposed:.0f}€", delta=f"{active} Attivi", delta_color="off")
    k5.metric("VELOCITY", f"{velocity:.2f}x", delta="Turnover")

    st.markdown("---")

    # --- MAIN CONTENT GRID ---
    c_main_sx, c_main_dx = st.columns([2, 1])

    with c_main_sx:
        st.markdown("#### 📈 PERFORMANCE TREND")
        if closed > 0:
            closed_df = df[df['Stato_Trade'].str.contains("CHIUSO", na=False)].copy()
            closed_df['N'] = range(1, len(closed_df)+1)
            closed_df['Cum'] = closed_df['Profitto_Reale'].cumsum()
            
            # Grafico Minimalista
            fig = px.area(closed_df, x='N', y='Cum')
            fig.update_traces(line_color='#3b82f6', fillcolor='rgba(59, 130, 246, 0.1)')
            fig.update_layout(
                height=250, # Grafico basso e largo
                margin=dict(l=0, r=0, t=10, b=0), # Zero margini
                paper_bgcolor='rgba(0,0,0,0)', 
                plot_bgcolor='rgba(0,0,0,0)', 
                font_color='#6b7280',
                xaxis=dict(showgrid=False, title=None),
                yaxis=dict(showgrid=True, gridcolor='#1f2937', title=None),
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("Dati insufficienti per il grafico.")

    with c_main_dx:
        st.markdown("#### 🚀 PROIEZIONE 1Y")
        
        # Tachimetro (Gauge) Piccolo
        gauge_color = "#ef4444" 
        if roi > 0: gauge_color = "#3b82f6"
        if roi > 5: gauge_color = "#10b981"

        fig_g = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = roi,
            number = {'suffix': "%", 'font': {'size': 20, 'color': 'white'}},
            gauge = {
                'axis': {'range': [-5, 15], 'tickwidth': 0},
                'bar': {'color': gauge_color},
                'bgcolor': "rgba(0,0,0,0)",
                'borderwidth': 0,
                'threshold': {'line': {'color': "white", 'width': 2}, 'thickness': 0.75, 'value': roi}
            }
        ))
        fig_g.update_layout(height=120, margin=dict(l=10, r=10, t=20, b=0), paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_g, use_container_width=True, config={'displayModeBar': False})
        
        st.markdown(f"""
        <div style="text-align: center; background: #111827; padding: 10px; border-radius: 8px; border: 1px solid #1f2937;">
            <div style="font-size: 10px; color: #6b7280;">FORECAST</div>
            <div style="font-size: 18px; font-weight: bold; color: #38bdf8;">{projected_annual:,.0f} €</div>
        </div>
        """, unsafe_allow_html=True)

# --- PAGINA 2: RADAR ---
elif page == "Radar":
    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("🎾 SCAN TENNIS"):
            with st.spinner("Analisi Mercati..."): scanner_tennis.scan_tennis()
            st.rerun()
    with c2:
        if st.button("⚽ SCAN CALCIO"):
            with st.spinner("Analisi Mercati..."): scanner_calcio.scan_calcio()
            st.rerun()
            
    st.markdown("<br>", unsafe_allow_html=True)
    
    df = load_data(config.FILE_PENDING)
    if not df.empty:
        df_view = df[df['Stato_Trade'] == 'APERTO'] if 'Stato_Trade' in df.columns else df
        
        if not df_view.empty:
            st.markdown(f"**OPPORTUNITÀ LIVE ({len(df_view)})**")
            
            # Colonne Selezionate
            cols = ['Orario_Match', 'Match', 'Selezione', 'Quota_Ingresso', 'Target_Scalping', 'Quota_Sniper_Target', 'Stake_Euro', 'Valore_%']
            final = [c for c in cols if c in df_view.columns]
            
            # Tabella Compatta
            st.dataframe(
                df_view[final], 
                use_container_width=True, 
                hide_index=True, 
                height=350,
                column_config={
                    "Orario_Match": st.column_config.TextColumn("Ora"),
                    "Quota_Ingresso": st.column_config.NumberColumn("Quota", format="%.2f"),
                    "Target_Scalping": st.column_config.NumberColumn("Exit", format="%.2f"),
                    "Quota_Sniper_Target": st.column_config.NumberColumn("Target", format="%.2f"),
                    "Stake_Euro": st.column_config.TextColumn("Stake"),
                    "Valore_%": st.column_config.ProgressColumn("Value", min_value=0, max_value=20, format="%f")
                }
            )
        else: st.info("Radar libero. In attesa di segnali.")
    else: st.info("Nessun dato nel database.")

# --- PAGINA 3: DIARIO ---
elif page == "Diario":
    st.markdown('<div class="header-title">REGISTRO ORDINI</div>', unsafe_allow_html=True)
    df = load_data(config.FILE_PENDING)
    if not df.empty:
        edited = st.data_editor(
            df, 
            num_rows="dynamic", 
            use_container_width=True,
            height=600, # Più alta per vedere meglio
            column_config={
                "Stato_Trade": st.column_config.SelectboxColumn("Stato", options=["APERTO", "CHIUSO (Scalping)", "CHIUSO (Stop Loss)", "CHIUSO (Value Bet Vinta)", "CHIUSO (Value Bet Persa)"], required=True, width="medium"),
                "Profitto_Reale": st.column_config.NumberColumn("P/L (€)", format="%.2f €")
            }
        )
        if st.button("💾 SALVA MODIFICHE", type="primary"):
            edited.to_csv(config.FILE_PENDING, index=False)
            st.toast("Database Aggiornato!", icon="💾")
            st.rerun()
    else: st.warning("Diario vuoto.")

# --- PAGINA 4: SETTINGS ---
elif page == "Settings":
    st.markdown('<div class="header-title">SYSTEM CONFIG</div>', unsafe_allow_html=True)
    
    st.info(f"Bankroll Attuale: **{config.BANKROLL_TOTALE} €** | Stake Max: **{config.STAKE_MASSIMO} €**")
    
    c_danger, c_void = st.columns([1, 2])
    with c_danger:
        st.markdown("#### 🛑 ZONA PERICOLO")
        if st.button("🗑️ RESET TOTALE DATABASE"):
            if os.path.exists(config.FILE_PENDING): os.remove(config.FILE_PENDING)
            st.toast("Database Eliminato.", icon="🔥")
            st.rerun()
