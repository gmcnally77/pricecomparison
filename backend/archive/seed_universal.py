import os
import sys
import requests
from supabase import create_client, Client

# ==========================================
# CONFIGURATION
# ==========================================
# Standard logic to find config.py
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

SUPABASE_URL = getattr(config, 'SUPABASE_URL', None)
SUPABASE_KEY = getattr(config, 'SUPABASE_SERVICE_ROLE_KEY', getattr(config, 'SUPABASE_KEY', None))
ODDS_API_KEY = getattr(config, 'ODDS_API_KEY', None)

if not all([SUPABASE_URL, SUPABASE_KEY, ODDS_API_KEY]):
    print("!! ERROR: Missing variables (SUPABASE_URL, SUPABASE_KEY, ODDS_API_KEY).")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==========================================
# SPORTS CONFIGURATION
# ==========================================
SPORTS_LIST = [
    'mma_mixed_martial_arts',
    'americanfootball_nfl',
    'basketball_nba'
]

def seed_universal():
    print(">> 🌍 Starting Universal Seeding (MMA, NFL, NBA)...")
    
    total_inserted = 0
    
    for sport_key in SPORTS_LIST:
        print(f"\n.. Fetching roster for: {sport_key}")
        
        # We use 'us,uk,eu' to catch all possible team names/variants
        url = f'https://api.the-odds-api.com/v4/sports/{sport_key}/odds'
        params = {
            'apiKey': ODDS_API_KEY,
            'regions': 'us,uk,eu', 
            'markets': 'h2h',
            'oddsFormat': 'decimal'
        }

        try:
            response = requests.get(url, params=params)
            data = response.json()
            
            if 'message' in data:
                print(f"   !! API Message: {data['message']}")
                continue
                
            print(f"   >> Found {len(data)} events.")
        except Exception as e:
            print(f"   !! Network Error: {e}")
            continue

        # Extract Unique Competitors (Home & Away)
        competitors = set()
        for event in data:
            competitors.add(event['home_team'])
            competitors.add(event['away_team'])

        # Insert into Supabase
        sport_count = 0
        for name in competitors:
            # We reuse 'fighter_name' for ALL sports to keep schema simple
            payload = {
                'fighter_name': name,
                'market_status': 'OPEN' 
            }
            try:
                # Check existence first to avoid duplicates
                # (Simple check to prevent unique constraint errors if you have them)
                exists = supabase.table('mma_prices').select('id').eq('fighter_name', name).execute()
                if not exists.data:
                    supabase.table('mma_prices').insert(payload).execute()
                    sport_count += 1
            except Exception as e:
                pass # Silent fail on dupes

        print(f"   + Seeded {sport_count} new selections for {sport_key}")
        total_inserted += sport_count

    print(f"\n>> 🏁 UNIVERSAL SEED COMPLETE. Total New: {total_inserted}")

if __name__ == "__main__":
    seed_universal()