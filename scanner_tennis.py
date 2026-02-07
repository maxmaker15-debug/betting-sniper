import requests, csv, os, config, pandas as pd
from datetime import datetime, timezone
import dateutil.parser

# --- CONFIGURAZIONE ---
API_KEY = config.API_KEY
TELEGRAM_TOKEN = "8145327630:AAHJC6vDjvGUyPT0pKw63fyW53hTl_F873U"
TELEGRAM_CHAT_ID = "5562163433"

# --- WHITELIST TENNIS (Solo ATP/WTA Major per liquidità) ---
COMPETIZIONI_ELITE = [
    'tennis_atp_australian_open', 'tennis_wta_australian_open',
    'tennis_atp_french_open', 'tennis_wta_french_open',
    'tennis_atp_wimbledon', 'tennis_wta_wimbledon',
    'tennis_atp_us_open', 'tennis_wta_us_open',
    'tennis_atp_masters_1000', 'tennis_wta_1000'
]

# --- PARAMETRI FILTRO ---
MIN_ODDS = 1.70
MAX_ODDS = 3.50
MIN_EV = 1.0 

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try: requests.get(url, params={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
    except: pass

def converti_orario(iso_date):
    try: return dateutil.parser.parse(iso_date).strftime("%Y-%m-%d %H:%M")
    except: return iso_date

def calcola_quota_reale_pinnacle(odds_dict):
    try:
        inverses = []
        outcomes = []
        for name, price in odds_dict.items():
            inverses.append(1/price)
            outcomes.append(name)
        
        margin = sum(inverses)
        
        real_probs = {}
        for i, name in enumerate(outcomes):
            true_prob = inverses[i] / margin
            real_probs[name] = true_prob
            
        return real_probs
    except: return {}

def calcola_stake_value(ev_perc, quota):
    try:
        stake = 0
        if ev_perc < 2.0: stake = 50 
        elif ev_perc < 5.0: stake = 100 
        else: stake = config.STAKE_MASSIMO 
            
        if stake > config.STAKE_MASSIMO: stake = config.STAKE_MASSIMO
        return int(stake)
    except: return 0

def scan_tennis():
    print(f"--- 🎾 SCANSIONE TENNIS (V20 VALUE SNIPER) - {datetime.now()} ---")
    
    header = ['Sport', 'Data_Scan', 'Orario_Match', 'Torneo', 'Match', 'Selezione', 'Quota_Betfair', 'Quota_Reale_Pinna', 'Valore_%', 'Stake_Euro', 'Stato_Trade', 'Esito_Finale', 'Profitto_Reale']
    
    if not os.path.exists(config.FILE_PENDING):
        with open(config.FILE_PENDING, 'w', newline='', encoding='utf-8') as f: csv.writer(f).writerow(header)

    try:
        resp = requests.get('https://api.the-odds-api.com/v4/sports', params={'apiKey': API_KEY})
        tennis_leagues = [s for s in resp.json() if 'tennis' in s['key'] and ('atp' in s['key'] or 'wta' in s['key'])] # Filtro generico ATP/WTA

        now_utc = datetime.now(timezone.utc)

        for league in tennis_leagues:
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

                # Calcolo Reale
                real_probs = calcola_quota_reale_pinnacle(pinna_odds_raw)
                if not real_probs: continue

                for sel_name, bf_price in betfair_odds_raw.items():
                    if sel_name not in real_probs: continue
                    
                    # FILTRO RANGE (1.70 - 3.50)
                    if not (MIN_ODDS <= bf_price <= MAX_ODDS): continue
                    
                    bf_netto = 1 + ((bf_price - 1) * (1 - config.COMMISSIONE_BETFAIR))
                    true_prob = real_probs[sel_name]
                    fair_odds = 1 / true_prob
                    
                    ev = (true_prob * bf_netto) - 1
                    ev_perc = round(ev * 100, 2)
                    
                    if ev_perc >= MIN_EV:
                        print(f"🔥 VALUE TENNIS: {match_name} -> {sel_name} (EV {ev_perc}%)")
                        
                        stake = calcola_stake_value(ev_perc, bf_price)
                        
                        with open(config.FILE_PENDING, 'a', newline='', encoding='utf-8') as f:
                            csv.writer(f).writerow(['TENNIS', datetime.now().strftime("%Y-%m-%d %H:%M"), converti_orario(event['commence_time']), league['title'], match_name, sel_name, bf_price, round(fair_odds, 2), f"{ev_perc}", stake, 'APERTO', '', ''])
                        
                        msg = (
                            f"🎾 VALUE BET TENNIS: {sel_name}\n"
                            f"🏟️ {match_name}\n"
                            f"🏆 {league['title']}\n"
                            f"📊 QUOTA BETFAIR: {bf_price}\n"
                            f"🎯 QUOTA REALE: {round(fair_odds, 2)}\n"
                            f"📈 EV: +{ev_perc}%\n"
                            f"💰 STAKE: {stake}€\n"
                            f"⚠️ Strategia: Buy & Hold"
                        )
                        send_telegram(msg)

    except Exception as e: print(f"Errore Tennis: {e}")

if __name__ == "__main__":
    scan_tennis()
