import requests, csv, os, config, pandas as pd
from datetime import datetime
import dateutil.parser

# --- ⚠️ CONFIGURAZIONE DIRETTA (DEBUG) ⚠️ ---
# Inserisci le chiavi qui tra le virgolette per essere SICURI al 100%
API_KEY = "INSERISCI_QUI_LA_TUA_CHIAVE_ODDS_API" 
TELEGRAM_TOKEN = "8145327630:AAHJC6vDjvGUyPT0pKw63fyW53hTl_F873U"
TELEGRAM_CHAT_ID = "5562163433"

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try: 
        resp = requests.get(url, params={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
        print(f"TELEGRAM STATUS: {resp.status_code}") # Log per GitHub
    except Exception as e: 
        print(f"TELEGRAM ERROR: {e}")

def converti_orario(iso_date):
    try: return dateutil.parser.parse(iso_date).strftime("%Y-%m-%d %H:%M")
    except: return iso_date

def calcola_quota_target(prob_reale, roi=0.02):
    fair_odds = 1 / prob_reale
    target_netto = fair_odds * (1 + roi)
    target_lordo = 1 + ((target_netto - 1) / (1 - config.COMMISSIONE_BETFAIR))
    return round(target_lordo, 2)

def calcola_stake(valore_perc, quota_netta):
    try:
        if quota_netta <= 1: return 0
        kelly_perc = (valore_perc / 100) / (quota_netta - 1)
        stake_calcolato = config.BANKROLL_TOTALE * config.KELLY_FRACTION * kelly_perc
        if stake_calcolato > config.STAKE_MASSIMO: stake_calcolato = config.STAKE_MASSIMO
        if stake_calcolato < 0: stake_calcolato = 0
        return int(stake_calcolato)
    except: return 0

def calcola_target_scalping(quota_ingresso):
    target = quota_ingresso - (quota_ingresso * 0.025) 
    if target < 1.01: target = 1.01
    return round(target, 2)

def check_watchdog(event_name, current_pinnacle_odds, trade_row):
    # Funzione Watchdog (semplificata per debug)
    pass

def analizza_calcio_sniper(pinnacle_odds, soft_odds):
    if len(pinnacle_odds) != 3: return None
    try:
        inv_h, inv_d, inv_a = 1/pinnacle_odds['Home'], 1/pinnacle_odds['Draw'], 1/pinnacle_odds['Away']
        margin = inv_h + inv_d + inv_a
        real_prob = {'Home': inv_h/margin, 'Draw': inv_d/margin, 'Away': inv_a/margin}
    except: return None

    migliore_opzione = None
    miglior_valore = -100

    for outcome, soft_price in soft_odds.items():
        if outcome not in real_prob: continue
        
        quota_reale_pinna = round(1 / real_prob[outcome], 2)
        net_price = 1 + ((soft_price - 1) * (1 - config.COMMISSIONE_BETFAIR))
        ev = (real_prob[outcome] * net_price) - 1
        ev_perc = ev * 100
        quota_req = calcola_quota_target(real_prob[outcome])

        status = None
        if ev_perc > config.SOGLIA_VALUE_CALCIO: status = "VALUE"
        elif ev_perc > config.SOGLIA_SNIPER_CALCIO: status = "ATTESA"

        if status:
            if ev_perc > miglior_valore:
                miglior_valore = ev_perc
                migliore_opzione = {
                    'sel': outcome, 
                    'q_att': soft_price, 
                    'q_req': quota_req, 
                    'q_real': quota_reale_pinna,
                    'val': round(ev_perc, 2), 
                    'status': status
                }
    return migliore_opzione

def scan_calcio():
    print("--- INIZIO SCANSIONE CALCIO (DEBUG MODE) ---")
    
    # 1. TEST CONNESSIONE ODDS API
    leagues = ['soccer_italy_serie_a', 'soccer_england_premier_league', 'soccer_spain_la_liga'] # Riduciamo per test veloce
    
    events_found = 0
    opportunities = 0

    for league in leagues:
        print(f"Analisi Lega: {league}...")
        url = f'https://api.the-odds-api.com/v4/sports/{league}/odds'
        # Qui togliamo il try/except per vedere se crasha!
        resp = requests.get(url, params={'apiKey': API_KEY, 'regions': config.REGIONS, 'markets': 'h2h', 'oddsFormat': 'decimal'})
        
        print(f"API Status Code: {resp.status_code}")
        
        if resp.status_code != 200:
            print(f"ERRORE API: {resp.text}")
            continue

        data = resp.json()
        print(f"Eventi trovati: {len(data)}")
        
        for event in data:
            events_found += 1
            home, away = event['home_team'], event['away_team']
            
            # Estrazione Pinnacle
            pinna_raw = {}
            for b in event['bookmakers']:
                if b['key'] == 'pinnacle':
                    for m in b['markets']:
                        if m['key'] == 'h2h':
                            for o in m['outcomes']: pinna_raw[o['name']] = o['price']
            
            # Estrazione Betfair
            soft_raw = {}
            for b in event['bookmakers']:
                if 'betfair' in b['title'].lower():
                    for m in b['markets']:
                        if m['key'] == 'h2h':
                            for o in m['outcomes']: soft_raw[o['name']] = o['price']
            
            # Analisi
            if len(pinna_raw) >= 3 and len(soft_raw) >= 2:
                try: 
                    p_map = {'Home': pinna_raw[home], 'Draw': pinna_raw['Draw'], 'Away': pinna_raw[away]}
                    soft_map = {}
                    if home in soft_raw: soft_map['Home'] = soft_raw[home]
                    if away in soft_raw: soft_map['Away'] = soft_raw[away]
                    if 'Draw' in soft_raw: soft_map['Draw'] = soft_raw['Draw']
                    
                    res = analizza_calcio_sniper(p_map, soft_map)
                    
                    if res:
                        print(f"!!! OPPORTUNITÀ TROVATA: {home} vs {away} !!!")
                        opportunities += 1
                        
                        # INVIO NOTIFICA
                        sel_name = home if res['sel']=='Home' else (away if res['sel']=='Away' else 'Pareggio')
                        msg = f"🔍 TEST DEBUG:\n⚽ {home} vs {away}\n👉 {sel_name}\n🔹 {res['q_att']} (Pinna {res['q_real']})"
                        send_telegram(msg)
                except Exception as e:
                    print(f"Errore nel calcolo: {e}")

    print(f"--- FINE SCANSIONE. Eventi: {events_found}, Occasioni: {opportunities} ---")
