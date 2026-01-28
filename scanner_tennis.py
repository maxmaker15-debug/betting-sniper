import requests, csv, os, config
from datetime import datetime
import dateutil.parser

# --- I TUOI DATI TELEGRAM ---
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
                migliore_opzione = {'sel': outcome, 'q_att': soft_price, 'q_req': quota_req, 'val': round(ev_perc, 2), 'status': status}
    return migliore_opzione

def scan_tennis():
    if os.path.exists(config.FILE_PENDING): os.remove(config.FILE_PENDING)
    if not os.path.exists(config.FILE_PENDING):
        with open(config.FILE_PENDING, 'w', newline='', encoding='utf-8') as f:
            csv.writer(f).writerow(['Sport', 'Data_Scan', 'Orario_Match', 'Torneo', 'Match', 'Selezione', 'Bookmaker', 'Quota_Netta', 'Valore_%', 'Stake_Euro', 'Esito', 'Profitto_Euro'])

    try:
        resp = requests.get('https://api.the-odds-api.com/v4/sports', params={'apiKey': config.API_KEY})
        active_tennis = [s for s in resp.json() if 'tennis' in s['key'] and 'winner' not in s['key']]
        
        for torneo in active_tennis:
            url = f'https://api.the-odds-api.com/v4/sports/{torneo["key"]}/odds'
            resp = requests.get(url, params={'apiKey': config.API_KEY, 'regions': config.REGIONS, 'markets': 'h2h', 'oddsFormat': 'decimal'})
            if resp.status_code != 200: continue
            for event in resp.json():
                home, away = event['home_team'], event['away_team']
                pinna = {}
                for b in event['bookmakers']:
                    if b['key'] == 'pinnacle':
                        for m in b['markets']:
                             if m['key']=='h2h':
                                for o in m['outcomes']: pinna[o['name']] = o['price']
                if len(pinna)<2: continue
                try: p_map = {'Home': pinna[home], 'Away': pinna[away]}
                except: continue
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
                                sel_name = home if res['sel']=='Home' else away
                                label_status = f"🟢 {res['status']}" if res['status']=="VALUE" else f"🟡 {res['status']}"
                                stake_str = f"TARGET: {res['q_req']}" if res['status']=="ATTESA" else "PUNTA SUBITO"
                                
                                with open(config.FILE_PENDING, 'a', newline='', encoding='utf-8') as f:
                                    csv.writer(f).writerow(['TENNIS', datetime.now().strftime("%Y-%m-%d %H:%M"), converti_orario(event.get('commence_time', 'N/A')), torneo['title'], f"{home} vs {away}", sel_name, b['title'], res['q_att'], f"{label_status} {res['val']}%", stake_str, '', ''])
                                
                                # NOTIFICA
                                emoji = "🟢" if res['status'] == "VALUE" else "🟡"
                                msg = f"{emoji} TENNIS ALERT!\n🎾 {home} vs {away}\n👉 {sel_name}\n📊 Quota: {res['q_att']}\n📈 Valore: {res['val']}%\n💰 Azione: {stake_str}"
                                send_telegram(msg)
    except: pass
