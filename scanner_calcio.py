import requests, csv, os, config, pandas as pd
from datetime import datetime, timezone
import dateutil.parser

# --- CONFIGURAZIONE ---
API_KEY = config.API_KEY
TELEGRAM_TOKEN = "8145327630:AAHJC6vDjvGUyPT0pKw63fyW53hTl_F873U"
TELEGRAM_CHAT_ID = "5562163433"

# --- WHITELIST CAMPIONATI (Alta Liquidità per Value Bet) ---
COMPETIZIONI_ELITE = [
    'soccer_italy_serie_a', 'soccer_italy_serie_b',
    'soccer_england_premier_league', 'soccer_england_championship',
    'soccer_spain_la_liga', 'soccer_spain_segunda_division',
    'soccer_germany_bundesliga', 'soccer_germany_bundesliga2',
    'soccer_france_ligue_one', 'soccer_france_ligue_two',
    'soccer_netherlands_eredivisie', 'soccer_portugal_primeira_liga',
    'soccer_uefa_champions_league', 'soccer_uefa_europa_league'
]

# --- PARAMETRI FILTRO ---
MIN_ODDS = 1.70
MAX_ODDS = 3.50
MIN_EV = -10.0  # Mostrami tutto, anche se perdo soldi matematicamente

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try: requests.get(url, params={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
    except: pass

def converti_orario(iso_date):
    try: return dateutil.parser.parse(iso_date).strftime("%Y-%m-%d %H:%M")
    except: return iso_date

def calcola_quota_reale_pinnacle(odds_dict):
    """
    Rimuove il margine (Vig) di Pinnacle per trovare la probabilità reale.
    """
    try:
        inverses = []
        outcomes = []
        for name, price in odds_dict.items():
            inverses.append(1/price)
            outcomes.append(name)
        
        margin = sum(inverses) # Es. 1.04
        
        real_probs = {}
        for i, name in enumerate(outcomes):
            # Normalizziamo la probabilità
            raw_prob = inverses[i]
            true_prob = raw_prob / margin
            real_probs[name] = true_prob
            
        return real_probs
    except:
        return {}

def calcola_stake_value(ev_perc, quota):
    """
    Calcola lo stake in base alla forza del valore (EV).
    EV 1-3% -> Stake Medio
    EV >3% -> Stake Massimo
    """
    try:
        # Base: Kelly Frazionario (molto conservativo per Value Betting puro)
        # Ma qui usiamo una logica a gradini come richiesto
        stake = 0
        
        if ev_perc < 2.0:
            stake = 50 # Assaggio
        elif ev_perc < 5.0:
            stake = 100 # Colpo solido
        else:
            stake = config.STAKE_MASSIMO # 150€ (Occasione d'oro)
            
        # Limiti sicurezza
        if stake > config.STAKE_MASSIMO: stake = config.STAKE_MASSIMO
        return int(stake)
    except: return 0

def scan_calcio():
    print(f"--- ⚽ SCANSIONE CALCIO (V20 VALUE SNIPER) - {datetime.now()} ---")
    
    # Header CSV aggiornato per Value Betting
    header = ['Sport', 'Data_Scan', 'Orario_Match', 'Torneo', 'Match', 'Selezione', 'Quota_Betfair', 'Quota_Reale_Pinna', 'Valore_%', 'Stake_Euro', 'Stato_Trade', 'Esito_Finale', 'Profitto_Reale']
    
    if not os.path.exists(config.FILE_PENDING):
        with open(config.FILE_PENDING, 'w', newline='', encoding='utf-8') as f: csv.writer(f).writerow(header)

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
                
                # 1. Cerca quote Pinnacle
                pinna_odds_raw = {}
                betfair_odds_raw = {}
                
                for b in event['bookmakers']:
                    if b['key'] == 'pinnacle':
                        for o in b['markets'][0]['outcomes']: pinna_odds_raw[o['name']] = o['price']
                    if 'betfair' in b['title'].lower():
                        for o in b['markets'][0]['outcomes']: betfair_odds_raw[o['name']] = o['price']
                
                if not pinna_odds_raw or not betfair_odds_raw: continue

                # 2. Calcola Quote Reali (No Margin) da Pinnacle
                real_probs = calcola_quota_reale_pinnacle(pinna_odds_raw)
                if not real_probs: continue

                # 3. Confronta con Betfair
                for sel_name, bf_price in betfair_odds_raw.items():
                    if sel_name not in real_probs: continue
                    
                    # FILTRO RANGE (1.70 - 3.50)
                    if not (MIN_ODDS <= bf_price <= MAX_ODDS): continue
                    
                    # Calcolo EV su Betfair NETTO
                    bf_netto = 1 + ((bf_price - 1) * (1 - config.COMMISSIONE_BETFAIR))
                    true_prob = real_probs[sel_name]
                    fair_odds = 1 / true_prob
                    
                    # Expected Value %
                    ev = (true_prob * bf_netto) - 1
                    ev_perc = round(ev * 100, 2)
                    
                    if ev_perc >= MIN_EV:
                        print(f"🔥 VALUE BET TROVATA: {match_name} -> {sel_name} (EV {ev_perc}%)")
                        
                        stake = calcola_stake_value(ev_perc, bf_price)
                        
                        # Salvataggio
                        with open(config.FILE_PENDING, 'a', newline='', encoding='utf-8') as f:
                            # Nota: Colonne adattate per Value Betting (Target Scalping rimosso o messo a 0)
                            csv.writer(f).writerow(['CALCIO', datetime.now().strftime("%Y-%m-%d %H:%M"), converti_orario(event['commence_time']), league['title'], match_name, sel_name, bf_price, round(fair_odds, 2), f"{ev_perc}", stake, 'APERTO', '', ''])
                        
                        # Telegram
                        msg = (
                            f"🟢 VALUE BET CALCIO: {sel_name}\n"
                            f"⚽ {match_name}\n"
                            f"🏆 {league['title']}\n"
                            f"📊 QUOTA BETFAIR: {bf_price}\n"
                            f"🎯 QUOTA REALE (Pinna): {round(fair_odds, 2)}\n"
                            f"📈 EV: +{ev_perc}%\n"
                            f"💰 STAKE CONSIGLIATO: {stake}€\n"
                            f"⚠️ Strategia: Buy & Hold (No Cashout)"
                        )
                        send_telegram(msg)

    except Exception as e: print(f"Errore Calcio: {e}")

if __name__ == "__main__":
    scan_calcio()
