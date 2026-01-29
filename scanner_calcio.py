import requests, csv, os, config, pandas as pd
from datetime import datetime
import dateutil.parser

# --- DATI TELEGRAM ---
TELEGRAM_TOKEN = "8145327630:AAHJC6vDjvGUyPT0pKw63fyW53hTl_F873U"
TELEGRAM_CHAT_ID = "5562163433"

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try: requests.get(url, params={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
    except: pass

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

# --- FUNZIONE WATCHDOG (Cane da Guardia) ---
def check_watchdog(event_name, current_pinnacle_odds, trade_row):
    """
    Controlla se la quota Pinnacle è peggiorata rispetto all'ingresso.
    trade_row è la riga del CSV relativa a questo evento.
    """
    try:
        ingresso_betfair = float(trade_row['Quota_Ingresso'])
        pinna_inziale = float(trade_row['Pinnacle_Iniziale'])
        sel = trade_row['Selezione']
        
        # Troviamo la quota attuale di Pinnacle per la selezione specifica
        # current_pinnacle_odds è un dizionario {'Home': x, 'Draw': y, 'Away': z}
        quota_pinna_now = 0
        if sel in current_pinnacle_odds:
            quota_pinna_now = current_pinnacle_odds[sel]
        elif sel == 'Pareggio' and 'Draw' in current_pinnacle_odds:
            quota_pinna_now = current_pinnacle_odds['Draw']
        else:
            # Selezione non trovata o nomi diversi, proviamo a mappare
            if 'Home' in str(sel) or trade_row['Match'].split(' vs ')[0] in str(sel): quota_pinna_now = current_pinnacle_odds['Home']
            elif 'Away' in str(sel) or trade_row['Match'].split(' vs ')[1] in str(sel): quota_pinna_now = current_pinnacle_odds['Away']

        if quota_pinna_now > 0:
            # 1. DRIFT GRAVE: Pinnacle ora dice che vale MENO di quanto l'abbiamo pagata
            if quota_pinna_now >= ingresso_betfair:
                msg = f"🔴 ALLARME STOP LOSS: {event_name}\nLa quota Pinnacle ({quota_pinna_now}) ha superato il tuo ingresso ({ingresso_betfair})!\nIl valore matematico è perso.\n👉 CHIUDI SUBITO IN PERDITA."
                send_telegram(msg)
            
            # 2. DRIFT LIEVE: Pinnacle si è alzato molto rispetto all'inizio, ma c'è ancora margine
            elif quota_pinna_now > (pinna_inziale * 1.05): # Se salita del 5%
                msg = f"⚠️ WARNING DRIFT: {event_name}\nPinnacle si sta alzando: {pinna_inziale} ➡️ {quota_pinna_now}.\nMonitora attentamente, valuta uscita anticipata."
                send_telegram(msg)

    except Exception as e:
        pass # Evitiamo blocchi se i dati non sono leggibili

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
    # Intestazione CSV (Con colonna "Pinnacle_Iniziale")
    header = ['Sport', 'Data_Scan', 'Orario_Match', 'Torneo', 'Match', 'Selezione', 'Bookmaker', 'Quota_Ingresso', 'Pinnacle_Iniziale', 'Target_Scalping', 'Valore_%', 'Stake_Euro', 'Stato_Trade', 'Esito_Finale', 'Profitto_Reale']
    
    # Carichiamo i trade aperti per il Watchdog
    open_trades = []
    if os.path.exists(config.FILE_PENDING):
        try:
            df = pd.read_csv(config.FILE_PENDING)
            # Normalizziamo i nomi colonne se necessario
            if 'Stato_Trade' in df.columns:
                open_trades = df[df['Stato_Trade'] == 'APERTO'].to_dict('records')
        except: pass
    else:
         with open(config.FILE_PENDING, 'w', newline='', encoding='utf-8') as f:
            csv.writer(f).writerow(header)

    leagues = [
        'soccer_italy_serie_a', 'soccer_england_premier_league', 'soccer_spain_la_liga', 
        'soccer_france_ligue_one', 'soccer_germany_bundesliga',
        'soccer_uefa_champions_league', 'soccer_uefa_europa_league', 'soccer_uefa_europa_conference_league'
    ]
    
    found_any = False
    for league in leagues:
        try:
            resp = requests.get(f'https://api.the-odds-api.com/v4/sports/{league}/odds', params={'apiKey': config.API_KEY, 'regions': config.REGIONS, 'markets': 'h2h', 'oddsFormat': 'decimal'})
            if resp.status_code != 200: continue
            
            for event in resp.json():
                home, away = event['home_team'], event['away_team']
                match_name = f"{home} vs {away}"
                
                # 1. ESTRAZIONE QUOTE PINNACLE (Base per tutto)
                pinna_raw = {}
                p_map = {} # Mapping pulito Home/Draw/Away
                for b in event['bookmakers']:
                    if b['key'] == 'pinnacle':
                        for m in b['markets']:
                            if m['key'] == 'h2h':
                                for o in m['outcomes']: pinna_raw[o['name']] = o['price']
                
                if len(pinna_raw) >= 3:
                     try: p_map = {'Home': pinna_raw[home], 'Draw': pinna_raw['Draw'], 'Away': pinna_raw[away]}
                     except: pass

                # --- WATCHDOG LOGIC ---
                # Se abbiamo quote Pinnacle e ci sono trade aperti su questo match, controlliamo il drift
                if p_map:
                    for trade in open_trades:
                        if trade['Match'] == match_name:
                            check_watchdog(match_name, p_map, trade)

                # --- SCANNING LOGIC (Nuove opportunità) ---
                if len(pinna_raw)<3: continue
                
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
                                # Verifichiamo che non sia già nel CSV per non duplicare la notifica
                                gia_presente = False
                                for t in open_trades:
                                    if t['Match'] == match_name and t['Selezione'] == res['sel']: gia_presente = True
                                
                                if not gia_presente:
                                    sel_name = home if res['sel']=='Home' else (away if res['sel']=='Away' else 'Pareggio')
                                    label_status = f"🟢 {res['status']}" if res['status']=="VALUE" else f"🟡 {res['status']}"
                                    
                                    stake_info = ""
                                    q_scalp = 0
                                    if res['status'] == "VALUE":
                                        euro = calcola_stake(res['val'], res['q_att'])
                                        stake_info = f"{euro}€"
                                        q_scalp = calcola_target_scalping(res['q_att'])
                                    else:
                                        stake_info = f"TARGET: {res['q_req']}"
                                        q_scalp = calcola_target_scalping(res['q_req'])

                                    with open(config.FILE_PENDING, 'a', newline='', encoding='utf-8') as f:
                                        csv.writer(f).writerow(['CALCIO', datetime.now().strftime("%Y-%m-%d %H:%M"), converti_orario(event['commence_time']), league, f"{home} vs {away}", sel_name, b['title'], res['q_att'], res['q_real'], q_scalp, f"{label_status} {res['val']}%", stake_info, 'APERTO', '', ''])
                                    
                                    emoji = "🟢" if res['status'] == "VALUE" else "🟡"
                                    msg = f"{emoji} CALCIO NUOVO:\n⚽ {home} vs {away}\n👉 {sel_name}\n\n🔹 BETFAIR: {res['q_att']}\n📉 PINNACLE (Ora): {res['q_real']}\n🎯 EXIT SCALP: {q_scalp}\n💰 STAKE: {stake_info}"
                                    send_telegram(msg)
                                    found_any = True
        except: pass
