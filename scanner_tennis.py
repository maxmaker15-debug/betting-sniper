import requests, csv, os, config, json
from datetime import datetime, timezone
import dateutil.parser

# --- CONFIGURAZIONE COMMANDER V41 ---
API_KEY = config.API_KEY
TELEGRAM_TOKEN = "8145327630:AAHJC6vDjvGUyPT0pKw63fyW53hTl_F873U"
TELEGRAM_CHAT_ID = "5562163433"
FILE_MEMORY = "odds_memory_tennis.json" # Memoria separata per il Tennis

BANKROLL = 5000.0
MAX_STAKE_PERC = 0.02
MIN_STAKE_EURO = 10.0
KELLY_FRACTION = 0.20

# TENNIS: Range più ampio
MIN_ODDS = 1.40
MAX_ODDS = 6.00
TARGET_ROI = 0.025

COMPETIZIONI_ELITE_TENNIS = [
    'tennis_atp_australian_open', 'tennis_wta_australian_open',
    'tennis_atp_french_open', 'tennis_wta_french_open',
    'tennis_atp_wimbledon', 'tennis_wta_wimbledon',
    'tennis_atp_us_open', 'tennis_wta_us_open',
    'tennis_atp_masters_1000', 'tennis_wta_1000'
]

# --- GESTIONE MEMORIA ---
def load_memory():
    if not os.path.exists(FILE_MEMORY): return {}
    try:
        with open(FILE_MEMORY, 'r') as f: return json.load(f)
    except: return {}

def save_memory(data):
    try:
        with open(FILE_MEMORY, 'w') as f: json.dump(data, f)
    except: pass

def send_telegram(msg):
    try: requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", params={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
    except: pass

def converti_orario(iso_date):
    try: return dateutil.parser.parse(iso_date).strftime("%Y-%m-%d %H:%M")
    except: return iso_date

def get_fair_odds_pinnacle(odds_dict):
    try:
        inverses = [1/p for p in odds_dict.values()]
        margin = sum(inverses)
        return {k: (1/v)/margin for k, v in odds_dict.items()}
    except: return {}

def calcola_kelly_stake(true_prob, quota_bf):
    try:
        if quota_bf <= 1.01: return 0
        quota_netta = 1 + ((quota_bf - 1) * (1 - config.COMMISSIONE_BETFAIR))
        b = quota_netta - 1
        p = true_prob
        q = 1 - p
        full_kelly = (b * p - q) / b
        if full_kelly <= 0: return 0
        stake_euro = min(BANKROLL * full_kelly * KELLY_FRACTION, BANKROLL * MAX_STAKE_PERC)
        return int(stake_euro) if stake_euro >= MIN_STAKE_EURO else 0
    except: return 0

def calcola_target_buy(true_prob):
    try:
        target_net = (1 + TARGET_ROI) / true_prob
        return round(((target_net - 1) / (1 - config.COMMISSIONE_BETFAIR)) + 1, 2)
    except: return 0.0

def scan_tennis():
    print(f"--- 🎾 TENNIS V41 TREND HUNTER - {datetime.now()} ---")
    
    # Header Allineato con Calcio e App
    header = ['Sport', 'Data', 'Ora', 'Torneo', 'Match', 'Selezione', 'Q_Betfair', 'Q_Target', 'Q_Reale', 'EV_%', 'Stake_Ready', 'Stake_Limit', 'Trend', 'Stato', 'Esito', 'Profitto']
    
    history = load_memory()
    new_history = {}

    # Append mode 'a' per non cancellare i dati del calcio appena scritti
    mode = 'a'
    if not os.path.exists(config.FILE_PENDING): mode = 'w'
    
    with open(config.FILE_PENDING, mode, newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if mode == 'w': writer.writerow(header)

        try:
            resp = requests.get('https://api.the-odds-api.com/v4/sports', params={'apiKey': API_KEY})
            leagues = [s for s in resp.json() if s['key'] in COMPETIZIONI_ELITE_TENNIS]
            now_utc = datetime.now(timezone.utc)

            for league in leagues:
                resp = requests.get(f'https://api.the-odds-api.com/v4/sports/{league["key"]}/odds', 
                                  params={'apiKey': API_KEY, 'regions': 'eu', 'markets': 'h2h', 'oddsFormat': 'decimal'})
                if resp.status_code != 200: continue
                
                for event in resp.json():
                    try:
                        if dateutil.parser.parse(event['commence_time']) <= now_utc: continue
                    except: continue

                    match_id = event['id']
                    match_name = f"{event['home_team']} vs {event['away_team']}"
                    
                    pinna_odds, bf_odds = {}, {}
                    for b in event['bookmakers']:
                        if b['key'] == 'pinnacle':
                            for o in b['markets'][0]['outcomes']: pinna_odds[o['name']] = o['price']
                        if 'betfair' in b['title'].lower():
                            for o in b['markets'][0]['outcomes']: bf_odds[o['name']] = o['price']
                    
                    if not pinna_odds or not bf_odds: continue
                    
                    # Salva memoria per trend
                    new_history[match_id] = pinna_odds

                    real_probs = get_fair_odds_pinnacle(pinna_odds)
                    if not real_probs: continue

                    match_best = None

                    for sel, bf_price in bf_odds.items():
                        if sel not in real_probs: continue
                        if not (MIN_ODDS <= bf_price <= MAX_ODDS): continue
                        
                        true_p = real_probs[sel]
                        real_odd = round(1/true_p, 2)
                        
                        bf_net =
