import os
from dotenv import load_dotenv
from pathlib import Path
import socket
from urllib.parse import urlparse

# 1. Force Load .env from Root
base_dir = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=base_dir / '.env')

url = os.getenv("SUPABASE_URL")

print("--- DIAGNOSTIC REPORT ---")

# CHECK 1: Did we find the file?
if not url:
    print("❌ ERROR: .env file not found or SUPABASE_URL is empty.")
    exit()
else:
    # Print the URL safely (hide the middle) to check for spaces/quotes
    clean_url = url.strip()
    print(f"✅ FOUND URL: '{clean_url}'")
    if clean_url != url:
        print("⚠️  WARNING: Your URL has hidden spaces at the start/end!")

# CHECK 2: Can we find the server on the internet?
try:
    parsed = urlparse(clean_url)
    hostname = parsed.hostname
    print(f"Testing Hostname: '{hostname}'")
    
    if not hostname:
        print("❌ ERROR: Could not extract hostname. Is the URL format 'https://...'?")
    else:
        ip = socket.gethostbyname(hostname)
        print(f"✅ DNS SUCCESS: Resolved to {ip}")
        print(">> The internet connection to Supabase is GOOD.")

except Exception as e:
    print(f"❌ DNS FAILED: {e}")
    print(">> This means your computer cannot find the Supabase address.")
    print(">> Likely cause: Database is still waking up, or a typo in the URL.")