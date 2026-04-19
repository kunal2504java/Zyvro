"""
Blinkit Fast Monitor - 15 sec intervals, CSV logging
Using Playwright to hit the API properly
"""
import os, json, time
from datetime import datetime
import csv
from playwright.sync_api import sync_playwright

LOC = {"lat": "28.57", "lng": "77.32"}
KEYWORDS = ["milk", "bread", "eggs", "butter", "cheese"]
POLL_INTERVAL = 15
POLLS = 240  # 1 hour at 15 sec intervals

BASELINE_FILE = "inventory_data/baseline/blinkit_fast_baseline.json"
CSV_FILE = "inventory_data/blinkit_inventory_log.csv"

def load_baseline():
    return json.load(open(BASELINE_FILE)) if os.path.exists(BASELINE_FILE) else {}

def save_baseline(data):
    json.dump(data, open(BASELINE_FILE, "w"), indent=2)

def init_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "poll", "keyword", "inventory", "product_id", "status"])

def log_csv(ts, poll, kw, inv, pid, status):
    with open(CSV_FILE, "a", newline="") as f:
        csv.writer(f).writerow([ts, poll, kw, inv, pid, status])

def main():
    print(f"\n{'#'*60}")
    print("BLINKIT FAST MONITOR - 15s intervals + CSV")
    print(f"Location: Noida Sector 104")
    print(f"{'#'*60}\n")
    
    init_csv()
    baseline = load_baseline()
    print(f"Baseline: {baseline}\n")
    
    poll_num = 0
    drops = []
    
    while poll_num < POLLS:
        poll_num += 1
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"\n--- Poll #{poll_num} at {ts} ---")
        
        api_data = []
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            
            def handle_response(resp):
                if "layout/search" in resp.url or "/v1/" in resp.url:
                    try:
                        data = resp.json()
                        if data.get("is_success"):
                            api_data.append(data)
                    except: pass
            
            page.on("response", handle_response)
            
            for kw in KEYWORDS:
                print(f"  {kw}: ", end="")
                
                url = f"https://blinkit.com/s/?q={kw}&lat={LOC['lat']}&lon={LOC['lng']}"
                page.goto(url, wait_until="networkidle", timeout=15000)
                time.sleep(2)
                
                inv = 0
                pid = ""
                for resp in api_data:
                    for snippet in resp.get("response", {}).get("snippets", []):
                        d = snippet.get("data", {})
                        inv = d.get("inventory", 0)
                        pid = d.get("identity", {}).get("id", "")
                        if inv > 0: break
                    if inv > 0: break
                
                if inv > 0:
                    if kw in baseline:
                        old = baseline[kw]["inventory"]
                        if inv < old:
                            print(f"DROP {old}->{inv}")
                            log_csv(ts, poll_num, kw, inv, pid, f"DROP {old}->{inv}")
                            drops.append((kw, old, inv))
                        else:
                            print(f"{inv}")
                            log_csv(ts, poll_num, kw, inv, pid, "stable")
                        baseline[kw] = {"inventory": inv, "product_id": pid}
                    else:
                        print(f"base:{inv}")
                        log_csv(ts, poll_num, kw, inv, pid, "baseline")
                        baseline[kw] = {"inventory": inv, "product_id": pid}
                else:
                    print("no data")
                    log_csv(ts, poll_num, kw, 0, "", "no_data")
                
                api_data.clear()
                time.sleep(0.5)
            
            browser.close()
        
        save_baseline(baseline)
        
        if poll_num < POLLS:
            print(f"Waiting {POLL_INTERVAL}s...")
            time.sleep(POLL_INTERVAL)
    
    print(f"\n{'='*60}")
    print(f"RESULTS: {poll_num} polls done")
    print(f"Drops: {drops}")

if __name__ == "__main__":
    main()