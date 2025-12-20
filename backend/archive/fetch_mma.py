import betfairlightweight
from betfairlightweight import filters
import pandas as pd
import config
import time
import requests
import traceback
from datetime import datetime, timezone
from supabase import create_client, Client

# 1. SETUP
print(f">> Connecting to Supabase at {config.SUPABASE_URL}...")
supabase: Client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

print(f">> Initializing Betfair Client for user: {config.USERNAME}...")
trading = betfairlightweight.APIClient(
    username=config.USERNAME,
    password=config.PASSWORD,
    app_key=config.APP_KEY,
    certs=config.CERTS_PATH
)

# PINNACLE CONFIG (SECURE)
ODDS_API_KEY = config.ODDS_API_KEY
SPORT = 'mma_mixed_martial_arts'

opening_prices_cache = {}
last_pinnacle_update = 0

def normalize(name):
    return name.lower().replace(" ", "").replace("'", "").replace("-", "").replace(".", "")

def fetch_sharp_odds():
    print(f">> 🕵️  Spying on Pinnacle (Strict Mode)...")
    try:
        # Wipe old prices first
        supabase.table('mma_prices').update({'bookie_price': None, 'bookie_name': None}).neq('id', 0).execute()

        url = f'https://api.the-odds-api.com/v4/sports/{SPORT}/odds'
        params = {'api_key': ODDS_API_KEY, 'regions': 'eu', 'markets': 'h2h', 'oddsFormat': 'decimal'}
        response = requests.get(url, params=params)
        data = response.json()
        
        if 'message' in data: 
            print(f"!! Spy API Message: {data['message']}")
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
            
    except Exception as e:
        print(f"!! Spy Error: {e}")

def load_existing_openers():
    try:
        response = supabase.table('mma_prices').select('fighter_name, opening_price').execute()
        if response.data:
            for row in response.data:
                if row.get('opening_price'):
                    opening_prices_cache[row['fighter_name']] = row['opening_price']
    except: pass

def chunker(seq, size):
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))

def get_mma_prices():
    # 3. LOGIN DEBUGGING
    if not trading.session_token:
        try:
            # print(">> Attempting Betfair Login...") 
            trading.login()
            # print(f">> Login Successful")
        except Exception as e:
            print(f"!! BETFAIR LOGIN FAILED: {e}")
            return

    # 4. FIND MMA ID
    try:
        event_types = trading.betting.list_event_types(filter=filters.market_filter(text_query="Mixed Martial Arts"))
        if not event_types: 
            return
        mma_id = event_types[0].event_type.id
    except Exception as e:
        return

    # 5. FETCH MARKETS
    now = pd.Timestamp.now(tz='UTC')
    market_filter = filters.market_filter(
        event_type_ids=[mma_id],
        market_type_codes=['MATCH_ODDS'],
        market_start_time={
            'from': (now - pd.Timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),          
            'to': (now + pd.Timedelta(days=90)).strftime("%Y-%m-%dT%H:%M:%SZ") 
        }
    )

    try:
        markets = trading.betting.list_market_catalogue(
            filter=market_filter, max_results=200, 
            market_projection=['MARKET_START_TIME', 'EVENT', 'RUNNER_METADATA'],
            sort='FIRST_TO_START' 
        )
    except Exception as e:
        return

    if not markets: 
        return

    # 6. PROCESS DATA
    active_market_ids = set()
    update_time = datetime.now(timezone.utc).isoformat()
    market_ids = [m.market_id for m in markets]
    rows_to_insert = []
    
    try:
        for batch in chunker(market_ids, 5):
            market_books = trading.betting.list_market_book(market_ids=batch, price_projection=filters.price_projection(price_data=['EX_BEST_OFFERS', 'EX_TRADED'], virtualise=True))
            for book in market_books:
                active_market_ids.add(book.market_id) 
                market_info = next((m for m in markets if m.market_id == book.market_id), None)
                if not market_info: continue
                
                for runner in book.runners:
                    if runner.status == 'ACTIVE':
                        runner_details = next((r for r in market_info.runners if r.selection_id == runner.selection_id), None)
                        if not runner_details: continue
                        
                        fighter_name = runner_details.runner_name
                        back_price = runner.ex.available_to_back[0].price if runner.ex.available_to_back else 0.0
                        lay_price = runner.ex.available_to_lay[0].price if runner.ex.available_to_lay else 0.0

                        if fighter_name not in opening_prices_cache and back_price > 0 and (book.total_matched or 0) > 500:
                            opening_prices_cache[fighter_name] = back_price
                        
                        rows_to_insert.append({
                            "market_id": book.market_id,
                            "fight_name": market_info.event.name,
                            "fighter_name": fighter_name,
                            "back_price": back_price,
                            "lay_price": lay_price,
                            "volume": int(book.total_matched or 0),
                            "opening_price": opening_prices_cache.get(fighter_name, None),
                            "start_time": market_info.market_start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                            "in_play": book.inplay,
                            "market_status": book.status,
                            "last_updated": update_time 
                        })
    except Exception as e:
        traceback.print_exc()

    if rows_to_insert:
        try:
            supabase.table('mma_prices').upsert(rows_to_insert, on_conflict='market_id, fighter_name').execute()
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚡ Synced {len(rows_to_insert)} prices.")
        except Exception as e: print(f"!! Database Upsert Error: {e}")

    # GARBAGE COLLECTION
    try:
        db_open = supabase.table('mma_prices').select('market_id').neq('market_status', 'CLOSED').execute()
        ghost_ids = [row['market_id'] for row in db_open.data if row['market_id'] not in active_market_ids]
        if ghost_ids:
            supabase.table('mma_prices').update({'market_status': 'CLOSED', 'in_play': False}).in_('market_id', ghost_ids).execute()
    except: pass

if __name__ == "__main__":
    print("--- STARTING TURBO ENGINE ---")
    load_existing_openers() 
    while True:
        get_mma_prices()
        
        if time.time() - last_pinnacle_update > 60:
            fetch_sharp_odds()
            last_pinnacle_update = time.time()
            
        time.sleep(1)