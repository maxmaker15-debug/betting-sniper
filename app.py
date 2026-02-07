import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import subprocess
import sys
import config

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="Sniper Betting Suite",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS 2026 (LAYOUT FIX & DARK MODE) ---
st.markdown("""
    <link href="https://cdn.jsdelivr.net/npm/remixicon@3.5.0/fonts/remixicon.css" rel="stylesheet">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap');
        
        .stApp {
            background-color: #080808;
            font-family: 'Inter', sans-serif;
        }

        /* FIX IMPAGINAZIONE */
        .block-container {
            padding-top: 3.5rem !important; 
            padding-bottom: 3rem !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
        }

        /* CARD STYLE */
        div[data-testid="stMetric"], div[data-testid="stDataFrame"], div[data-testid="stPlotlyChart"] {
            background-color: #121212;
            border: 1px solid #333;
            border-radius: 6px;
            padding: 12px 15px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.4);
            transition: border-color 0.3s ease;
        }
        div[data-testid="stMetric"]:hover { border-color: #555; }

        /* TITOLI */
        h1, h2, h3 { color: #fff; font-weight: 700; margin-bottom: 10px; }
        
        /* METRICHE */
        div[data-testid="stMetricValue"] {
            font-size: 1.8rem !important;
            color: #00E096 !important;
            font-weight: 700;
        }
        div[data-testid="stMetricLabel"] {
            color: #777;
            font-size: 0.8rem;
            text-transform: uppercase;
            font-weight: 500;
        }

        /* SIDEBAR */
        section[data-testid="stSidebar"] { background-color: #0b0b0b; border-right: 1px solid #222; }
        
        /* PULSANTI */
        .stButton button {
            background-color: #1a1a1a;
            color: #ddd;
            border: 1px solid #333;
            border-radius: 4px;
            text-transform: uppercase;
            font-weight: 600;
            padding: 0.5rem 1rem;
            width: 100%;
        }
        .stButton button:hover { border-color: #00E096; color: #00E096; }

        /* HEADER LOGO */
        .header-logo {
            font-size: 1
