import requests, csv, os, config, json
from datetime import datetime, timezone
import dateutil.parser

# --- CONFIGURAZIONE V49 ---
API_KEY = config.API_KEY
TELEGRAM_TOKEN = "8145327630:AAHJC6vDjvGUyPT0pKw63fyW53hTl_F873U"
TELEGRAM_CHAT_ID = "5562163433"
FILE_MEMORY = "odds_memory_calcio.json"

BANKROLL = 5000.0
MAX_STAKE_PERC = 0.02
MIN_STAKE_EURO = 10.0   
KELLY_FRACTION = 0.30   

# --- RANGE QUOTE (Wide Spectrum) ---
MIN_ODDS = 1.45  
MAX_ODDS = 5.50  

# --- SOGLIE STANDARD (1 o 2) ---
STD_EV_VALUE = 1.5      
STD_EV_WATCH = -1.5     

# --- SOGLIE PAREGGI (X) ---
DRAW_EV_VALUE = 2.5     # Molto più severi per considerare VALUE un pareggio
DRAW_EV_WATCH = 1.5     # Ignoriamo i pareggi sotto l'1.5%

COMPETIZIONI_ELITE = [
    'soccer_italy_serie_a', 'soccer_italy_serie_b',
    'soccer_england_premier_league', 'soccer_england_championship',
    'soccer_spain_la_liga', 'soccer_germany_bundesliga',
    'soccer_france_ligue_one', 'soccer_uefa_champions_league', 
    'soccer_uefa_europa_league', 'soccer_netherlands_eredivisie', 
    'soccer_portugal_primeira_liga'
]

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

def calcola_kelly_stake(true_prob, quota_bf, trend_modifier=1.0):
    try:
        if quota_bf <= 1.01: return 0
        quota_netta = 1 + ((quota_bf - 1) * (1 - config.COMMISSIONE_BETFAIR))
        b = quota_netta - 1
        p = true_prob
        q = 1 - p
        full_kelly = (b * p - q) / b
        
        if full_kelly <= 0: return 0
        
        adjusted_fraction = KELLY_FRACTION * trend_modifier
        stake_euro = BANKROLL * full_kelly * adjusted_fraction
        stake_euro = min(stake_euro, BANKROLL * MAX_STAKE_PERC)
        
        return int(stake_euro) if stake_euro >= MIN_STAKE_EURO else 0
    except: return 0

def calcola_target_buy(true_prob):
    try:
        target_roi = 0.025
        target_net = (1 + target_roi) / true_prob
        return round(((target_net - 1) / (1 - config.COMMISSIONE_BETFAIR)) + 1, 2)
    except: return 0.0

def scan_calcio():
    print(f"--- ⚽ CALCIO V49 DRAW FILTER - {datetime.now()} ---")
    
    header = ['Sport', 'Data', 'Ora', 'Torneo', 'Match', 'Selezione', 'Q_Betfair', 'Q_Target', 'Q_Reale', 'EV_%', 'Stake_Ready', 'Stake_Limit', 'Trend', 'Stato', 'Esito', 'Profitto']
    
    history = load_memory()
    new_history = {}
    
    with open(config.FILE_PENDING, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(header)

    try:
        resp = requests.get('https://api.the-odds-api.com/v4/sports', params={'apiKey': API_KEY})
        leagues = [s for s in resp.json() if s['key'] in COMPETIZIONI_ELITE]
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
                new_history[match_id] = pinna_odds
                real_probs = get_fair_odds_pinnacle(pinna_odds)
                if not real_probs: continue

                match_candidates = []

                for sel, bf_price in bf_odds.items():
                    if sel not in real_probs: continue
                    
                    # REGOLA 1: RANGE QUOTA
                    if not (MIN_ODDS <= bf_price <= MAX_ODDS): continue
                    
                    true_p = real_probs[sel]
                    real_odd = round(1/true_p, 2)
                    
                    bf_net = 1 + ((bf_price - 1) * (1 - config.COMMISSIONE_BETFAIR))
                    ev_perc = round(((true_p * bf_net) - 1) * 100, 2)
                    q_target = calcola_target_buy(true_p)

                    # --- REGOLA 2: FILTRO SPECIFICO PAREGGI (V49) ---
                    is_draw = (sel == 'Draw' or sel == 'X')
                    
                    # Definizione soglie dinamiche
                    if is_draw:
                        soglia_watch = DRAW_EV_WATCH # 1.5%
                        soglia_value = DRAW_EV_VALUE # 2.5%
                    else:
                        soglia_watch = STD_EV_WATCH  # -1.5%
                        soglia_value = STD_EV_VALUE  # 1.5%

                    # Filtro Base (Cestino)
                    if ev_perc < soglia_watch: continue

                    # TREND
                    trend_symbol = "➖"
                    trend_mod = 1.0
                    if match_id in history and sel in history[match_id]:
                        pinna_old = history[match_id][sel]
                        pinna_now = pinna_odds[sel]
                        diff = pinna_now - pinna_old
                        if diff < 0: 
                            trend_symbol = "↘️ DROP"
                            trend_mod = 1.2
                        elif diff > 0: 
                            trend_symbol = "↗️ RISE"
                            trend_mod = 0.5
                    
                    # STAKE & STATO
                    stake_ready = 0
                    stato = "WATCH"
                    
                    # Diventa READY solo se supera la soglia VALUE specifica (2.5 per X, 1.5 per 1/2)
                    if ev_perc >= soglia_value:
                        stake_ready = calcola_kelly_stake(true_p, bf_price, trend_mod)
                        stato = "READY" if stake_ready > 0 else "WATCH"
                    
                    q_calc = max(bf_price, q_target)
                    stake_limit = calcola_kelly_stake(true_p, q_calc, trend_mod)

                    if stake_limit > 0:
                        match_candidates.append({
                            'sel': sel, 'bf': bf_price, 'target': q_target, 'real': real_odd,
                            'ev': ev_perc, 's_ready': stake_ready, 's_limit': stake_limit, 
                            'trend': trend_symbol, 'st': stato
                        })

                if match_candidates:
                    # REGOLA 3: SOLO IL MIGLIORE DEL MATCH
                    best = sorted(match_candidates, key=lambda x: x['ev'], reverse=True)[0]
                    
                    with open(config.FILE_PENDING, 'a', newline='', encoding='utf-8') as f:
                        csv.writer(f).writerow([
                            'CALCIO', datetime.now().strftime("%d/%m %H:%M"), converti_orario(event['commence_time']),
                            league['title'], match_name, best['sel'],
                            best['bf'], best['target'], best['real'], best['ev'],
                            best['s_ready'], best['s_limit'], 
                            best['trend'], best['st'], '', ''
                        ])

                    if best['st'] == "READY":
                        emoji = "🔥" if "DROP" in best['trend'] else "🟢"
                        msg = (
                            f"{emoji} SNIPER V49: {best['sel']} {best['trend']}\n"
                            f"⚽ {match_name}\n"
                            f"💰 BF: {best['bf']} (Target: {best['target']})\n"
                            f"📊 EV: +{best['ev']}%\n"
                            f"💵 STAKE: {best['s_ready']}€"
                        )
                        send_telegram(msg)
        
        save_memory(new_history)
                        
    except Exception as e: print(f"Err: {e}")

if __name__ == "__main__":
    scan_calcio()

   
