import requests, csv, os, config
from datetime import datetime

# --- CONFIGURAZIONE DEBUG ---
API_KEY = "78f03ed8354c09f7ac591fe7e105deda"

def scan_tennis():
    print(f"--- 🕵️‍♂️ SCANNER INVESTIGATIVO TENNIS - {datetime.now()} ---")
    
    # Chiediamo TUTTI gli sport
    url = 'https://api.the-odds-api.com/v4/sports'
    try:
        resp = requests.get(url, params={'apiKey': API_KEY, 'all': 'true'})
        data = resp.json()
        
        print(f"📡 Totale Sport Ricevuti: {len(data)}")
        
        tennis_items = []
        target_found = False

        print("\n--- 🎾 ELENCO COMPLETO CHIAVI TENNIS TROVATE ---")
        for s in data:
            # Stampiamo TUTTO ciò che è tennis, senza filtri
            if 'tennis' in s['key'].lower() or 'tennis' in s['title'].lower():
                tennis_items.append(s)
                print(f"🔹 KEY: {s['key']}  |  TITLE: {s['title']}")
                
                # Cerca specificamente i tornei di questa settimana
                title_lower = s['title'].lower()
                if 'montpellier' in title_lower or 'abu dhabi' in title_lower or 'dallas' in title_lower or 'cordoba' in title_lower:
                    print(f"   🔥 TROVATO TARGET ATTIVO: {s['title']} !!!")
                    target_found = True

        print("------------------------------------------------")
        print(f"Totale voci Tennis: {len(tennis_items)}")
        
        if not target_found:
            print("❌ ALLARME: I tornei settimanali (Montpellier, Abu Dhabi, ecc.) NON sono nella lista!")
            print("Possibili cause: L'API li chiama in modo diverso o non sono coperti dal piano.")
        else:
            print("✅ I tornei ci sono! Ora sappiamo come si chiamano.")

    except Exception as e:
        print(f"Errore: {e}")

if __name__ == "__main__":
    scan_tennis()
