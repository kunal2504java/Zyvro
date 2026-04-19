"""
Blinkit Drop Tracker - Using API Response
"""
import os, json, re, time
from datetime import datetime
from playwright.sync_api import sync_playwright

LOC = {"lat": "28.57", "lng": "77.32"}  # Noida Sector 104
KEYWORDS = ["milk", "bread", "eggs", "butter", "cheese"]
BASELINE = "blinkit_baseline.json"

def load():
    return json.load(open(BASELINE)) if os.path.exists(BASELINE) else {}

def save(data):
    json.dump(data, open(BASELINE, "w"), indent=2)

def main():
    print(f"\n=== BLINKIT NOIDA SECTOR 104 DROP TRACKER ===\n")
    
    if os.path.exists(BASELINE):
        os.remove(BASELINE)
    
    bl = load()
    print(f"Baseline: {bl}\n")
    
    poll_num = 0
    drops = []
    
    while poll_num < 3:
        poll_num += 1
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"\n--- Poll {poll_num} at {ts} ---")
        
        api_data = []
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            
            def handle_response(response):
                url = response.url
                if "layout/search" in url or "/v1/" in url:
                    try:
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
                time.sleep(3)
                
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
                        break
                
                if inv > 0:
                    if kw in bl:
                        old = bl[kw]
                        if inv < old:
                            print(f"DROP {old}->{inv}")
                            drops.append({"kw": kw, "old": old, "new": inv, "time": ts})
                        else:
                            print(f"{inv}")
                    else:
                        print(f"base:{inv}")
                        bl[kw] = inv
                else:
                    print("no data")
                
                api_data.clear()
                time.sleep(0.5)
            
            browser.close()
        
        save(bl)
        
        if poll_num < 3:
            print("Waiting 30s...")
            time.sleep(30)
    
    print(f"\n=== RESULTS ===")
    print(f"Baseline: {bl}")
    print(f"Drops: {drops}")

if __name__ == "__main__":
    main()