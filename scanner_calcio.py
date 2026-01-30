import requests, csv, os, config, pandas as pd
from datetime import datetime
import dateutil.parser

# --- ⚠️ CONFIGURAZIONE DIRETTA (HARDCODED) ⚠️ ---
# Inseriamo le chiavi direttamente qui per bypassare problemi di lettura file su GitHub
API_KEY = "78f03ed8354c09f7ac591fe7e105deda"
TELEGRAM_TOKEN = "8145327630:AAHJC6vDjvGUyPT0pKw63fyW53hTl_F873U"
TELEGRAM_CHAT_ID = "5562163433"

# Parametri operativi
REGIONS = 'eu'
MARKETS = 'h2h'
ODDS_FORMAT = 'decimal'

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try: 
        resp = requests.get(url, params={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
        # Log per il Debug su GitHub Actions
        if resp.status_code == 200:
            print("✅ TELEGRAM: Messaggio inviato correttamente.")
        else:
            print(f"❌ TELEGRAM ERROR {resp.status_code}: {resp.text}")
    except Exception as e: 
        print(f"❌ TELEGRAM CONNECTION ERROR: {e}")

def converti_orario(iso_date):
    try: return dateutil.parser.parse(iso_date).strftime("%Y-%m-%d %H:%M")
    except: return iso_date

def calcola_quota_target(prob_reale, roi=0.02):
    try:
        fair_odds = 1 / prob_reale
        target_netto = fair_odds * (1 + roi)
        target_lordo = 1 + ((target_netto - 1) / (1 - config.COMMISSIONE_BETFAIR))
        return round(target_lordo, 2)
    except: return 0

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
    try:
        ingresso_betfair = float(trade_row['Quota_Ingresso'])
        pinna_inziale = float(trade_row['Pinnacle_Iniziale'])
        sel = trade_row['Selezione']
        
        quota_pinna_now = 0
        # Logica matching selezione
        if sel in current_pinnacle_odds:
            quota_pinna_now = current_pinnacle_odds[sel]
        elif sel == 'Pareggio' and 'Draw' in current_pinnacle_odds:
            quota_pinna_now = current_pinnacle_odds['Draw']
        else:
            if 'Home' in str(sel) or trade_row['Match'].split(' vs ')[0] in str(sel): quota_pinna_now = current_pinnacle_odds.get('Home', 0)
            elif 'Away' in str(sel) or trade_row['Match'].split(' vs ')[1] in str(sel): quota_pinna_now = current_pinnacle_odds.get('Away', 0)

        if quota_pinna_now > 0:
            print(f"🐶 WATCHDOG: {event_name} - Ingresso: {ingresso_betfair}, Pinna Ora: {quota_pinna_now}") # Debug
            
            if quota_pinna_now >= ingresso_betfair:
                msg = f"🔴 ALLARME STOP LOSS: {event_name}\nLa quota Pinnacle ({quota_pinna_now}) ha superato il tuo ingresso ({ingresso_betfair})!\nChiudi subito."
                send_telegram(msg)
            elif quota_pinna_now > (pinna_inziale * 1.05):
                msg = f"⚠️ WARNING DRIFT: {event_name}\nPinnacle si sta alzando: {pinna_inziale} ➡️ {quota_pinna_now}."
                send_telegram(msg)
    except Exception as e:
        print(f"Errore Watchdog: {e}")

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
    print(f"--- 🚀 AVVIO SCANSIONE CALCIO (DEBUG) - {datetime.now()} ---")
    
    # Intestazione CSV Aggiornata (16 colonne)
    header = ['Sport', 'Data_Scan', 'Orario_Match', 'Torneo', 'Match', 'Selezione', 'Bookmaker', 'Quota_Ingresso', 'Pinnacle_Iniziale', 'Target_Scalping', 'Quota_Sniper_Target', 'Valore_%', 'Stake_Euro', 'Stato_Trade', 'Esito_Finale', 'Profitto_Reale']
    
    open_trades = []
    if os.path.exists(config.FILE_PENDING):
        try:
            df = pd.read_csv(config.FILE_PENDING)
            if 'Stato_Trade' in df.columns:
                open_trades = df[df['Stato_Trade'] == 'APERTO'].to_dict('records')
            print(f"📂 Caricati {len(open_trades)} trade aperti per Watchdog.")
        except Exception as e: print(f"Errore lettura CSV: {e}")
    else:
         with open(config.FILE_PENDING, 'w', newline='', encoding='utf-8') as f:
            csv.writer(f).writerow(header)

    leagues = [
        'soccer_italy_serie_a', 'soccer_england_premier_league', 'soccer_spain_la_liga', 
        'soccer_france_ligue_one', 'soccer_germany_bundesliga',
        'soccer_uefa_champions_league', 'soccer_uefa_europa_league', 'soccer_uefa_europa_conference_league'
    ]
    
    total_events = 0
    
    for league in leagues:
        print(f"🔍 Analisi Lega: {league}...")
        try:
            # CHIAMATA API DIRETTA
            resp = requests.get(f'https://api.the-odds-api.com/v4/sports/{league}/odds', params={'apiKey': API_KEY, 'regions': REGIONS, 'markets': MARKETS, 'oddsFormat': ODDS_FORMAT})
            
            if resp.status_code != 200:
                print(f"❌ ERRORE API {league}: {resp.status_code} - {resp.text}")
                continue

            events = resp.json()
            print(f"   -> Trovati {len(events)} eventi.")
            total_events += len(events)
            
            for event in events:
                home, away = event['home_team'], event['away_team']
                match_name = f"{home} vs {away}"
                
                # Estrazione Pinnacle
                pinna_raw = {}
                p_map = {}
                for b in event['bookmakers']:
                    if b['key'] == 'pinnacle':
                        for m in b['markets']:
                            if m['key'] == 'h2h':
                                for o in m['outcomes']: pinna_raw[o['name']] = o['price']
                if len(pinna_raw)>=3:
                     try: p_map = {'Home': pinna_raw[home], 'Draw': pinna_raw['Draw'], 'Away': pinna_raw[away]}
                     except: pass

                # Watchdog Check
                if p_map:
                    for trade in open_trades:
                        if trade['Match'] == match_name:
                            check_watchdog(match_name, p_map, trade)

                if len(pinna_raw)<3: continue
                
                # Analisi Value
                for b in event['bookmakers']:
                    if 'betfair' in b['title'].lower():
                        soft = {}
                        for m in b['markets']:
                            if m['key']=='h2h':
                                for o in m['outcomes']:
                                    if o['name']==home: soft['Home']=o['price']
                                    elif o['name']==away: soft['Away']=o['price']
                                    elif o['name']=='Draw': soft['Draw']=o['price']
                        if len(soft) >= 2:
                            res = analizza_calcio_sniper(p_map, soft)
                            if res:
                                gia_presente = False
                                for t in open_trades:
                                    if t['Match'] == match_name and t['Selezione'] == res['sel']: gia_presente = True
                                
                                if not gia_presente:
                                    print(f"🔥 OCCASIONE TROVATA: {match_name}")
                                    sel_name = home if res['sel']=='Home' else (away if res['sel']=='Away' else 'Pareggio')
                                    label_status = f"🟢 {res['status']}" if res['status']=="VALUE" else f"🟡 {res['status']}"
                                    
                                    stake_euro = 0
                                    quota_sniper = 0
                                    q_scalp = calcola_target_scalping(res['q_att']) if res['status'] == "VALUE" else calcola_target_scalping(res['q_req'])

                                    if res['status'] == "VALUE":
                                        stake_euro = calcola_stake(res['val'], res['q_att'])
                                        quota_sniper = 0
                                    else:
                                        stake_euro = 0
                                        quota_sniper = res['q_req']

                                    with open(config.FILE_PENDING, 'a', newline='', encoding='utf-8') as f:
                                        csv.writer(f).writerow(['CALCIO', datetime.now().strftime("%Y-%m-%d %H:%M"), converti_orario(event['commence_time']), league, f"{home} vs {away}", sel_name, b['title'], res['q_att'], res['q_real'], q_scalp, quota_sniper, f"{label_status} {res['val']}%", stake_euro, 'APERTO', '', ''])
                                    
                                    emoji = "🟢" if res['status'] == "VALUE" else "🟡"
                                    msg_stake = f"{stake_euro}€" if stake_euro > 0 else f"ATTENDI {quota_sniper}"
                                    msg = f"{emoji} CALCIO: {sel_name}\n🆚 {home} vs {away}\n🔹 INGRESSO: {res['q_att']}\n📉 PINNACLE: {res['q_real']}\n💰 AZIONE: {msg_stake}"
                                    send_telegram(msg)
        except Exception as e:
            print(f"❌ ERRORE NEL LOOP LEGA: {e}")

    print(f"--- ✅ SCANSIONE TERMINATA. Totale eventi analizzati: {total_events} ---")

if __name__ == "__main__":
    scan_calcio()
