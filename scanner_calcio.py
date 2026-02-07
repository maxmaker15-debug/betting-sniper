import requests, csv, os, config, pandas as pd
from datetime import datetime, timezone
import dateutil.parser

# --- CONFIGURAZIONE ---
API_KEY = config.API_KEY
TELEGRAM_TOKEN = "8145327630:AAHJC6vDjvGUyPT0pKw63fyW53hTl_F873U"
TELEGRAM_CHAT_ID = "5562163433"

COMPETIZIONI_ELITE = [
    'soccer_italy_serie_a', 'soccer_italy_serie_b',
    'soccer_england_premier_league', 'soccer_england_championship',
    'soccer_spain_la_liga', 'soccer_spain_segunda_division',
    'soccer_germany_bundesliga', 'soccer_germany_bundesliga2',
    'soccer_france_ligue_one', 'soccer_france_ligue_two',
    'soccer_netherlands_eredivisie', 'soccer_portugal_primeira_liga',
    'soccer_uefa_champions_league', 'soccer_uefa_europa_league'
]

MIN_ODDS = 1.70
MAX_ODDS = 4.00
MIN_EV_SAVE = -2.0
MIN_EV_NOTIFY = 1.0

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try: requests.get(url, params={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
    except: pass

def converti_orario(iso_date):
    try: return dateutil.parser.parse(iso_date).strftime("%Y-%m-%d %H:%M")
    except: return iso_date

def calcola_quota_reale_pinnacle(odds_dict):
    try:
        inverses = [1/p for p in odds_dict.values()]
        margin = sum(inverses)
        real_probs = {k: (1/v)/margin for k, v in odds_dict.items()}
        return real_probs
    except: return {}

def calcola_stake_value(ev_perc, quota):
    try:
        if ev_perc < 1.0: return 0 
        if ev_perc < 2.5: return 50
        if ev_perc < 5.0: return 100
        return config.STAKE_MASSIMO
    except: return 0

def scan_calcio():
    print(f"--- ⚽ SCANSIONE CALCIO (V31 STRICT) - {datetime.now()} ---")
    
    # Header corretto e allineato con l'App V31
    header = ['Sport', 'Data_Scan', 'Orario_Match', 'Torneo', 'Match', 'Selezione', 'Quota_Betfair', 'Quota_Reale_Pinna', 'Valore_%', 'Stake_Euro', 'Stato_Trade', 'Esito_Finale', 'Profitto_Reale']
    
    # Se il file non esiste o è corrotto, lo ricrea
    mode = 'a'
    if not os.path.exists(config.FILE_PENDING):
        mode = 'w'
    
    # Scrittura CSV Blindata (Delimiter virgola)
    f = open(config.FILE_PENDING, mode, newline='', encoding='utf-8')
    writer = csv.writer(f, delimiter=',') # FORZA VIRGOLA
    
    if mode == 'w':
        writer.writerow(header)

    try:
        resp = requests.get('https://api.the-odds-api.com/v4/sports', params={'apiKey': API_KEY})
        soccer_leagues = [s for s in resp.json() if s['key'] in COMPETIZIONI_ELITE]
        now_utc = datetime.now(timezone.utc)

        for league in soccer_leagues:
            url = f'https://api.the-odds-api.com/v4/sports/{league["key"]}/odds'
            resp = requests.get(url, params={'apiKey': API_KEY, 'regions': 'eu', 'markets': 'h2h', 'oddsFormat': 'decimal'})
            if resp.status_code != 200: continue
            
            events = resp.json()
            for event in events:
                try:
                    if dateutil.parser.parse(event['commence_time']) <= now_utc: continue 
                except: continue

                home, away = event['home_team'], event['away_team']
                match_name = f"{home} vs {away}"
                
                pinna_odds_raw = {}
                betfair_odds_raw = {}
                
                for b in event['bookmakers']:
                    if b['key'] == 'pinnacle':
                        for o in b['markets'][0]['outcomes']: pinna_odds_raw[o['name']] = o['price']
                    if 'betfair' in b['title'].lower():
                        for o in b['markets'][0]['outcomes']: betfair_odds_raw[o['name']] = o['price']
                
                if not pinna_odds_raw or not betfair_odds_raw: continue

                real_probs = calcola_quota_reale_pinnacle(pinna_odds_raw)
                if not real_probs: continue

                for sel_name, bf_price in betfair_odds_raw.items():
                    if sel_name not in real_probs: continue
                    if not (MIN_ODDS <= bf_price <= MAX_ODDS): continue
                    
                    bf_netto = 1 + ((bf_price - 1) * (1 - config.COMMISSIONE_BETFAIR))
                    true_prob = real_probs[sel_name]
                    fair_odds = 1 / true_prob
                    
                    ev = (true_prob * bf_netto) - 1
                    ev_perc = round(ev * 100, 2)
                    
                    if ev_perc >= MIN_EV_SAVE:
                        print(f"🔎 TROVATO: {match_name} -> EV {ev_perc}%")
                        
                        stake = calcola_stake_value(ev_perc, bf_price)
                        stato = "VALUE" if ev_perc >= MIN_EV_NOTIFY else "WATCH"
                        
                        # SCRITTURA RIGA (Ordine esatto delle colonne)
                        writer.writerow([
                            'CALCIO', 
                            datetime.now().strftime("%Y-%m-%d %H:%M"), 
                            converti_orario(event['commence_time']), 
                            league['title'], 
                            match_name, 
                            sel_name, 
                            bf_price,               # Quota Betfair
                            round(fair_odds, 2),    # Quota Reale Pinna
                            ev_perc,                # Valore % (Numero puro)
                            stake,                  # Stake
                            stato,                  # Stato
                            '', ''                  # Colonne vuote finali
                        ])
                        
                        if ev_perc >= MIN_EV_NOTIFY:
                            msg = (
                                f"🟢 VALUE BET CALCIO: {sel_name}\n"
                                f"⚽ {match_name}\n"
                                f"📊 BF: {bf_price} | 🎯 REAL: {round(fair_odds, 2)}\n"
                                f"📈 EV: +{ev_perc}%\n"
                                f"💰 Stake: {stake}€"
                            )
                            send_telegram(msg)
    except Exception as e: print(f"Errore Calcio: {e}")
    finally:
        f.close()

if __name__ == "__main__":
    scan_calcio()
