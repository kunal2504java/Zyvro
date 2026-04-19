"""
Blinkit Inventory Drop Tracker - Noida Sector 104
1 hour monitoring, 5 min intervals
"""
import os, json, re, time
from datetime import datetime
from playwright.sync_api import sync_playwright

LOC = {"lat": "28.57", "lng": "77.32"}  # Noida Sector 104
KEYWORDS = ["milk", "bread", "eggs", "butter", "cheese"]
BASELINE_FILE = "blinkit_inventory_baseline.json"

def load_baseline():
    if os.path.exists(BASELINE_FILE):
        with open(BASELINE_FILE) as f:
            return json.load(f)
    return {}

def save_baseline(data):
    with open(BASELINE_FILE, "w") as f:
        json.dump(data, f, indent=2)

def main():
    print(f"\n{'#'*60}")
    print("BLINKIT INVENTORY DROP TRACKER")
    print(f"Location: Noida Sector 104 (28.57, 77.32)")
    print(f"{'#'*60}\n")
    
    baseline = load_baseline()
    print(f"Baseline: {baseline}\n")
    
    poll_num = 0
    drops_found = []
    
    while poll_num < 12:  # 12 polls x 5 min = 1 hour
        poll_num += 1
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"\n--- Poll #{poll_num} at {ts} ---")
        
        api_data = []
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            
            def handle_response(response):
                try:
                    if "layout/search" in response.url or "/v1/" in response.url:
                        data = response.json()
                        if data.get("is_success"):
                            api_data.append(data)
                except:
                    pass
            
            page.on("response", handle_response)
            
            for kw in KEYWORDS:
                print(f"  {kw}: ", end="")
                
                url = f"https://blinkit.com/s/?q={kw}&lat={LOC['lat']}&lon={LOC['lng']}"
                page.goto(url, wait_until="networkidle", timeout=30000)
                time.sleep(4)
                
                inv = 0
                for resp in api_data:
                    for snippet in resp.get("response", {}).get("snippets", []):
                        d = snippet.get("data", {})
                        inv = d.get("inventory", 0)
                        if inv > 0:
                            break
                    if inv > 0:
                        break
                
                if inv > 0:
                    if kw in baseline:
                        old = baseline[kw]
                        if inv < old:
                            print(f"DROP! {old} -> {inv} (Δ={old-inv})")
                            drops_found.append({
                                "keyword": kw,
                                "old": old,
                                "new": inv,
                                "drop": old - inv,
                                "time": ts,
                                "poll": poll_num
                            })
                        else:
                            print(f"{inv} (stable)")
                    else:
                        print(f"{inv} (baseline)")
                        baseline[kw] = inv
                else:
                    print("no data")
                
                api_data.clear()
                time.sleep(0.5)
            
            browser.close()
            save_baseline(baseline)
        
        if poll_num < 12:
            print(f"\nWaiting 5 min...")
            time.sleep(300)
    
    print(f"\n{'='*60}")
    print("RESULTS - BLINKIT NOIDA SECTOR 104")
    print(f"{'='*60}")
    
    print(f"\nBaseline:")
    for k, v in baseline.items():
        print(f"  {k}: {v}")
    
    print(f"\nDrops detected: {len(drops_found)}")
    for d in drops_found:
        print(f"  {d['keyword']}: {d['old']} -> {d['new']}")
    
    if drops_found:
        with open(f"blinkit_drops_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
            json.dump(drops_found, f, indent=2)
        print("\nSaved to blinkit_drops_*.json")

if __name__ == "__main__":
    main()