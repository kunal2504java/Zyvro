"""
Blinkit Inventory Tracker - Properly initializes location
"""
import os
from playwright.sync_api import sync_playwright
import nest_asyncio
nest_asyncio.apply()

class BlinkitInventoryTracker:
    def __init__(self, latitude="28.6048439", longitude="77.2928391"):
        self.latitude = latitude
        self.longitude = longitude
        self.api_url = "https://blinkit.com/v1/layout/search"
        self.base_url = "https://blinkit.com"
        self.state_file = "data/blinkit_state.json"
    
    def set_location(self, latitude, longitude):
        self.latitude = latitude
        self.longitude = longitude
    
    def _get_storage_state(self):
        if os.path.exists(self.state_file):
            return self.state_file
        return None
    
    def search(self, query, limit=20):
        storage_state = self._get_storage_state()
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(storage_state=storage_state)
            page = context.new_page()
            
            # Step 1: Go to homepage first
            page.goto(self.base_url, wait_until="domcontentloaded")
            page.wait_for_timeout(3000)
            
            # Step 2: Set location via localStorage and cookies
            page.evaluate(f"""
                () => {{
                    localStorage.setItem('gr_1_lat', '{self.latitude}');
                    localStorage.setItem('gr_1_lon', '{self.longitude}');
                }}
            """)
            
            # Set cookies
            context.add_cookies([
                {"name": "gr_1_lat", "value": self.latitude, "domain": ".blinkit.com", "path": "/"},
                {"name": "gr_1_lon", "value": self.longitude, "domain": ".blinkit.com", "path": "/"},
                {"name": "gr_1_locality", "value": "1", "domain": ".blinkit.com", "path": "/"}
            ])
            
            # Step 3: Navigate to search page with location params
            search_url = f"{self.base_url}/s/?q={query}&lat={self.latitude}&lon={self.longitude}"
            page.goto(search_url, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(2000)
            
            # Step 4: Try API call
            api_response = page.evaluate(f"""
                async () => {{
                    const params = new URLSearchParams({{
                        q: "{query}",
                        search_type: "type_to_search"
                    }});
                    
                    const body = {{
                        applied_filters: null,
                        monet_assets: [{{name: "ads_vertical_banner", processed: 0, total: 0}}],
                        postback_meta: {{
                            processedGroupIds: [446538],
                            pageMeta: {{scrollMeta: [{{entitiesCount: 167}}]}},
                            excludedGroupIds: [642039, 642040, 733086, 2520540, 2143654, 1937936, 1937938, 2625128, 2625124, 2557981, 2557979]
                        }},
                        previous_search_query: "",
                        processed_rails: {{
                            similar_brand_rail: {{total_count: 1, processed_count: 1}},
                            usecase_grid_rail: {{total_count: 0, processed_count: 1}}
                        }},
                        similar_entities: [],
                        sort: "",
                        vertical_cards_processed: 11
                    }};
                    
                    try {{
                        const response = await fetch("{self.api_url}?" + params, {{
                            method: "POST",
                            headers: {{
                                "Content-Type": "application/json",
                                "Accept": "*/*"
                            }},
                            body: JSON.stringify(body)
                        }});
                        return await response.json();
                    }} catch (e) {{
                        return {{ error: e.message }};
                    }}
                }}
            """)
            
            context.storage_state(path=self.state_file)
            browser.close()
            
            if "error" in api_response:
                print(f"API Error: {api_response['error']}")
                return []
            
            return self._parse_response(api_response, limit)
    
    def _parse_response(self, data, limit):
        products = []
        
        if not data.get("is_success"):
            print(f"API Response: {data}")
            return []
        
        try:
            for snippet in data.get("response", {}).get("snippets", []):
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
                    "price": float(d.get("normal_price", {}).get("text", "₹0").replace("₹", "").replace(",", "")),
                    "mrp": float(d.get("mrp", {}).get("text", "₹0").replace("₹", "").replace(",", "")) or 0,
                    "inventory": d.get("inventory", 0),
                    "brand": d.get("brand_name", {}).get("text", ""),
                    "eta": d.get("eta_tag", {}).get("title", {}).get("text", "earliest")
                })
        except Exception as e:
            print(f"Parse error: {e}")
        
        return products


if __name__ == "__main__":
    import sys
    
    lat, lon = "28.6048439", "77.2928391"
    query = sys.argv[1] if len(sys.argv) > 1 else "milk"
    
    if len(sys.argv) > 3:
        lat, lon = sys.argv[2], sys.argv[3]
    
    tracker = BlinkitInventoryTracker(lat, lon)
    
    print(f"Tracking: {query} at {lat},{lon}")
    products = tracker.search(query, limit=10)
    
    if products:
        for p in products:
            print(f"  {p['name']} ({p['variant']}) - Rs.{p['price']} - Inventory: {p['inventory']}")
    else:
        print("No products")