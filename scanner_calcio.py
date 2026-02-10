import requests, csv, os, config, json
from datetime import datetime, timedelta

# --- CONFIGURAZIONE SPORTMONKS V60 ---
TOKEN = config.SPORTMONKS_TOKEN
TELEGRAM_TOKEN = "8145327630:AAHJC6vDjvGUyPT0pKw63fyW53hTl_F873U"
TELEGRAM_CHAT_ID = "5562163433"

# STRATEGIA DA CONFIG
BANKROLL = config.BANKROLL_TOTALE
COMMISSIONE = config.COMMISSIONE_BETFAIR
KELLY = 0.30 
MIN_STAKE = 10.0

# BOOKMAKER IDs
BK_PINNACLE = 2
BK_BETFAIR = 6
BK_BET365 = 1 

# LEGE EUROPEE
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
        net_odd = 1 + ((odd_b - 1) * (1 - COMMISSIONE))
        b = net_odd - 1
        q = 1 - true_p
        f = (b * true_p - q) / b
        stake = BANKROLL * f * KELLY
        return int(stake) if stake >= MIN_STAKE else 0
    except: return 0

def scan_calcio():
    print(f"--- ⚽ CALCIO V60 (SPORTMONKS EUROPE) - {datetime.now()} ---")
    
    try:
        RULES = config.FILTRI_STRATEGIA
        print(f"⚙️ REGOLE: Quote {RULES['QUOTA_MIN']}-{RULES['QUOTA_MAX']} | Quasi Value: {RULES['QUASI_VALUE_MIN']}% a {RULES['QUASI_VALUE_MAX']}%")
    except AttributeError:
        print("⚠️ ERRORE: Configurazione non trovata.")
        return

    dates = [datetime.now().strftime("%Y-%m-%d"), (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")]
    header = ['Sport', 'Data', 'Ora', 'Torneo', 'Match', 'Selezione', 'Q_Betfair', 'Q_Target', 'Q_Reale', 'EV_%', 'Stake_Ready', 'Stake_Limit', 'Trend', 'Stato', 'Esito', 'Profitto']
    mode = 'a' if os.path.exists(config.FILE_PENDING) else 'w'
    
    with open(config.FILE_PENDING, mode, newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if mode == 'w': writer.writerow(header)

        for d in dates:
            url = f"https://api.sportmonks.com/v3/football/fixtures/date/{d}"
            params = {"api_token": TOKEN, "include": "league;participants;odds"}
            
            try:
                resp = requests.get(url, params=params)
                if resp.status_code != 200: continue
                fixtures = resp.json().get('data', [])
                print(f"📅 {d}: Analisi {len(fixtures)} match...")

                for fix in fixtures:
                    league_name = fix.get('league', {}).get('name', 'Unknown')
                    is_target = False
                    for l in EURO_LEAGUES:
                        if l in league_name: is_target = True
                    if not is_target: continue 

                    name = fix.get('name')
                    start_str = fix.get('starting_at', d)
                    
                    # Filtro Temporale
                    try:
                        match_time = datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S")
                        ore_mancanti = (match_time - datetime.now()).total_seconds() / 3600
                        if not (RULES['ORE_ANTICIPO_MIN'] <= ore_mancanti <= RULES['ORE_ANTICIPO_MAX']): continue
                    except: pass

                    odds = fix.get('odds', [])
                    pinna = {}
                    target = {}

                    for o in odds:
                        if o['market_id'] != 1: continue
                        bid = o['bookmaker_id']
                        label = o['label'] 
                        try: val = float(o['value'])
                        except: continue
                        if bid == BK_PINNACLE: pinna[label] = val
                        if bid == BK_BET365: target[label] = val 
                    
                    if len(pinna) < 3 or len(target) < 3: continue

                    margin = (1/pinna['1']) + (1/pinna['X']) + (1/pinna['2'])
                    real_probs = {k: (1/v)/margin for k,v in pinna.items()}

                    for sel in ['1', 'X', '2']:
                        if sel not in target: continue
                        q_targ = target[sel]
                        true_p = real_probs[sel]
                        q_pinna = pinna[sel]
                        
                        # A. Filtro Range
                        if not (RULES['QUOTA_MIN'] <= q_targ <= RULES['QUOTA_MAX']): continue
                        
                        # B. Calcolo EV
                        net = 1 + ((q_targ - 1) * 0.95)
                        ev = round(((true_p * net) - 1) * 100, 2)
                        
                        # C. Filtro Spazzatura (Sotto il minimo del Quasi Value)
                        if ev < RULES['QUASI_VALUE_MIN']: continue

                        # D. Regola Pareggi (EV > 2.5%)
                        if sel == 'X' and ev < RULES['PAREGGIO_MIN_EV']: continue

                        # E. Trend (Pinnacle Drop)
                        trend_diff = round((1 - (q_pinna / q_targ)) * 100, 1)
                        trend_str = f"📉 {trend_diff}%" if trend_diff > 0 else "➖"

                        stake = 0
                        status = "WATCH"
                        
                        # F. Classificazione: QUASI vs READY
                        if RULES['QUASI_VALUE_MIN'] <= ev <= RULES['QUASI_VALUE_MAX']:
                            status = "QUASI"
                        elif ev >= (RULES['VALUE_MINIMO'] * 100):
                            stake = kelly_crit(true_p, q_targ)
                            status = "READY" if stake > 0 else "WATCH"

                        # G. Limit Order (Target Price)
                        limit_p = round((( (1.025)/true_p - 1)/0.95) + 1, 2)
                        stake_limit = kelly_crit(true_p, max(q_targ, limit_p))

                        # Scrittura (Solo se è almeno una Quasi Value o Ready)
                        writer.writerow([
                            'CALCIO', datetime.now().strftime("%d/%m %H:%M"), start_str,
                            league_name, name, sel,
                            q_targ, limit_p, round(1/true_p, 2), ev,
                            stake, stake_limit, trend_str, status, '', ''
                        ])
                        
                        if status == "READY":
                            print(f"✅ TROVATO: {name} [{sel}] @{q_targ} (EV: {ev}%)")
                            send_telegram(f"⚽ SM-V60: {name} ({sel}) EV:{ev}% Stake:{stake}€ Q:{q_targ}")

            except Exception as e: print(f"Err {d}: {e}")

if __name__ == "__main__":
    scan_calcio()
