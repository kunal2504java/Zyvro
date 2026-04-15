"""
Blinkit Inventory - Use browser to capture the network API response
"""
import os
import json
from playwright.sync_api import sync_playwright
import nest_asyncio
nest_asyncio.apply()

class BlinkitInventory:
    def __init__(self):
        self.base_url = "https://blinkit.com"
        self.state_file = "data/blinkit_state.json"
        self.lat = "28.6048439"
        self.lon = "77.2928391"
    
    def set_location(self, lat, lon):
        self.lat = lat
        self.lon = lon
    
    def search(self, query, limit=20):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(
                storage_state=self.state_file if os.path.exists(self.state_file) else None
            )
            
            # Enable network interception
            page = context.new_page()
            
            # Capture API responses
            api_data = []
            
            def handle_response(response):
                url = response.url
                if "layout/search" in url or "/v1/" in url:
                    try:
                        data = response.json()
                        api_data.append(data)
                    except:
                        pass
            
            page.on("response", handle_response)
            
            # Navigate
            page.goto(f"{self.base_url}/s/?q={query}", wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(3000)
            
            # Save session
            context.storage_state(path=self.state_file)
            browser.close()
            
            # Parse API data for inventory
            products = []
            for api_resp in api_data:
                if api_resp.get("is_success"):
                    snippets = api_resp.get("response", {}).get("snippets", [])
                    for snippet in snippets:
                        if len(products) >= limit:
                            break
                        
                        d = snippet.get("data", {})
                        pid = d.get("identity", {}).get("id", "")
                        
                        if not pid or not pid.isdigit():
                            continue
                        
                        products.append({
                            "product_id": pid,
                            "name": d.get("name", {}).get("text", ""),
                            "variant": d.get("variant", {}).get("text", ""),
                            "price": float(d.get("normal_price", {}).get("text", "₹0").replace("₹", "").replace(",", "") or 0),
                            "inventory": d.get("inventory", 0),
                            "brand": d.get("brand_name", {}).get("text", ""),
                            "eta": d.get("eta_tag", {}).get("title", {}).get("text", "")
                        })
            
            return products


if __name__ == "__main__":
    import sys
    query = sys.argv[1] if len(sys.argv) > 1 else "milk"
    
    tracker = BlinkitInventory()
    print(f"Searching: {query}")
    
    products = tracker.search(query, limit=10)
    
    if products:
        for p in products:
            print(f"  {p['name']} ({p['variant']}) - Rs.{p['price']} - Stock: {p['inventory']}")
    else:
        print("No products found. Try logging in first.")