import requests, csv, os, config, pandas as pd
from datetime import datetime, timezone
import dateutil.parser

# --- CONFIGURAZIONE ---
API_KEY = config.API_KEY
TELEGRAM_TOKEN = "8145327630:AAHJC6vDjvGUyPT0pKw63fyW53hTl_F873U"
TELEGRAM_CHAT_ID = "5562163433"

# --- 🔒 WHITELIST BLINDATA ---
COMPETIZIONI_ELITE = [
    'soccer_italy_serie_a', 'soccer_italy_serie_b',
    'soccer_england_premier_league', 'soccer_england_championship',
    'soccer_spain_la_liga', 'soccer_spain_segunda_division',
    'soccer_germany_bundesliga', 'soccer_germany_bundesliga2',
    'soccer_france_ligue_one', 'soccer_france_ligue_two',
    'soccer_netherlands_eredivisie',
    'soccer_uefa_champions_league', 'soccer_uefa_europa_league', 'soccer_uefa_europa_conference_league'
]

# --- PARAMETRI ---
REGIONS = 'eu'
MARKETS = 'h2h'
ODDS_FORMAT = 'decimal'
MAX_ODDS_CAP = 5.00 

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try: requests.get(url, params={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
    except: pass

def converti_orario(iso_date):
    try: return dateutil.parser.parse(iso_date).strftime("%Y-%m-%d %H:%M")
    except: return iso_date

def calcola_target_scalping(quota_ingresso):
    # Target Scalping: Uscita rapida (es. 1.5% di movimento quota)
    target = quota_ingresso - (quota_ingresso * 0.015) 
    if target < 1.01: target = 1.01
    return round(target, 2)

def calcola_quota_target_teorica(prob_reale):
    # Calcola dove DOVREBBE essere la quota (Fair Value)
    try: return round(1/prob_reale, 2)
    except: return 0

# --- 🧠 IL CUORE DEL SISTEMA IBRIDO ---
def calcola_stake_ibrido(ev_perc, quota, status):
    try:
        if quota <= 1: return 0
        
        # 1. Calcolo Kelly Standard (Base Matematica)
        # Formula: (bp - q) / b
        # b = quota - 1
        # p = probabilità stimata (inclusa EV) = (1 + EV%/100) / quota
        b = quota - 1
        p = (1 + (ev_perc / 100)) / quota
        q = 1 - p
        
        if b == 0: return 0
        kelly_fraction = (b * p - q) / b
        
        # Stake base secondo Kelly puro
        stake_base = config.BANKROLL_TOTALE * config.KELLY_FRACTION * kelly_fraction
        
        # 2. LOGICA IBRIDA "VOLUME BOOST"
        stake_finale = 0
        
        if status == "VALUE":
            # Per le Value Bet (Verdi), ci fidiamo di Kelly ma garantiamo un minimo di sostanza
            stake_finale = stake_base
            # Se Kelly è troppo timido su una Value Bet, forziamo almeno il 20% dello stake massimo
            min_floor = config.STAKE_MASSIMO * 0.2
            if stake_finale < min_floor: stake_finale = min_floor

        elif status == "ATTESA":
            # Per lo Scalping (Gialli), il rischio temporale è basso, quindi ALZIAMO IL VOLUME.
            # Moltiplichiamo il suggerimento di Kelly x4 (Leva Scalping)
            stake_finale = stake_base * 4.0
            
            # SCALPING FLOOR: Non ha senso scalpare con meno di 10€ (commissioni e fatica)
            # Se lo stake calcolato è basso, forziamo un ingresso "tattico"
            # Usiamo il 40% dello Stake Massimo come base minima per lo scalping
            scalp_floor = config.STAKE_MASSIMO * 0.4 
            if stake_finale < scalp_floor: stake_finale = scalp_floor

        # 3. SICUREZZA ASSOLUTA (Hard Cap)
        # Non superiamo mai lo Stake Massimo impostato nel config, qualunque cosa dica il boost
        if stake_finale > config.STAKE_MASSIMO: stake_finale = config.STAKE_MASSIMO
        
        # Filtro spiccioli (sotto i 2 euro non ci muoviamo)
        if stake_finale < 2: stake_finale = 0
        
        return int(stake_finale)

    except Exception as e:
        return 0

def check_watchdog(event_name, current_pinnacle_odds, trade_row):
    try:
        ingresso_betfair = float(trade_row['Quota_Ingresso'])
        sel = trade_row['Selezione']
        
        quota_pinna_now = 0
        if sel in current_pinnacle_odds:
            quota_pinna_now = current_pinnacle_odds[sel]
        else:
            if 'Home' in str(sel) or trade_row['Match'].split(' vs ')[0] in str(sel): quota_pinna_now = current_pinnacle_odds.get('Home', 0)
            elif 'Away' in str(sel) or trade_row['Match'].split(' vs ')[1] in str(sel): quota_pinna_now = current_pinnacle_odds.get('Away', 0)

        if quota_pinna_now > 0:
            if quota_pinna_now >= ingresso_betfair:
                msg = f"🔴 ALLARME STOP LOSS: {event_name}\nLa quota Pinnacle ({quota_pinna_now}) ha superato il tuo ingresso ({ingresso_betfair})!\nChiudi subito."
                send_telegram(msg)
    except: pass

def scan_calcio():
    print(f"--- ⚽ SCANSIONE CALCIO (V13 HYBRID KELLY) - {datetime.now()} ---")
    
    header = ['Sport', 'Data_Scan', 'Orario_Match', 'Torneo', 'Match', 'Selezione', 'Bookmaker', 'Quota_Ingresso', 'Pinnacle_Iniziale', 'Target_Scalping', 'Quota_Sniper_Target', 'Valore_%', 'Stake_Euro', 'Stato_Trade', 'Esito_Finale', 'Profitto_Reale']
    
    open_trades = []
    if os.path.exists(config.FILE_PENDING):
        try:
            df = pd.read_csv(config.FILE_PENDING)
            if 'Stato_Trade' in df.columns: open_trades = df[df['Stato_Trade'] == 'APERTO'].to_dict('records')
        except: pass
    else:
        with open(config.FILE_PENDING, 'w', newline='', encoding='utf-8') as f: csv.writer(f).writerow(header)

    try:
        resp = requests.get('https://api.the-odds-api.com/v4/sports', params={'apiKey': API_KEY})
        if resp.status_code != 200: return
        
        soccer_leagues = [s for s in resp.json() if s['key'] in COMPETIZIONI_ELITE]
        match_analizzati = 0
        now_utc = datetime.now(timezone.utc)

        for league in soccer_leagues:
            url = f'https://api.the-odds-api.com/v4/sports/{league["key"]}/odds'
            resp = requests.get(url, params={'apiKey': API_KEY, 'regions': REGIONS, 'markets': MARKETS, 'oddsFormat': ODDS_FORMAT})
            if resp.status_code != 200: continue
            
            events = resp.json()
            for event in events:
                try:
                    commence_time = dateutil.parser.parse(event['commence_time'])
                    if commence_time <= now_utc: continue 
                except: continue

                match_analizzati += 1
                home, away = event['home_team'], event['away_team']
                match_name = f"{home} vs {away}"
                
                pinna_odds = {}
                for b in event['bookmakers']:
                    if b['key'] == 'pinnacle':
                        for m in b['markets']:
                            if m['key']=='h2h':
                                for o in m['outcomes']: pinna_odds[o['name']] = o['price']
                
                if len(pinna_odds) < 2: continue

                # Watchdog
                for trade in open_trades:
                    if trade['Match'] == match_name: check_watchdog(match_name, pinna_odds, trade)

                try:
                    inv_h = 1/pinna_odds[home]
                    inv_a = 1/pinna_odds[away]
                    inv_d = 1/pinna_odds['Draw'] if 'Draw' in pinna_odds else 0
                    margin = inv_h + inv_a + inv_d
                    real_prob = {home: inv_h/margin, away: inv_a/margin}
                    if inv_d: real_prob['Draw'] = inv_d/margin
                except: continue

                for b in event['bookmakers']:
                    if 'betfair' in b['title'].lower():
                        for m in b['markets']:
                            if m['key']=='h2h':
                                for outcome in m['outcomes']:
                                    if outcome['name'] not in real_prob: continue
                                    
                                    soft_price = outcome['price']
                                    sel_name = outcome['name']
                                    if soft_price > MAX_ODDS_CAP: continue

                                    net_price = 1 + ((soft_price - 1) * (1 - config.COMMISSIONE_BETFAIR))
                                    ev = (real_prob[sel_name] * net_price) - 1
                                    ev_perc = round(ev * 100, 2)
                                    
                                    status = None
                                    if ev_perc > config.SOGLIA_VALUE_CALCIO: status = "VALUE"
                                    elif ev_perc > config.SOGLIA_SNIPER_CALCIO: status = "ATTESA"

                                    if status:
                                        print(f"🔥 OCCASIONE CALCIO ELITE: {match_name} ({status})")
                                        
                                        # --- CALCOLO IBRIDO ---
                                        stake_euro = calcola_stake_ibrido(ev_perc, soft_price, status)
                                        q_scalp = calcola_target_scalping(soft_price)
                                        quota_teorica = calcola_quota_target_teorica(real_prob[sel_name])
                                        
                                        # Salvataggio
                                        with open(config.FILE_PENDING, 'a', newline='', encoding='utf-8') as f:
                                            csv.writer(f).writerow(['CALCIO', datetime.now().strftime("%Y-%m-%d %H:%M"), converti_orario(event.get('commence_time', 'N/A')), league['title'], match_name, sel_name, b['title'], soft_price, quota_teorica, q_scalp, 0, f"{status} {ev_perc}%", stake_euro, 'APERTO', '', ''])
                                        
                                        emoji = "🟢" if status == "VALUE" else "🟡"
                                        
                                        # Messaggio Telegram
                                        msg = (
                                            f"{emoji} CALCIO ELITE: {sel_name}\n"
                                            f"⚽ {match_name}\n"
                                            f"🏆 {league['title']}\n"
                                            f"🔹 INGRESSO: {soft_price}\n"
                                            f"📈 EV: {ev_perc}%\n"
                                            f"💰 STAKE HYBRID: {stake_euro}€\n"
                                            f"🏃 USCITA (Scalp): {q_scalp}"
                                        )
                                        
                                        if status == "ATTESA":
                                            msg += f"\n⚖️ FAIR VALUE: {quota_teorica}"
                                        
                                        send_telegram(msg)

    except Exception as e: print(f"Errore Calcio: {e}")
    print("--- SCANSIONE ELITE COMPLETATA ---")

if __name__ == "__main__":
    scan_calcio()
