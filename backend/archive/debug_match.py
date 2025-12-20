import os
import sys
import requests
import difflib
from supabase import create_client, Client

# ==========================================
# CONFIGURATION LOAD
# ==========================================
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

try:
    import config
except ImportError:
    sys.path.append(os.path.join(os.getcwd(), 'backend'))
    try:
        import config
    except ImportError:
        print("!! ERROR: Could not find 'config.py'.")
        exit(1)

# Map config variables
SUPABASE_URL = getattr(config, 'SUPABASE_URL', None)
ODDS_API_KEY = getattr(config, 'ODDS_API_KEY', None)
SUPABASE_KEY = getattr(config, 'SUPABASE_SERVICE_ROLE_KEY', getattr(config, 'SUPABASE_KEY', None))

if not all([SUPABASE_URL, SUPABASE_KEY, ODDS_API_KEY]):
    print("!! ERROR: Missing variables in config.py")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def debug_mismatch():
    print(">> 🕵️  STARTING MATCH DIAGNOSTIC...")

    # 1. INSPECT DATABASE
    print("\n====== [1] DATABASE ROSTER (The Truth) ======")
    try:
        # Fetching the names we are trying to match against
        db_response = supabase.table('mma_prices').select('*').neq('market_status', 'CLOSED').execute()
        db_rows = db_response.data
        if not db_rows:
            print("!! DB is EMPTY. No active selections found.")
            return
        
        db_names = []
        for row in db_rows:
            # Check different possible column names
            name = row.get('fighter_name') or row.get('selection_name') or row.get('runner_name') or 'UNKNOWN_COLUMN'
            db_names.append(name)
            print(f"   DB ID {row['id']}: '{name}'")
            
    except Exception as e:
        print(f"!! Supabase Error: {e}")
        return

    # 2. INSPECT API (Ladbrokes/NFL)
    print("\n====== [2] API ROSTER (The Feed) ======")
    sport_key = 'americanfootball_nfl'
    url = f'https://api.the-odds-api.com/v4/sports/{sport_key}/odds'
    params = {
        'apiKey': ODDS_API_KEY,
        'regions': 'uk,eu', 
        'markets': 'h2h',
        'oddsFormat': 'decimal'
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()
        print(f">> API returned {len(data)} events for {sport_key}")
        
        print("\n   --- SAMPLING API NAMES (Ladbrokes) ---")
        found_names = set()
        
        for event in data:
            # Look specifically for Ladbrokes to see what THEY call the teams
            bookie = next((b for b in event['bookmakers'] if 'ladbrokes' in b['key']), None)
            if bookie:
                for market in bookie['markets']:
                    if market['key'] == 'h2h':
                        for outcome in market['outcomes']:
                            found_names.add(outcome['name'])
        
        if not found_names:
            print("!! Ladbrokes not found in this API response. Checking ANY bookie...")
            # Fallback to just printing the first bookie found
            for event in data[:5]:
                for bookmaker in event['bookmakers']:
                    for market in bookmaker['markets']:
                         for outcome in market['outcomes']:
                             found_names.add(f"{outcome['name']} (via {bookmaker['key']})")

        for name in sorted(list(found_names))[:10]: # Print top 10
            print(f"   API: '{name}'")
            
    except Exception as e:
        print(f"!! API Error: {e}")
        return

    # 3. TEST MATCHING
    print("\n====== [3] TEST MATCHING ======")
    print("Testing fuzzy match on first 5 DB items...")
    
    # Simple normalizer
    def norm(t): return t.lower().strip() if t else ""

    for db_name in db_names[:5]:
        best_score = 0
        best_match = "None"
        
        clean_db = norm(db_name)
        
        for api_name in found_names:
            clean_api = norm(api_name.split(' (via')[0]) # Strip debug suffix if added above
            score = difflib.SequenceMatcher(None, clean_db, clean_api).ratio()
            if score > best_score:
                best_score = score
                best_match = api_name
        
        print(f"   DB: '{db_name}' vs BEST API: '{best_match}' -> Score: {best_score:.2f}")

if __name__ == "__main__":
    debug_mismatch()