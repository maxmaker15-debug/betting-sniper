import requests, csv, os, config, json
from datetime import datetime, timezone, timedelta
import dateutil.parser

# --- CONFIGURAZIONE TENNIS V60 ---
API_KEY = config.API_KEY 
TELEGRAM_TOKEN = "8145327630:AAHJC6vDjvGUyPT0pKw63fyW53hTl_F873U"
TELEGRAM_CHAT_ID = "5562163433"

BANKROLL = config.BANKROLL_TOTALE
COMMISSIONE = config.COMMISSIONE_BETFAIR
KELLY = 0.30
MIN_STAKE = 10.0

def send_telegram(msg):
    try: requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", params={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
    except: pass

def kelly_stake(true_p, odd_b):
    try:
        if odd_b <= 1.01: return 0
        net = 1 + ((odd_b - 1) * (1 - COMMISSIONE))
        b = net - 1
        f = (b * true_p - (1-true_p)) / b
        stake = BANKROLL * f * KELLY
        return int(stake) if stake >= MIN_STAKE else 0
    except: return 0

def scan_tennis():
    print(f"--- 🎾 TENNIS V60 (FULL SCAN) - {datetime.now()} ---")
    
    try:
        RULES = config.FILTRI_STRATEGIA
        print(f"⚙️ REGOLE: Quote {RULES['QUOTA_MIN']}-{RULES['QUOTA_MAX']} | Quasi Value: {RULES['QUASI_VALUE_MIN']}% a {RULES['QUASI_VALUE_MAX']}%")
    except AttributeError:
        print("⚠️ ERRORE: Configurazione non trovata.")
        return

    header = ['Sport', 'Data', 'Ora', 'Torneo', 'Match', 'Selezione', 'Q_Betfair', 'Q_Target', 'Q_Reale', 'EV_%', 'Stake_Ready', 'Stake_Limit', 'Trend', 'Stato', 'Esito', 'Profitto']
    mode = 'a' if os.path.exists(config.FILE_PENDING) else 'w'
    
    with open(config.FILE_PENDING, mode, newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if mode == 'w': writer.writerow(header)

        try:
            resp = requests.get('https://api.the-odds-api.com/v4/sports', params={'apiKey': API_KEY})
            if resp.status_code != 200: return
            leagues = [s for s in resp.json() if 'tennis' in s['key'].lower() and 'winner' not in s['key']]
            print(f"📡 Trovati {len(leagues)} tornei tennis. Scansione in corso...")

            for league in leagues:
                resp = requests.get(f'https://api.the-odds-api.com/v4/sports/{league["key"]}/odds', 
                                  params={'apiKey': API_KEY, 'regions': 'eu', 'markets': 'h2h', 'oddsFormat': 'decimal'})
                if resp.status_code != 200: continue
                data = resp.json()
                
                for ev in data:
                    match = f"{ev['home_team']} vs {ev['away_team']}"
                    try:
                        commence_time = dateutil.parser.parse(ev['commence_time'])
                        now = datetime.now(timezone.utc)
                        hours_diff = (commence_time - now).total_seconds() / 3600
                        if not (RULES['ORE_ANTICIPO_MIN'] <= hours_diff <= RULES['ORE_ANTICIPO_MAX']): continue
                        start_str = commence_time.strftime("%d/%m %H:%M")
                    except: start_str = "N/A"

                    pinna = {}
                    bf = {}
                    for b in ev['bookmakers']:
                        if b['key'] == 'pinnacle':
                            for o in b['markets'][0]['outcomes']: pinna[o['name']] = o['price']
                        if b['key'] == 'betfair_ex_eu' or b['key'] == 'betfair': 
                            for o in b['markets'][0]['outcomes']: bf[o['name']] = o['price']
                    
                    if not bf:
                         for b in ev['bookmakers']:
                            if b['key'] == 'bet365':
                                for o in b['markets'][0]['outcomes']: bf[o['name']] = o['price']

                    if not pinna or not bf: continue

                    margin = sum([1/x for x in pinna.values()])
                    real_probs = {k: (1/v)/margin for k,v in pinna.items()}

                    for sel, odd in bf.items():
                        if sel not in real_probs: continue
                        true_p = real_probs[sel]
                        q_pinna = pinna[sel]
                        
                        # A. Filtro Range
                        if not (RULES['QUOTA_MIN'] <= odd <= RULES['QUOTA_MAX']): continue

                        # B. Calcolo EV
                        net = 1 + ((odd - 1) * (1 - COMMISSIONE))
                        ev = round(((true_p * net) - 1) * 100, 2)
                        
                        # C. Filtro Spazzatura (Sotto Quasi Value)
                        if ev < RULES['QUASI_VALUE_MIN']: continue

                        # E. Trend
                        trend_diff = round((1 - (q_pinna / odd)) * 100, 1)
                        trend_str = f"📉 {trend_diff}%" if trend_diff > 0 else "➖"

                        stake = 0
                        status = "WATCH"
                        
                        # F. Classificazione: QUASI vs READY
                        if RULES['QUASI_VALUE_MIN'] <= ev <= RULES['QUASI_VALUE_MAX']:
                            status = "QUASI"
                        elif ev >= (RULES['VALUE_MINIMO'] * 100):
                            stake = kelly_stake(true_p, odd)
                            status = "READY" if stake > 0 else "WATCH"
                        
                        # G. Limit Order
                        target_p = round((( (1.025)/true_p - 1)/(1-COMMISSIONE)) + 1, 2)
                        limit = kelly_stake(true_p, max(odd, target_p))

                        writer.writerow([
                            'TENNIS', datetime.now().strftime("%d/%m %H:%M"), start_str,
                            league['title'], match, sel,
                            odd, target_p, round(1/true_p, 2), ev,
                            stake, limit, trend_str, status, '', ''
                        ])
                        
                        if status == "READY":
                             print(f"✅ TENNIS: {match} [{sel}] @{odd} (EV: {ev}%)")
                             send_telegram(f"🎾 ODS-V60: {match} ({sel}) EV:{ev}% Stake:{stake}€")

        except Exception as e: print(f"Err Tennis: {e}")

if __name__ == "__main__":
    scan_tennis()
