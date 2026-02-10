# --- CONFIGURAZIONE V60 HYBRID (MASTER) ---

# 1. CREDENZIALI & API
SPORTMONKS_TOKEN = "EUVQIE2eHy4T2wsYSr3D1RuPQCFuMZLa6n0ey3Q3AtBO8GxOJFzBX1w9hlF8"
API_KEY = "78f03ed8354c09f7ac591fe7e105deda" # The-Odds-Api

# 2. GESTIONE FILE
FILE_PENDING = "radar_pending.csv"
FILE_STORICO = "registro_operazioni.csv"

# 3. MONEY MANAGEMENT
BANKROLL_TOTALE = 5000.0
COMMISSIONE_BETFAIR = 0.05 
STAKE_FISSO = 0.02 

# ---------------------------------------------------------
# 4. REGOLE DI INGAGGIO (LOGICA DI SELEZIONE)
# ---------------------------------------------------------

FILTRI_STRATEGIA = {
    # Range Quote (Concordato)
    "QUOTA_MIN": 1.50,
    "QUOTA_MAX": 3.80,
    
    # Parametri Value Bet (Per entrare a mercato)
    "VALUE_MINIMO": 0.02,    # 2% (Match READY)
    "PAREGGIO_MIN_EV": 2.5,  # 2.5% (Solo per le X)

    # Parametri "Quasi Value Bet" (Da monitorare)
    "QUASI_VALUE_MIN": -1.0, # Sotto a -1% scartiamo
    "QUASI_VALUE_MAX": 0.5,  # Fino a 0.5% è "Quasi"
    
    # Filtri Temporali
    "ORE_ANTICIPO_MIN": 1,   # Minimo 1 ora prima
    "ORE_ANTICIPO_MAX": 48,  # Massimo 48 ore prima
}
