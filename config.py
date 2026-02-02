# --- CONFIGURAZIONE GENERALE SNIPER PRO ---

# 1. CHIAVI DI ACCESSO & COMUNICAZIONE
# Inserite direttamente per evitare errori di lettura
API_KEY = "78f03ed8354c09f7ac591fe7e105deda"
TELEGRAM_TOKEN = "8145327630:AAHJC6vDjvGUyPT0pKw63fyW53hTl_F873U"
TELEGRAM_CHAT_ID = "5562163433"

# 2. GESTIONE BANKROLL (MONEY MANAGEMENT AVANZATO)
BANKROLL_TOTALE = 5000.0   # Capitale Totale Disponibile
STAKE_MASSIMO = 150.0      # HARD CAP: Non puntare mai più di 150€ (3%) su una singola bet

# MOLTIPLICATORE KELLY
# 0.2 = Conservativo (20% del suggerimento matematico)
# 0.5 = Aggressivo (50% del suggerimento)
# 1.0 = KELLY PURO (100% del suggerimento - Massimizza la crescita, limitato solo dallo STAKE_MASSIMO)
KELLY_FRACTION = 1.0       

COMMISSIONE_BETFAIR = 0.05 # Commissione Exchange (Standard 5%)

# 3. SOGLIE OPERATIVE (STRATEGIA)
# Quando il sistema deve segnalare un'opportunità?

# CALCIO
SOGLIA_VALUE_CALCIO = 1.5   # Se il vantaggio è > 1.5%, è VERDE (Value Bet)
SOGLIA_SNIPER_CALCIO = 0.5  # Se il vantaggio è tra 0.5% e 1.5%, è GIALLO (Attesa)

# TENNIS (Richiede margini leggermente più alti per la volatilità)
SOGLIA_VALUE_TENNIS = 2.0   # Se il vantaggio è > 2.0%, è VERDE (Value Bet)
SOGLIA_SNIPER_TENNIS = 1.0  # Se il vantaggio è tra 1.0% e 2.0%, è GIALLO (Attesa)

# 4. PARAMETRI DI SISTEMA (NON TOCCARE)
FILE_PENDING = "trades_pending.csv"  # Database operazioni aperte
REGIONS = 'eu'                       # Regione Bookmakers
