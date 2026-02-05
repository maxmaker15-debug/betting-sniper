## --- CONFIGURAZIONE GENERALE ---
API_KEY = "78f03ed8354c09f7ac591fe7e105deda"

# Nomi dei File Database
FILE_PENDING = "pending_trades.csv"
FILE_STORICO = "storico_trades.csv"

# --- GESTIONE BANKROLL ---
BANKROLL_TOTALE = 1000      # Il tuo capitale totale (aggiornalo se cresce)
KELLY_FRACTION = 1.0        # 1.0 = Kelly Puro (Aggressivo), 0.5 = Mezzo Kelly (Conservativo)

# Limiti di Sicurezza Stake
STAKE_MASSIMO = 50          # Non punterà mai più di 50€ su un singolo colpo
STAKE_MINIMO = 2            # Se il calcolo dà meno di 2€, ignora

# Parametri Piattaforma
COMMISSIONE_BETFAIR = 0.05  # 5% (Standard)

# --- PARAMETRI TATTICI (Soglie di Allerta) ---

# CALCIO
# Se il vantaggio matematico > 3% -> VERDE (Stake Consigliato)
# Se il vantaggio matematico > 0.5% -> GIALLO (Monitorare/AsianOdds)
SOGLIA_VALUE_CALCIO = 3.0
SOGLIA_SNIPER_CALCIO = 0.5

# TENNIS
# Se il vantaggio matematico > 2% -> VERDE (Stake Consigliato)
# Se il vantaggio matematico > 0.5% -> GIALLO (Monitorare)
SOGLIA_VALUE_TENNIS = 2.0
SOGLIA_SNIPER_TENNIS = 0.5 Regione Bookmakers
