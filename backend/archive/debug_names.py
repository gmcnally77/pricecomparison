import os
import sys
import requests
import json

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
        exit(1)

ODDS_API_KEY = getattr(config, 'ODDS_API_KEY', None)

if not ODDS_API_KEY:
    print("!! ERROR: ODDS_API_KEY not found in config.py")
    exit(1)

# ==========================================
# DEBUG SCRIPT
# ==========================================

def scan_nfl_names():
    print(">> 🏈 Scanning NFL Names for Bet365 & PaddyPower...")

    sport_key = 'americanfootball_nfl'
    url = f'https://api.the-odds-api.com/v4/sports/{sport_key}/odds'
    params = {
        'apiKey': ODDS_API_KEY,
        'regions': 'uk,eu', # UK/EU usually covers Paddy/365 best
        'markets': 'h2h',
        'oddsFormat': 'decimal'
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        if 'message' in data:
            print(f"!! API Error: {data['message']}")
            return

        print(f">> API returned {len(data)} events.\n")

    except Exception as e:
        print(f"!! API Request Error: {e}")
        return

    # Store names sets to avoid duplicates
    bet365_names = set()
    paddy_names = set()

    target_bookies = ['bet365', 'paddypower']

    for event in data:
        for bookmaker in event['bookmakers']:
            key = bookmaker['key'].lower()
            
            # Check if this is one of our targets
            is_bet365 = 'bet365' in key
            is_paddy = 'paddypower' in key

            if not (is_bet365 or is_paddy):
                continue

            for market in bookmaker['markets']:
                if market['key'] == 'h2h':
                    for outcome in market['outcomes']:
                        name = outcome['name']
                        if is_bet365:
                            bet365_names.add(name)
                        if is_paddy:
                            paddy_names.add(name)

    # PRINT RESULTS
    print("====== BET365 NAMES ======")
    for name in sorted(bet365_names):
        print(f'"{name}"')
    
    print("\n====== PADDY POWER NAMES ======")
    for name in sorted(paddy_names):
        print(f'"{name}"')

    print("\n>> Scan Complete.")

if __name__ == "__main__":
    scan_nfl_names()