import os
import httpx
from dotenv import load_dotenv
from backend.database.db import engine, Base

load_dotenv()

def reset_system():
    print("--- 1. Resetting Vectorize Hindsight Cloud Memory Bank ---")
    api_key = os.getenv("HINDSIGHT_API_KEY", "").strip()
    bank_id = os.getenv("HINDSIGHT_BANK_ID", "incident-response-bank").strip()
    api_url = os.getenv("HINDSIGHT_API_URL", "https://api.hindsight.vectorize.io").rstrip('/')
    
    if api_key and not api_key.startswith("your_"):
        url = f"{api_url}/v1/default/banks/{bank_id}"
        headers = {"Authorization": f"Bearer {api_key}"}
        try:
            res = httpx.delete(url, headers=headers)
            print(f"Hindsight Cloud Reset Response: {res.status_code}")
        except Exception as e:
            print(f"Hindsight Reset Warning: {e}")

    print("\n--- 2. Resetting SQLite Application Database ---")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("SQLite DB Reset: All incident records dropped and recreated clean.")
    print("\n[SUCCESS] System is 100% clean and ready for fresh testing!")

if __name__ == "__main__":
    reset_system()