import requests, csv, os, config, pandas as pd
from datetime import datetime, timezone
import dateutil.parser

# --- CONFIGURAZIONE ---
API_KEY = config.API_KEY
TELEGRAM_TOKEN = "8145327630:AAHJC6vDjvGUyPT0pKw63fyW53hTl_F873U"
TELEGRAM_CHAT_ID = "5562163433"

# --- PARAMETRI ---
REGIONS = 'eu'
MARKETS = 'h2h'
ODDS_FORMAT = 'decimal'
MAX_ODDS_CAP = 5.00 # Filtro anti-biscotto

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try: requests.get(url, params={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
    except: pass

def converti_orario(iso_date):
    try: return dateutil.parser.parse(iso_date).strftime("%Y-%m-%d %H:%M")
    except: return iso_date

def scan_calcio():
    print(f"\n--- ⚽ SCANSIONE CALCIO (DIAGNOSTICA) - {datetime.now()} ---")
    
    # Header CSV
    header = ['Sport', 'Data_Scan', 'Orario_Match', 'Torneo', 'Match', 'Selezione', 'Bookmaker', 'Quota_Ingresso', 'Pinnacle_Iniziale', 'Target_Scalping', 'Quota_Sniper_Target', 'Valore_%', 'Stake_Euro', 'Stato_Trade', 'Esito_Finale', 'Profitto_Reale']
    
    # Carica trades aperti per Watchdog
    open_trades = []
    if os.path.exists(config.FILE_PENDING):
        try:
            df = pd.read_csv(config.FILE_PENDING)
            if 'Stato_Trade' in df.columns: open_trades = df[df['Stato_Trade'] == 'APERTO'].to_dict('records')
        except: pass
    else:
        with open(config.FILE_PENDING, 'w', newline='', encoding='utf-8') as f: csv.writer(f).writerow(header)

    try:
        # 1. Recupero Campionati
        print("📡 Recupero lista campionati Calcio...")
        resp = requests.get('https://api.the-odds-api.com/v4/sports', params={'apiKey': API_KEY})
        if resp.status_code != 200:
            print("❌ Errore API lista sport.")
            return

        # Filtra solo calcio (Soccer)
        soccer_leagues = [s for s in resp.json() if 'soccer' in s['key'] and 'winner' not in s['key']]
        print(f"✅ Campionati attivi trovati: {len(soccer_leagues)}")

        match_analizzati = 0
        match_scartati_valore_basso = 0
        now_utc = datetime.now(timezone.utc)

        # 2. Analisi Quote
        for league in soccer_leagues:
            # print(f"🔍 Scansiono: {league['title']}...") # Decommentare se vuoi la lista lunga
            url = f'https://api.the-odds-api.com/v4/sports/{league["key"]}/odds'
            resp = requests.get(url, params={'apiKey': API_KEY, 'regions': REGIONS, 'markets': MARKETS, 'oddsFormat': ODDS_FORMAT})
            
            if resp.status_code != 200: continue
            
            events = resp.json()
            for event in events:
                # Filtro Anti-Live
                try:
                    commence_time = dateutil.parser.parse(event['commence_time'])
                    if commence_time <= now_utc: continue 
                except: continue

                match_analizzati += 1
                home, away = event['home_team'], event['away_team']
                match_name = f"{home} vs {away}"

                # Trova Pinnacle (Benchmark)
                pinna_odds = {}
                for b in event['bookmakers']:
                    if b['key'] == 'pinnacle':
                        for m in b['markets']:
                            if m['key']=='h2h':
                                for o in m['outcomes']: pinna_odds[o['name']] = o['price']
                
                if len(pinna_odds) < 2: continue # Niente Pinnacle, niente party

                # Calcolo Probabilità Reale (No Margin)
                try:
                    inv_h = 1/pinna_odds[home]
                    inv_a = 1/pinna_odds[away]
                    inv_d = 1/pinna_odds['Draw'] if 'Draw' in pinna_odds else 0
                    margin = inv_h + inv_a + inv_d
                    real_prob = {home: inv_h/margin, away: inv_a/margin}
                    if inv_d: real_prob['Draw'] = inv_d/margin
                except: continue

                # Confronto con Betfair
                for b in event['bookmakers']:
                    if 'betfair' in b['title'].lower():
                        for m in b['markets']:
                            if m['key']=='h2h':
                                for outcome in m['outcomes']:
                                    if outcome['name'] not in real_prob: continue
                                    
                                    soft_price = outcome['price']
                                    sel_name = outcome['name']
                                    
                                    # Filtro Quota Alta
                                    if soft_price > MAX_ODDS_CAP: continue

                                    # CALCOLO VALORE
                                    net_price = 1 + ((soft_price - 1) * (1 - config.COMMISSIONE_BETFAIR))
                                    ev = (real_prob[sel_name] * net_price) - 1
                                    ev_perc = round(ev * 100, 2)
                                    
                                    # --- DEBUG PRINT ---
                                    # Stampa solo se il valore è almeno decente (es. > -2%) per non intasare il log
                                    if ev_perc > -2.0:
                                        print(f"   📉 {match_name} [{sel_name}] -> EV: {ev_perc}% (Quota: {soft_price})")

                                    # LOGICA SELEZIONE
                                    status = None
                                    if ev_perc > config.SOGLIA_VALUE_CALCIO: status = "VALUE"
                                    elif ev_perc > config.SOGLIA_SNIPER_CALCIO: status = "ATTESA"

                                    if status:
                                        print(f"   🔥 TROVATO! {status} - {match_name}")
                                        # (Codice salvataggio CSV e Telegram identico a prima...)
                                        # Calcoli
                                        stake_euro = 0
                                        quota_sniper = 0
                                        q_scalp = 0
                                        quota_reale_pinna = round(1/real_prob[sel_name], 2)
                                        
                                        # Scrive CSV e Telegram...
                                        with open(config.FILE_PENDING, 'a', newline='', encoding='utf-8') as f:
                                            csv.writer(f).writerow(['CALCIO', datetime.now().strftime("%Y-%m-%d %H:%M"), converti_orario(event.get('commence_time', 'N/A')), league['title'], match_name, sel_name, b['title'], soft_price, quota_reale_pinna, 0, 0, f"{status} {ev_perc}%", 0, 'APERTO', '', ''])
                                        
                                        msg = f"{'🟢' if status=='VALUE' else '🟡'} CALCIO: {sel_name}\n⚽ {match_name}\n🔹 EV: {ev_perc}%\nQuota: {soft_price}"
                                        send_telegram(msg)
                                    else:
                                        match_scartati_valore_basso += 1

        print(f"🏁 DIAGNOSI COMPLETATA.")
        print(f"Match Totali Analizzati: {match_analizzati}")
        print(f"Match Scartati (EV Basso): {match_scartati_valore_basso}")

    except Exception as e: print(f"❌ Errore Calcio: {e}")

if __name__ == "__main__":
    scan_calcio()
