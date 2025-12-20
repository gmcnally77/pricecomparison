import os
import sys
import requests
import difflib
from supabase import create_client, Client

# ==========================================
# CONFIGURATION LOAD
# ==========================================
# Logic: Look for config.py in backend/ or root/

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

try:
    import config
except ImportError:
    # Fallback: Try loading from backend folder specifically if running from root
    sys.path.append(os.path.join(os.getcwd(), 'backend'))
    try:
        import config
    except ImportError:
        print("!! ERROR: Could not find 'config.py'.")
        exit(1)

# Map config variables (Flexible Mapping)
SUPABASE_URL = getattr(config, 'SUPABASE_URL', None)
ODDS_API_KEY = getattr(config, 'ODDS_API_KEY', None)

# We check for SERVICE_ROLE_KEY first, but fallback to SUPABASE_KEY if that's what you named it
SUPABASE_KEY = getattr(config, 'SUPABASE_SERVICE_ROLE_KEY', getattr(config, 'SUPABASE_KEY', None))

# Validation
if not all([SUPABASE_URL, SUPABASE_KEY, ODDS_API_KEY]):
    print("!! ERROR: Missing variables in config.py")
    print(f"   URL: {'OK' if SUPABASE_URL else 'MISSING'}")
    print(f"   KEY: {'OK' if SUPABASE_KEY else 'MISSING'}")
    print(f"   ODDS: {'OK' if ODDS_API_KEY else 'MISSING'}")
    exit(1)

# Initialize Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==========================================
# CONSTANTS
# ==========================================
MATCH_THRESHOLD = 0.85
SPORT_KEY = 'mma_mixed_martial_arts'
TARGET_BOOKIES = ['pinnacle', 'bet365', 'paddypower']

# ==========================================
# HELPER FUNCTIONS
# ==========================================

def normalize_text(text: str) -> str:
    if not text: return ""
    return text.lower().strip()

def get_best_match(target_name: str, db_candidates: list):
    """
    Returns: (best_match_row, score)
    """
    normalized_target = normalize_text(target_name)
    best_score = 0.0
    best_row = None
    
    for row in db_candidates:
        db_name_clean = normalize_text(row.get('fighter_name', ''))
        if not db_name_clean: continue
            
        score = difflib.SequenceMatcher(None, normalized_target, db_name_clean).ratio()
        
        if score > best_score:
            best_score = score
            best_row = row

    return best_row, best_score

# ==========================================
# MAIN INGESTION SCRIPT
# ==========================================

def ingest_odds():
    print(">> Starting Ingestion Cycle...")
    
    # 1. Fetch DB Active Selections
    try:
        print(".. Fetching active selections from Supabase")
        db_response = supabase.table('mma_prices').select('*').neq('market_status', 'CLOSED').execute()
        db_rows = db_response.data
        if not db_rows:
            print("!! No active markets found in DB. Exiting.")
            return
        print(f">> Loaded {len(db_rows)} active selections from DB.")
    except Exception as e:
        print(f"!! Supabase Error: {e}")
        print("   (Hint: Check if your SUPABASE_KEY has write permissions)")
        return

    # 2. Fetch Odds API
    url = f'https://api.the-odds-api.com/v4/sports/{SPORT_KEY}/odds'
    params = {
        'apiKey': ODDS_API_KEY,
        'regions': 'uk,eu',
        'markets': 'h2h',
        'oddsFormat': 'decimal'
    }

    try:
        print(f".. Fetching odds from API for {SPORT_KEY}")
        response = requests.get(url, params=params)
        data = response.json()
        
        if 'message' in data:
            print(f"!! API Error: {data['message']}")
            return
        print(f">> API returned {len(data)} events.")

    except Exception as e:
        print(f"!! API Request Error: {e}")
        return

    # 3. Fuzzy Match & Map
    updates = []
    
    for event in data:
        for bookmaker in event['bookmakers']:
            bookie_key = bookmaker['key'].lower()
            
            if not any(t in bookie_key for t in TARGET_BOOKIES):
                continue
                
            for market in bookmaker['markets']:
                if market['key'] != 'h2h': continue
                
                for outcome in market['outcomes']:
                    api_name = outcome['name']
                    api_price = outcome['price']
                    
                    match_row, score = get_best_match(api_name, db_rows)
                    
                    # Log interesting matches
                    if score > 0.75:
                        status = "[MATCH]" if score >= MATCH_THRESHOLD else "[FAIL]"
                        # print(f"{status} {api_name} == {match_row['fighter_name']} ({score:.2f})")
                    
                    if score >= MATCH_THRESHOLD and match_row:
                        update_payload = {}
                        if 'pinnacle' in bookie_key: update_payload['price_pinnacle'] = api_price
                        elif 'bet365' in bookie_key: update_payload['price_bet365'] = api_price
                        elif 'paddypower' in bookie_key: update_payload['price_paddy'] = api_price
                        
                        if update_payload:
                            update_payload['id'] = match_row['id']
                            updates.append(update_payload)

    # 4. Batch Updates
    if updates:
        print(f">> Processing {len(updates)} updates...")
        
        # Deduplicate: Merge updates for same ID
        merged_updates = {}
        for up in updates:
            uid = up['id']
            if uid not in merged_updates:
                merged_updates[uid] = up
            else:
                merged_updates[uid].update(up)
        
        final_list = list(merged_updates.values())
        
        success_count = 0
        for up in final_list:
            try:
                supabase.table('mma_prices').update(up).eq('id', up['id']).execute()
                success_count += 1
            except Exception as e:
                print(f"!! Write Error ID {up['id']}: {e}")
                
        print(f">> SUCCESS: synced {success_count} selections.")
    else:
        print(">> Spy Report: No matches found above threshold.")

if __name__ == "__main__":
    ingest_odds()