import os
import random  # <--- This was missing
from dotenv import load_dotenv
from supabase import create_client, Client
from pathlib import Path

# 1. Force find the .env file
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

# DEBUG: Check if keys exist
if not url:
    print("CRITICAL ERROR: Could not find SUPABASE_URL in .env file")
    print(f"Looking in: {os.getcwd()}")
    exit()

supabase: Client = create_client(url, key)

def update_market():
    print("running update...")

    # 2. Simulate "Live" Data
    new_back_price = round(random.uniform(1.80, 1.95), 2)
    
    data = {
        "fight_name": "Brandon Moreno v Tatsuro Taira",
        "fighter_name": "Tatsuro Taira",
        "back_price": new_back_price,
        "lay_price": round(new_back_price + 0.02, 2),
        "market_id": "1.22334455" 
    }

    # 3. The "Upsert"
    try:
        response = supabase.table('mma_prices').upsert(data, on_conflict='market_id, fighter_name').execute()
        print(f"Update Success: Taira Back Price is now {new_back_price}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    update_market()