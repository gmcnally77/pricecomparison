import socket
import time

print("--- CHECKING SUPABASE CONNECTION ---")

host = "zwegnmqusvswbuptycgp.supabase.co"

while True:
    try:
        ip = socket.gethostbyname(host)
        print(f"✅ ONLINE! Connected to {ip}")
        print("👉 You can now run: python3 backend/fetch_universal.py")
        break
    except socket.gaierror:
        print("Still waiting for database to wake up...")
        time.sleep(5)