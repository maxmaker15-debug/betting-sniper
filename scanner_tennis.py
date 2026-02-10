import requests, csv, os, config, json
from datetime import datetime, timezone
import dateutil.parser

# --- CONFIGURAZIONE TENNIS V60 (ODDS API 20k PLAN) ---
API_KEY = config.API_KEY  # Prende la chiave da 20k inserita in config
TELEGRAM_TOKEN = "8145327630:AAHJC6vDjvGUyPT0pKw63fyW53hTl_F873U"
TELEGRAM_CHAT_ID = "5562163433"

BANKROLL = 5000.0
KELLY = 0.30
MIN_STAKE = 10.0

MIN_ODDS = 1.25
MAX_ODDS = 7.00
EV_MIN = 2.0

def send_telegram(msg):
    try: requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", params={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
    except: pass

def kelly_stake(true_p, odd_b):
    try:
        if odd_b <= 1.01: return 0
        net = 1 + ((odd_b - 1) * 0.95)
        b = net - 1
        f = (b * true_p - (1-true_p)) / b
        stake = BANKROLL * f * KELLY
        return int(stake) if stake >= MIN_STAKE else 0
    except: return 0

def scan_tennis():
    print(f"--- 🎾 TENNIS V60 (FULL SCAN) - {datetime.now()} ---")
    
    header = ['Sport', 'Data', 'Ora', 'Torneo', 'Match', 'Selezione', 'Q_Betfair', 'Q_Target', 'Q_Reale', 'EV_%', 'Stake_Ready', 'Stake_Limit', 'Trend', 'Stato', 'Esito', 'Profitto']
    mode = 'a' if os.path.exists(config.FILE_PENDING) else 'w'
    
    with open(config.FILE_PENDING, mode, newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if mode == 'w': writer.writerow(header)

        try:
            # 1. Trova TUTTI i tornei tennis attivi (abbiamo 20k crediti, non badare a spese)
            resp = requests.get('https://api.the-odds-api.com/v4/sports', params={'apiKey': API_KEY})
            if resp.status_code != 200:
                print(f"Err API Tennis: {resp.status_code}")
                return
                
            leagues = [s for s in resp.json() if 'tennis' in s['key'].lower() and 'winner' not in s['key']]
            print(f"📡 Trovati {len(leagues)} tornei tennis. Scansione totale in corso...")

            for league in leagues:
                resp = requests.get(f'https://api.the-odds-api.com/v4/sports/{league["key"]}/odds', 
                                  params={'apiKey': API_KEY, 'regions': 'eu', 'markets': 'h2h', 'oddsFormat': 'decimal'})
                if resp.status_code != 200: continue
                
                data = resp.json()
                for ev in data:
                    match = f"{ev['home_team']} vs {ev['away_team']}"
                    
                    # Cerca Bookmakers
                    pinna = {}
                    bf = {}
                    
                    for b in ev['bookmakers']:
                        if b['key'] == 'pinnacle':
                            for o in b['markets'][0]['outcomes']: pinna[o['name']] = o['price']
                        if b['key'] == 'betfair_ex_eu' or b['key'] == 'betfair': # Cerca Exchange
                            for o in b['markets'][0]['outcomes']: bf[o['name']] = o['price']
                    
                    # Se manca Exchange, usa Bet365 come riferimento per il Target
                    if not bf:
                         for b in ev['bookmakers']:
                            if b['key'] == 'bet365':
                                for o in b['markets'][0]['outcomes']: bf[o['name']] = o['price']

                    if not pinna or not bf: continue

                    # Calcoli
                    margin = sum([1/x for x in pinna.values()])
                    real_probs = {k: (1/v)/margin for k,v in pinna.items()}

                    for sel, odd in bf.items():
                        if sel not in real_probs: continue
                        true_p = real_probs[sel]
                        
                        if not (MIN_ODDS <= odd <= MAX_ODDS): continue

                        net = 1 + ((odd - 1) * 0.95)
                        ev = round(((true_p * net) - 1) * 100, 2)
                        
                        if ev < -1.0: continue

                        stake = 0
                        st = "WATCH"
                        if ev >= EV_MIN:
                            stake = kelly_stake(true_p, odd)
                            st = "READY" if stake > 0 else "WATCH"
                        
                        target_p = round((( (1.025)/true_p - 1)/0.95) + 1, 2)
                        limit = kelly_stake(true_p, max(odd, target_p))

                        if limit > 0:
                             writer.writerow([
                                'TENNIS', datetime.now().strftime("%d/%m %H:%M"), "Live/Up",
                                league['title'], match, sel,
                                odd, target_p, round(1/true_p, 2), ev,
                                stake, limit, "➖", st, '', ''
                            ])
                             
                             if st == "READY":
                                 send_telegram(f"🎾 ODS-V60: {match} ({sel}) EV:{ev}%")

        except Exception as e: print(f"Err Tennis: {e}")

if __name__ == "__main__":
    scan_tennis()
