from playwright.sync_api import sync_playwright
import json
import time

LOC = {"lat": "28.57", "lng": "77.32"}
KEYWORDS = ["milk", "bread", "eggs", "butter", "cheese"]

print("=== BLINKIT FETCH ===\n")

results = {}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    api_results = []

    def handle_response(resp):
        url = resp.url
        if "layout/search" in url or "/v1/" in url:
            try:
                data = resp.json()
                if data.get("is_success"):
                    api_results.append(data)
            except:
                pass

    page.on("response", handle_response)

    for kw in KEYWORDS:
        print(f"{kw}: ", end="")
        api_results.clear()

        # Go to web page URL (not direct API)
        url = f"https://blinkit.com/s/?q={kw}&lat={LOC['lat']}&lon={LOC['lng']}"
        page.goto(url, wait_until="networkidle", timeout=30000)
        time.sleep(2)

        inv = 0
        pid = ""
        name = ""
        for data in api_results:
            for snippet in data.get("response", {}).get("snippets", []):
                d = snippet.get("data", {})
                inv = d.get("inventory", 0)
                pid = d.get("identity", {}).get("id", "")
                name = d.get("name", {}).get("text", "")
                if inv > 0:
                    break
            if inv > 0:
                break

        if inv > 0:
            print(f"{inv} (pid: {pid}) - {name}")
            results[kw] = {"inventory": inv, "product_id": pid}
        else:
            print(f"no data ({len(api_results)} responses)")

        time.sleep(0.5)

    browser.close()

print(f"\n=== RESULTS ===")
print(results)

print(f"\n=== COMPARISON ===")
baseline = json.load(open("inventory_data/baseline/blinkit_fast_baseline.json"))
for kw in KEYWORDS:
    old = baseline.get(kw, {}).get("inventory", "?")
    new = results.get(kw, {}).get("inventory", "?")
    status = "SAME" if old == new else "CHANGED"
    print(f"{kw}: baseline={old}, now={new} [{status}]")