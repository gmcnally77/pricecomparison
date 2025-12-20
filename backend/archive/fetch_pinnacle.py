import requests
import config
import time
from supabase import create_client, Client

# 1. SETUP
# SECURE FIX: Read from config, do not hardcode
API_KEY = config.ODDS_API_KEY 
SPORT = 'mma_mixed_martial_arts'
REGIONS = 'eu'
MARKETS = 'h2h' 

supabase: Client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

def normalize(name):
    return name.lower().replace(" ", "").replace("'", "").replace("-", "").replace(".", "")

def fetch_sharp_odds():
    print(f">> 🕵️  Spying on Pinnacle (Strict Mode)...")
    
    # Wipe old data before fetching
    try:
        supabase.table('mma_prices').update({'bookie_price': None, 'bookie_name': None}).neq('id', 0).execute()
    except: pass

    try:
        url = f'https://api.the-odds-api.com/v4/sports/{SPORT}/odds'
        params = {'api_key': API_KEY, 'regions': REGIONS, 'markets': MARKETS, 'oddsFormat': 'decimal'}
        response = requests.get(url, params=params)
        data = response.json()
        
        if 'message' in data: 
            print(f"!! API Error: {data['message']}")
            return

        db_rows = supabase.table('mma_prices').select('*').neq('market_status', 'CLOSED').execute()
        db_map = {normalize(row['fighter_name']): row['id'] for row in db_rows.data}
        
        updates = []
        for event in data:
            sharp_book = next((b for b in event['bookmakers'] if 'pinnacle' in b['key'].lower()), None)
            
            if sharp_book:
                for outcome in sharp_book['markets'][0]['outcomes']:
                    clean = normalize(outcome['name'])
                    if clean in db_map:
                        updates.append({
                            'id': db_map[clean],
                            'bookie_price': outcome['price'],
                            'bookie_name': sharp_book['title']
                        })
        
        if updates:
            for up in updates:
                supabase.table('mma_prices').update(up).eq('id', up['id']).execute()
            print(f">> Spy Report: {len(updates)} confirmed Pinnacle prices synced.")
        else:
            print(">> Spy Report: Pinnacle has no lines matching your feed.")
            
    except Exception as e:
        print(f"!! Spy Error: {e}")

if __name__ == "__main__":
    fetch_sharp_odds()