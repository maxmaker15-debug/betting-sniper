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

MIN_ODDS = 1.60
MAX_ODDS = 6.00     
MIN_EV_SAVE = 0.1   # Salviamo tutto ciò che supera i filtri qualitativi sotto

# --- SOGLIE DI FILTRAGGIO (Anti-Pareggio) ---
MIN_EV_HOME_AWAY = 0.8  # Abbassato: Vogliamo vedere più 1 e 2
MIN_EV_DRAW = 3.5       # Alzato: I pareggi devono essere ECCEZIONALI per apparire

# CONFIGURAZIONE KELLY
KELLY_FRACTION = 0.25   # Leggermente più aggressivi sugli stake target

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

def calcola_target_quota(true_prob):
    try:
        # Target: vogliamo un ROI matematico del 2%
        target_roi = 0.02
        target_net_odds = (1 + target_roi) / true_prob
        target_gross_odds = ((target_net_odds - 1) / (1 - config.COMMISSIONE_BETFAIR)) + 1
        return round(target_gross_odds, 2)
    except: return 0.0

def calcola_stake_kelly(true_prob, quota_riferimento):
    """
    Calcola lo stake usando la quota A CUI PUNTEREMO (Target o Attuale).
    """
    try:
        quota_netta = 1 + ((quota_riferimento - 1) * (1 - config.COMMISSIONE_BETFAIR))
        b = quota_netta - 1
        p = true_prob
        q = 1 - p
        
        full_kelly_perc = (b * p - q) / b
        
        if full_kelly_perc <= 0: return 0
        
        stake_perc = full_kelly_perc * KELLY_FRACTION
        stake_euro = config.BANKROLL_TOTALE * stake_perc
        stake_euro = max(0, min(stake_euro, config.STAKE_MASSIMO))
        
        # Arrotondamento 5€
        return int(round(stake_euro / 5) * 5)
    except: return 0

def scan_calcio():
    print(f"--- ⚽ SCANSIONE CALCIO (V35 SNIPER SIGHT) - {datetime.now()} ---")
    
    header = ['Sport', 'Data_Scan', 'Orario_Match', 'Torneo', 'Match', 'Selezione', 'Quota_Betfair', 'Quota_Target', 'Quota_Reale_Pinna', 'Valore_%', 'Stake_Euro', 'Stato_Trade', 'Esito_Finale', 'Profitto_Reale']
    
    mode = 'a'
    if not os.path.exists(config.FILE_PENDING): mode = 'w'
    
    f = open(config.FILE_PENDING, mode, newline='', encoding='utf-8')
    writer = csv.writer(f, delimiter=',')
    if mode == 'w': writer.writerow(header)

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

                match_candidates = []

                for sel_name, bf_price in betfair_odds_raw.items():
                    if sel_name not in real_probs: continue
                    if not (MIN_ODDS <= bf_price <= MAX_ODDS): continue
                    
                    true_prob = real_probs[sel_name]
                    fair_odds = 1 / true_prob
                    
                    bf_netto = 1 + ((bf_price - 1) * (1 - config.COMMISSIONE_BETFAIR))
                    ev = (true_prob * bf_netto) - 1
                    ev_perc = round(ev * 100, 2)
                    
                    # --- FILTRO BRUTALE V35 ---
                    is_draw = (sel_name == 'Draw' or sel_name == 'X')
                    
                    # 1. ELIMINAZIONE DIRETTA DEI PAREGGI INUTILI
                    if is_draw and ev_perc < MIN_EV_DRAW:
                        continue # Salta direttamente, non lo voglio vedere

                    # 2. ELIMINAZIONE DIRETTA 1/2 SCARSI
                    if not is_draw and ev_perc < MIN_EV_HOME_AWAY:
                        continue

                    # 3. CALCOLO TARGET E STAKE PREVISIONALE
                    quota_target = calcola_target_quota(true_prob)
                    
                    # Se l'EV è già alto (es. > 2%), il Target è la quota attuale (compra subito)
                    # Se l'EV è basso (es. 1%), il Target rimane quello calcolato (metti ordine limit)
                    if ev_perc >= 2.0:
                        quota_usata_per_stake = bf_price
                        stato = "VALUE"
                    else:
                        quota_usata_per_stake = max(bf_price, quota_target) # Usa la maggiore per calcolare stake sicuro
                        stato = "WATCH"

                    # Calcolo Stake Kelly basato sulla quota a cui entreremo (Target o Attuale)
                    stake = calcola_stake_kelly(true_prob, quota_usata_per_stake)
                    
                    # Se lo stake calcolato è < 10€, scartiamo comunque per non perdere tempo
                    if stake < 10: continue

                    match_candidates.append({
                        'sel_name': sel_name,
                        'bf_price': bf_price,
                        'quota_target': quota_target,
                        'fair_odds': round(fair_odds, 2),
                        'ev_perc': ev_perc,
                        'stake': stake,
                        'stato': stato
                    })
                
                # SELEZIONE UNICA DEL MIGLIORE
                if match_candidates:
                    # Ordina per EV
                    best_bet = sorted(match_candidates, key=lambda x: x['ev_perc'], reverse=True)[0]
                    
                    print(f"🎯 SNIPER: {match_name} -> {best_bet['sel_name']} (EV {best_bet['ev_perc']}%) STAKE: {best_bet['stake']}")
                    
                    writer.writerow([
                        'CALCIO', 
                        datetime.now().strftime("%Y-%m-%d %H:%M"), 
                        converti_orario(event['commence_time']), 
                        league['title'], 
                        match_name, 
                        best_bet['sel_name'], 
                        best_bet['bf_price'],               
                        best_bet['quota_target'],           
                        best_bet['fair_odds'], 
                        best_bet['ev_perc'], 
                        best_bet['stake'], # Qui ora c'è lo stake calcolato sul TARGET
                        best_bet['stato'], '', ''
                    ])
                    
                    # Notifica
                    if best_bet['ev_perc'] >= 2.0:
                        msg = (
                            f"🟢 VALUE BET: {best_bet['sel_name']}\n"
                            f"⚽ {match_name}\n"
                            f"📊 BF: {best_bet['bf_price']} | 🎯 REAL: {best_bet['fair_odds']}\n"
                            f"📈 EV: +{best_bet['ev_perc']}%\n"
                            f"💰 Stake: {best_bet['stake']}€"
                        )
                        send_telegram(msg)

    except Exception as e: print(f"Errore Calcio: {e}")
    finally: f.close()

if __name__ == "__main__":
    scan_calcio()
