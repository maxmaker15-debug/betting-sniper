import requests
import config
import json

def test_connection():
    print("--- 📡 TEST DI CONNESSIONE TENNIS ---")
    
    # 1. Verifica Crediti
    url_status = f'https://api.the-odds-api.com/v4/sports/?apiKey={config.API_KEY}'
    resp = requests.get(url_status)
    
    if resp.status_code != 200:
        print(f"❌ ERRORE API: {resp.status_code}")
        print(f"Messaggio: {resp.text}")
        return

    print(f"✅ Connessione OK. Crediti rimanenti: {resp.headers.get('x-requests-remaining', 'N/A')}")
    
    # 2. Cerca Tennis
    all_sports = resp.json()
    tennis_leagues = [s for s in all_sports if 'tennis' in s['key'].lower() and 'winner' not in s['key']]
    
    if not tennis_leagues:
        print("❌ NESSUN TORNEO TENNIS ATTIVO TROVATO NELL'API.")
        return

    print(f"✅ Trovati {len(tennis_leagues)} campionati Tennis attivi:")
    for t in tennis_leagues:
        print(f"   -> {t['title']} ({t['key']})")

    # 3. Preleva quote dal primo torneo trovato
    if tennis_leagues:
        test_league = tennis_leagues[0]['key']
        print(f"\n🔎 Analisi profonda su: {test_league}...")
        
        url_odds = f'https://api.the-odds-api.com/v4/sports/{test_league}/odds'
        resp_odds = requests.get(url_odds, params={
            'apiKey': config.API_KEY,
            'regions': 'eu',
            'markets': 'h2h',
            'oddsFormat': 'decimal'
        })
        
        matches = resp_odds.json()
        print(f"   📊 Match trovati: {len(matches)}")
        
        if len(matches) > 0:
            first_match = matches[0]
            print(f"   🎾 Esempio Match: {first_match['home_team']} vs {first_match['away_team']}")
            bookies = [b['key'] for b in first_match['bookmakers']]
            print(f"   📚 Bookmakers disponibili: {', '.join(bookies)}")
            
            if 'pinnacle' not in bookies:
                print("   ⚠️ ATTENZIONE: Pinnacle manca in questo match! Ecco perché il radar lo scarta.")
            else:
                print("   ✅ Pinnacle presente. Il radar dovrebbe vederlo se l'EV è buono.")

if __name__ == "__main__":
    test_connection()
