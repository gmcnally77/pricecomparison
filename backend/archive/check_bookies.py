import os
import sys
import requests

# ==========================================
# CONFIGURATION LOAD
# ==========================================
# Robustly find config.py in backend/ or root/
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

try:
    import config
except ImportError:
    # Fallback: Try loading from backend folder specifically
    sys.path.append(os.path.join(os.getcwd(), 'backend'))
    try:
        import config
    except ImportError:
        print("!! ERROR: Could not find 'config.py'.")
        print("   Ensure 'config.py' is in the root or 'backend/' folder.")
        exit(1)

ODDS_API_KEY = getattr(config, 'ODDS_API_KEY', None)

if not ODDS_API_KEY:
    print("!! ERROR: ODDS_API_KEY not found in config.py")
    exit(1)

# ==========================================
# DIAGNOSTIC SCRIPT
# ==========================================

def audit_available_bookmakers():
    print(">> 🕵️  Auditing Bookmaker Availability for NFL...")

    # We use 'americanfootball_nfl' as the test bed
    sport_key = 'americanfootball_nfl'
    url = f'https://api.the-odds-api.com/v4/sports/{sport_key}/odds'
    
    # We explicitly request 'uk' and 'eu' regions to cast the widest net for Bet365/Paddy
    params = {
        'apiKey': ODDS_API_KEY,
        'regions': 'uk,eu,au', 
        'markets': 'h2h',
        'oddsFormat': 'decimal'
    }

    try:
        print(f".. Requesting data from: {url}")
        print(f".. Regions: {params['regions']}")
        
        response = requests.get(url, params=params)
        data = response.json()
        
        # Check for API-level errors (e.g., plan limits, invalid key)
        if 'message' in data:
            print(f"\n!! API RETURNED ERROR: {data['message']}")
            print("   (Check your API usage or Key status)")
            return

        print(f">> API returned {len(data)} events.\n")

    except Exception as e:
        print(f"!! Connection Error: {e}")
        return

    # Sift through the data
    found_bookies = set()
    event_count = 0

    for event in data:
        event_count += 1
        for bookmaker in event['bookmakers']:
            found_bookies.add(bookmaker['key'])

    # REPORTING
    print("====== 📋 UNIQUE BOOKMAKERS FOUND IN PAYLOAD ======")
    if not found_bookies:
        print("!! NO BOOKMAKERS FOUND.")
        print("   Possibilities:")
        print("   1. Region lock (try changing regions to 'us' or 'au' in the script).")
        print("   2. Off-season (no odds currently published).")
    else:
        for key in sorted(found_bookies):
            # Highlight our targets
            if key in ['bet365', 'paddypower', 'pinnacle']:
                print(f"✅ {key}")
            else:
                print(f"   {key}")

    print("\n=================================================")
    print(f"Total Events Scanned: {event_count}")
    
    # Specific check for your missing ones
    missing = []
    if 'bet365' not in found_bookies: missing.append('bet365')
    if 'paddypower' not in found_bookies: missing.append('paddypower')
    
    if missing:
        print(f"⚠️  MISSING TARGETS: {', '.join(missing)}")
        print("   Action: specific bookmakers might be blocked in your requested region.")
    else:
        print(">> ALL SYSTEMS GO: Target bookmakers are present in the feed.")

if __name__ == "__main__":
    audit_available_bookmakers()