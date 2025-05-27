import json
import os
import requests


# SUPABASE_URL = os.getenv("SUPABASE_URL")
# SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Missing SUPABASE_URL or SUPABASE_KEY")
    exit(1)

# Load local JSON data
with open("stats.json", "r", encoding="utf-8") as f:
    data = json.load(f)

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}

url = f"{SUPABASE_URL}/rest/v1/stats"

for row in data:
    response = requests.post(url, headers=headers, json=row)
    if response.status_code in [200, 201, 204]:
        print(f"✅ Inserted: {row['name']}")
    elif response.status_code == 409:
        print(f"⚠️ Already exists: {row['name']}")
    else:
        print(f"❌ Error inserting {row['name']}: {response.text}")
