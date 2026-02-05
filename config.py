# --- CONFIGURAZIONE GENERALE ---
API_KEY = "78f03ed8354c09f7ac591fe7e105deda"

# Nomi dei File Database
FILE_PENDING = "pending_trades.csv"
FILE_STORICO = "storico_trades.csv"

# --- GESTIONE BANKROLL ---
BANKROLL_TOTALE = 1000      # Capitale Totale
KELLY_FRACTION = 1.0        # Aggressività Standard

# Limiti di Sicurezza Stake
STAKE_MASSIMO = 150         # ⬆️ ALZATO A 150€ (Il tuo nuovo tetto)
STAKE_MINIMO = 5            # Alziamo anche il minimo per ignorare le briciole

# Parametri Piattaforma
COMMISSIONE_BETFAIR = 0.05  # 5%

# --- PARAMETRI TATTICI ---
# CALCIO ELITE
SOGLIA_VALUE_CALCIO = 3.0   # Verde (>3%)
SOGLIA_SNIPER_CALCIO = 0.1  # Giallo (>0.1%)

# TENNIS
SOGLIA_VALUE_TENNIS = 2.0
SOGLIA_SNIPER_TENNIS = 0.5
