# --- CONFIGURAZIONE GENERALE ---
API_KEY = "78f03ed8354c09f7ac591fe7e105deda"

# Nomi dei File Database
FILE_PENDING = "pending_trades.csv"
FILE_STORICO = "storico_trades.csv"

# --- GESTIONE BANKROLL ---
BANKROLL_TOTALE = 1000      # Il tuo capitale totale
KELLY_FRACTION = 1.0        # 1.0 = Aggressivo, 0.5 = Conservativo

# Limiti di Sicurezza Stake
STAKE_MASSIMO = 50          # Tetto massimo per singola bet
STAKE_MINIMO = 2            # Sotto questa cifra non scommette

# Parametri Piattaforma
COMMISSIONE_BETFAIR = 0.05  # 5%

# --- PARAMETRI TATTICI (Soglie di Allerta) ---

# CALCIO (Modalità Elite)
# VALUE (Verde): Solo occasioni matematiche forti (>3%) per lo stake automatico.
# SNIPER (Giallo): Radar impostato a 0.1%. Ti avvisa di QUALSIASI vantaggio matematico sui top campionati.
SOGLIA_VALUE_CALCIO = 3.0
SOGLIA_SNIPER_CALCIO = 0.1

# TENNIS (Modalità Standard)
# In attesa dei tornei big, manteniamo soglie bilanciate.
SOGLIA_VALUE_TENNIS = 2.0
SOGLIA_SNIPER_TENNIS = 0.5
