import requests, csv, os, config, json
from datetime import datetime, timedelta

# --- CONFIGURAZIONE SPORTMONKS V60 ---
TOKEN = config.SPORTMONKS_TOKEN
TELEGRAM_TOKEN = "8145327630:AAHJC6vDjvGUyPT0pKw63fyW53hTl_F873U"
TELEGRAM_CHAT_ID = "5562163433"

# STRATEGIA
BANKROLL = 5000.0
KELLY = 0.30
MIN_STAKE = 10.0

# FILTRO QUOTE
MIN_ODDS = 1.45
MAX_ODDS = 6.50
EV_MIN = 2.0  # Richiediamo valore puro

# BOOKMAKER IDs (Sportmonks V3 Standard)
BK_PINNACLE = 2
BK_BETFAIR = 6
BK_BET365 = 1  # Usato come backup affidabile se manca Betfair

# LEGE EUROPEE (Il tuo piano copre queste)
EURO_LEAGUES = [
    "Champions League", "Europa League", "Conference League",
    "Serie A", "Serie B", "Premier League", "Championship",
    "La Liga", "Bundesliga", "Ligue 1", "Eredivisie", 
    "Primeira Liga", "Coppa Italia", "FA Cup"
]

def send_telegram(msg):
    try: requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", params={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
    except: pass

def kelly_crit(true_p, odd_b):
    try:
        if odd_b <= 1.01: return 0
        net_odd = 1 + ((odd_b - 1) * (1 - config.COMMISSIONE_BETFAIR))
        b = net_odd - 1
        q = 1 - true_p
        f = (b * true_p - q) / b
        stake = BANKROLL * f * KELLY
        return int(stake) if stake >= MIN_STAKE else 0
    except: return 0

def scan_calcio():
    print(f"--- ⚽ CALCIO V60 (SPORTMONKS EUROPE) - {datetime.now()} ---")
    
    if "INCOLLA_QUI" in TOKEN:
        print("⚠️ ERRORE: Inserisci il token Sportmonks in config.py!")
        return

    # Date: Oggi e Domani
    dates = [datetime.now().strftime("%Y-%m-%d"), (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")]
    
    header = ['Sport', 'Data', 'Ora', 'Torneo', 'Match', 'Selezione', 'Q_Betfair', 'Q_Target', 'Q_Reale', 'EV_%', 'Stake_Ready', 'Stake_Limit', 'Trend', 'Stato', 'Esito', 'Profitto']
    mode = 'a' if os.path.exists(config.FILE_PENDING) else 'w'
    
    with open(config.FILE_PENDING, mode, newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if mode == 'w': writer.writerow(header)

        for d in dates:
            # Chiamata API Ottimizzata
            url = f"https://api.sportmonks.com/v3/football/fixtures/date/{d}"
            params = {
                "api_token": TOKEN,
                "include": "league;participants;odds", 
            }
            
            try:
                resp = requests.get(url, params=params)
                if resp.status_code != 200: 
                    print(f"Err API: {resp.status_code}"); continue
                
                fixtures = resp.json().get('data', [])
                print(f"📅 {d}: Analisi {len(fixtures)} match...")

                for fix in fixtures:
                    # 1. Filtro Lega
                    league_name = fix.get('league', {}).get('name', 'Unknown')
                    is_target = False
                    for l in EURO_LEAGUES:
                        if l in league_name: is_target = True
                    if not is_target: continue # Salta leghe minori non coperte bene

                    name = fix.get('name')
                    start = fix.get('starting_at', d)
                    
                    # 2. Estrazione Quote
                    odds = fix.get('odds', [])
                    pinna = {}
                    target = {}

                    for o in odds:
                        # Market 1 = 1X2
                        if o['market_id'] != 1: continue
                        bid = o['bookmaker_id']
                        label = o['label'] # 1, X, 2
                        try: val = float(o['value'])
                        except: continue
                        
                        if bid == BK_PINNACLE: pinna[label] = val
                        if bid == BK_BET365: target[label] = val # Bet365 molto solido come riferimento
                    
                    if len(pinna) < 3 or len(target) < 3: continue

                    # 3. Calcoli
                    margin = (1/pinna['1']) + (1/pinna['X']) + (1/pinna['2'])
                    real_probs = {k: (1/v)/margin for k,v in pinna.items()}

                    for sel in ['1', 'X', '2']:
                        q_targ = target[sel]
                        true_p = real_probs[sel]
                        
                        if not (MIN_ODDS <= q_targ <= MAX_ODDS): continue
                        
                        # EV
                        net = 1 + ((q_targ - 1) * 0.95)
                        ev = round(((true_p * net) - 1) * 100, 2)
                        
                        # Pareggi solo se altissimo valore
                        if sel == 'X' and ev < 3.0: continue
                        if ev < -1.0: continue

                        stake = 0
                        status = "WATCH"
                        if ev >= EV_MIN:
                            stake = kelly_crit(true_p, q_targ)
                            status = "READY" if stake > 0 else "WATCH"
                        
                        # Calcolo Target Price per Limit Order
                        limit_p = round((( (1.025)/true_p - 1)/0.95) + 1, 2)
                        stake_limit = kelly_crit(true_p, max(q_targ, limit_p))

                        if stake_limit > 0:
                            writer.writerow([
                                'CALCIO', datetime.now().strftime("%d/%m %H:%M"), start,
                                league_name, name, sel,
                                q_targ, limit_p, round(1/true_p, 2), ev,
                                stake, stake_limit, "➖", status, '', ''
                            ])
                            
                            if status == "READY":
                                send_telegram(f"⚽ SM-V60: {name} ({sel}) EV:{ev}% Stake:{stake}€")

            except Exception as e: print(f"Err {d}: {e}")

if __name__ == "__main__":
    scan_calcio()
