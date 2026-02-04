import requests, csv, os, config, pandas as pd
from datetime import datetime, timezone
import dateutil.parser

# --- ⚠️ CONFIGURAZIONE DIRETTA ---
API_KEY = "78f03ed8354c09f7ac591fe7e105deda" # La tua chiave PRO
TELEGRAM_TOKEN = "8145327630:AAHJC6vDjvGUyPT0pKw63fyW53hTl_F873U"
TELEGRAM_CHAT_ID = "5562163433"

# --- PARAMETRI TATTICI ---
REGIONS = 'eu'
MARKETS = 'h2h'
ODDS_FORMAT = 'decimal'
MAX_ODDS_CAP = 5.00 

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try: requests.get(url, params={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
    except: pass

def converti_orario(iso_date):
    try: return dateutil.parser.parse(iso_date).strftime("%Y-%m-%d %H:%M")
    except: return iso_date

def scan_tennis():
    print(f"--- 🚀 SCANSIONE TENNIS (DEBUG MODE) - {datetime.now()} ---")
    
    # 1. TEST DI CONNESSIONE E LISTA SPORT
    print("📡 Richiesta lista sport all'API (Parametro all=true)...")
    
    # FORZIAMO LA VISUALIZZAZIONE DI TUTTI GLI SPORT
    url_sports = 'https://api.the-odds-api.com/v4/sports'
    try:
        resp = requests.get(url_sports, params={'apiKey': API_KEY, 'all': 'true'})
        
        if resp.status_code != 200:
            print(f"❌ ERRORE RISPOSTA API: {resp.status_code}")
            print(f"MESSAGGIO: {resp.text}")
            return
        
        data = resp.json()
        print(f"✅ Connessione OK. L'API ha restituito {len(data)} sport totali.")
        
        # DEBUG: Stampiamo i primi 5 sport trovati per vedere se il formato è giusto
        print(f"Esempio dati ricevuti: {[s['key'] for s in data[:5]]}")

        # FILTRO TENNIS
        active_tennis = [s for s in data if 'tennis' in s['key'] and 'winner' not in s['key']]
        print(f"🎾 TORNEI TENNIS IDENTIFICATI: {len(active_tennis)}")
        
        if len(active_tennis) == 0:
            print("⚠️ ATTENZIONE: Nessun torneo contiene la parola 'tennis' nella chiave!")
            print("Ecco tutte le chiavi trovate (per controllo):")
            print([s['key'] for s in data])
            return

        # Elenco dei tornei trovati
        print(f"Tornei trovati: {[t['title'] for t in active_tennis]}")

        # 2. ANALISI DEI MATCH
        match_analizzati = 0
        now_utc = datetime.now(timezone.utc)

        for torneo in active_tennis:
            # print(f"🔍 Controllo {torneo['title']}...")
            url_odds = f'https://api.the-odds-api.com/v4/sports/{torneo["key"]}/odds'
            resp_odds = requests.get(url_odds, params={'apiKey': API_KEY, 'regions': REGIONS, 'markets': MARKETS, 'oddsFormat': ODDS_FORMAT})
            
            if resp_odds.status_code != 200: continue
            
            events = resp_odds.json()
            for event in events:
                # CHECK LIVE E DATA
                try:
                    commence_time = dateutil.parser.parse(event['commence_time'])
                    if commence_time <= now_utc: continue 
                except: continue

                match_analizzati += 1
                
                # --- LOGICA SEMPLIFICATA PER TEST ---
                # Qui controlliamo solo se trova Pinnacle e Betfair
                bookies = [b['key'] for b in event['bookmakers']]
                if 'pinnacle' in bookies and 'betfair_ex_eu' in bookies:
                    print(f"⚡ MATCH VALIDO TROVATO: {event['home_team']} vs {event['away_team']}")
                    # (Qui omettiamo il calcolo complesso per ora, vogliamo solo vedere se 'vede' i match)

        print(f"🏁 DIAGNOSTICA COMPLETATA. Match pre-live scansionati: {match_analizzati}")

    except Exception as e:
        print(f"❌ ERRORE CRITICO PYTHON: {e}")

if __name__ == "__main__":
    scan_tennis()
