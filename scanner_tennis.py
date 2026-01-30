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

def check_watchdog(event_name, current_pinnacle_odds, trade_row):
    try:
        ingresso_betfair = float(trade_row['Quota_Ingresso'])
        pinna_inziale = float(trade_row['Pinnacle_Iniziale'])
        sel = trade_row['Selezione']
        
        quota_pinna_now = 0
        if sel in current_pinnacle_odds:
            quota_pinna_now = current_pinnacle_odds[sel]
        else:
            if 'Home' in str(sel) or trade_row['Match'].split(' vs ')[0] in str(sel): quota_pinna_now = current_pinnacle_odds['Home']
            elif 'Away' in str(sel) or trade_row['Match'].split(' vs ')[1] in str(sel): quota_pinna_now = current_pinnacle_odds['Away']

        if quota_pinna_now > 0:
            if quota_pinna_now >= ingresso_betfair:
                msg = f"🔴 ALLARME STOP LOSS: {event_name}\nLa quota Pinnacle ({quota_pinna_now}) ha superato il tuo ingresso ({ingresso_betfair})!"
                send_telegram(msg)
            elif quota_pinna_now > (pinna_inziale * 1.05):
                msg = f"⚠️ WARNING DRIFT: {event_name}\nPinnacle si sta alzando."
                send_telegram(msg)
    except: pass

def analizza_tennis_sniper(pinnacle_odds, soft_odds):
    try:
        inv_1 = 1 / pinnacle_odds['Home']
        inv_2 = 1 / pinnacle_odds['Away']
        margin = inv_1 + inv_2
        real_prob = {'Home': inv_1/margin, 'Away': inv_2/margin}
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
        if ev_perc > config.SOGLIA_VALUE_TENNIS: status = "VALUE"
        elif ev_perc > config.SOGLIA_SNIPER_TENNIS: status = "ATTESA"

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

def scan_tennis():
    # NUOVA INTESTAZIONE
    header = ['Sport', 'Data_Scan', 'Orario_Match', 'Torneo', 'Match', 'Selezione', 'Bookmaker', 'Quota_Ingresso', 'Pinnacle_Iniziale', 'Target_Scalping', 'Quota_Sniper_Target', 'Valore_%', 'Stake_Euro', 'Stato_Trade', 'Esito_Finale', 'Profitto_Reale']
    
    open_trades = []
    if os.path.exists(config.FILE_PENDING):
        try:
            df = pd.read_csv(config.FILE_PENDING)
            if 'Stato_Trade' in df.columns:
                open_trades = df[df['Stato_Trade'] == 'APERTO'].to_dict('records')
        except: pass
    else:
        with open(config.FILE_PENDING, 'w', newline='', encoding='utf-8') as f:
            csv.writer(f).writerow(header)

    try:
        resp = requests.get('https://api.the-odds-api.com/v4/sports', params={'apiKey': config.API_KEY})
        active_tennis = [s for s in resp.json() if 'tennis' in s['key'] and 'winner' not in s['key']]
        
        for torneo in active_tennis:
            url = f'https://api.the-odds-api.com/v4/sports/{torneo["key"]}/odds'
            resp = requests.get(url, params={'apiKey': config.API_KEY, 'regions': config.REGIONS, 'markets': 'h2h', 'oddsFormat': 'decimal'})
            if resp.status_code != 200: continue
            
            for event in resp.json():
                home, away = event['home_team'], event['away_team']
                match_name = f"{home} vs {away}"
                
                pinna_raw = {}
                p_map = {}
                for b in event['bookmakers']:
                    if b['key'] == 'pinnacle':
                        for m in b['markets']:
                             if m['key']=='h2h':
                                for o in m['outcomes']: pinna_raw[o['name']] = o['price']
                if len(pinna_raw)>=2:
                    try: p_map = {'Home': pinna_raw[home], 'Away': pinna_raw[away]}
                    except: pass
                
                if p_map:
                    for trade in open_trades:
                        if trade['Match'] == match_name:
                            check_watchdog(match_name, p_map, trade)

                if len(pinna_raw)<2: continue
                for b in event['bookmakers']:
                    if 'betfair' in b['title'].lower():
                        soft = {}
                        for m in b['markets']:
                             if m['key']=='h2h':
                                for o in m['outcomes']:
                                    if o['name']==home: soft['Home']=o['price']
                                    elif o['name']==away: soft['Away']=o['price']
                        if len(soft)==2:
                            res = analizza_tennis_sniper(p_map, soft)
                            if res:
                                gia_presente = False
                                for t in open_trades:
                                    if t['Match'] == match_name and t['Selezione'] == res['sel']: gia_presente = True
                                
                                if not gia_presente:
                                    sel_name = home if res['sel']=='Home' else away
                                    label_status = f"🟢 {res['status']}" if res['status']=="VALUE" else f"🟡 {res['status']}"
                                    
                                    stake_euro = 0
                                    quota_sniper = 0
                                    q_scalp = calcola_target_scalping(res['q_att']) if res['status'] == "VALUE" else calcola_target_scalping(res['q_req'])

                                    if res['status'] == "VALUE":
                                        stake_euro = calcola_stake(res['val'], res['q_att'])
                                    else:
                                        quota_sniper = res['q_req']
                                    
                                    with open(config.FILE_PENDING, 'a', newline='', encoding='utf-8') as f:
                                        csv.writer(f).writerow(['TENNIS', datetime.now().strftime("%Y-%m-%d %H:%M"), converti_orario(event.get('commence_time', 'N/A')), torneo['title'], f"{home} vs {away}", sel_name, b['title'], res['q_att'], res['q_real'], q_scalp, quota_sniper, f"{label_status} {res['val']}%", stake_euro, 'APERTO', '', ''])
                                    
                                    emoji = "🟢" if res['status'] == "VALUE" else "🟡"
                                    msg_stake = f"{stake_euro}€" if stake_euro > 0 else f"ATTENDI {quota_sniper}"
                                    msg = f"{emoji} TENNIS: {sel_name}\n🎾 {home} vs {away}\n🔹 INGRESSO: {res['q_att']}\n📉 PINNACLE: {res['q_real']}\n💰 AZIONE: {msg_stake}"
                                    send_telegram(msg)
    except: pass
