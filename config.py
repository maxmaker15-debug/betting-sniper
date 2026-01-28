
import os

# CONFIGURAZIONE BASE
# Su Streamlit Cloud non useremo percorsi strani, ma la cartella corrente
FILE_PENDING = 'bets_pending.csv'
FILE_HISTORY = 'bets_history.csv'

# TUA API KEY (Già inserita)
API_KEY = '78f03ed8354c09f7ac591fe7e105deda' 
REGIONS = 'eu'

# PARAMETRI MONEY MANAGEMENT
BANKROLL_TOTALE = 5000.0
KELLY_FRACTION = 0.20
STAKE_MASSIMO = 150.0
COMMISSIONE_BETFAIR = 0.05

# SOGLIE STRATEGICHE
SOGLIA_VALUE_TENNIS = 0.5   # Verde
SOGLIA_SNIPER_TENNIS = -2.0 # Giallo
SOGLIA_VALUE_CALCIO = 1.5   # Verde
SOGLIA_SNIPER_CALCIO = -2.0 # Giallo
