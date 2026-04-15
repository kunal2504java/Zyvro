"""
Blinkit Inventory Tracker - Uses Playwright to make API calls
Works without login - just needs location
"""
import os
import sys
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
        """Update location for tracking different dark stores"""
        self.latitude = latitude
        self.longitude = longitude
    
    def _get_storage_state(self):
        if os.path.exists(self.state_file):
            return self.state_file
        return None
    
    def search(self, query, limit=20):
        """Search products and get EXACT inventory"""
        storage_state = self._get_storage_state()
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            
            context = browser.new_context(
                storage_state=storage_state,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            page = context.new_page()
            
            # Navigate to base URL first to establish session
            page.goto(self.base_url, wait_until="domcontentloaded")
            
            # Set location cookies
            context.add_cookies([
                {"name": "gr_1_lat", "value": self.latitude, "domain": "blinkit.com", "path": "/"},
                {"name": "gr_1_lon", "value": self.longitude, "domain": "blinkit.com", "path": "/"},
                {"name": "gr_1_locality", "value": "1", "domain": "blinkit.com", "path": "/"}
            ])
            
            # Reload to apply cookies
            page.goto(f"{self.base_url}/s/?q={query}", wait_until="domcontentloaded")
            page.wait_for_timeout(2000)
            
            # Now try the API call from within the page context
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
                            similar_brand_rail: {{total_count: 1, processed_count: 1, processed_product_ids: [], processed_rail_entities: null}},
                            usecase_grid_rail: {{total_count: 0, processed_count: 1, processed_product_ids: [], processed_rail_entities: [{{id: "9028"}}]}}
                        }},
                        similar_entities: [],
                        sort: "",
                        vertical_cards_processed: 11
                    }};
                    
                    const response = await fetch("{self.api_url}?" + params, {{
                        method: "POST",
                        headers: {{
                            "Content-Type": "application/json",
                            "Accept": "*/*"
                        }},
                        body: JSON.stringify(body),
                        credentials: "include"
                    }});
                    
                    return await response.json();
                }}
            """)
            
            # Save session for next time
            context.storage_state(path=self.state_file)
            
            browser.close()
            
            return self._parse_response(api_response, limit)
    
    def _parse_response(self, data, limit):
        products = []
        
        if not data.get("is_success"):
            print(f"API Error: {data}")
            return []
        
        try:
            snippets = data.get("response", {}).get("snippets", [])
            
            for snippet in snippets:
                if len(products) >= limit:
                    break
                
                d = snippet.get("data", {})
                identity = d.get("identity", {})
                product_id = identity.get("id", "")
                
                if not product_id or not product_id.isdigit():
                    continue
                
                name = d.get("name", {}).get("text", "")
                variant = d.get("variant", {}).get("text", "")
                
                price_text = d.get("normal_price", {}).get("text", "₹0")
                price = float(price_text.replace("₹", "").replace(",", ""))
                
                mrp_text = d.get("mrp", {}).get("text", "")
                mrp = float(mrp_text.replace("₹", "").replace(",", "")) if mrp_text else price
                
                # EXACT INVENTORY from API!
                inventory = d.get("inventory", 0)
                merchant_id = str(d.get("merchant_id", ""))
                merchant_type = d.get("merchant_type", "express")
                eta = d.get("eta_tag", {}).get("title", {}).get("text", "earliest")
                brand = d.get("brand_name", {}).get("text", "")
                image_url = d.get("image", {}).get("url", "")
                
                rating_data = d.get("rating", {})
                rating = None
                rating_count = None
                if rating_data:
                    bar = rating_data.get("bar", {})
                    rating = bar.get("value")
                    title = bar.get("title", {})
                    if title:
                        rating_count = title.get("text", "")
                
                products.append({
                    "product_id": product_id,
                    "name": name,
                    "variant": variant,
                    "price": price,
                    "mrp": mrp,
                    "inventory": inventory,
                    "merchant_id": merchant_id,
                    "merchant_type": merchant_type,
                    "eta": eta,
                    "brand": brand,
                    "image_url": image_url,
                    "rating": rating,
                    "rating_count": rating_count
                })
                
        except Exception as e:
            print(f"Parse error: {e}")
        
        return products
    
    def track_location(self, query, location_name=None):
        """Track inventory for a single location"""
        loc_name = location_name or f"Lat:{self.latitude}, Lon:{self.longitude}"
        
        print(f"\n{'='*60}")
        print(f"Location: {loc_name}")
        print(f"{'='*60}")
        
        products = self.search(query, limit=10)
        
        for p in products:
            print(f"  - {p['name']} ({p['variant']}): Inventory={p['inventory']}, Price=Rs.{p['price']}")
        
        return products
    
    def track_multiple_locations(self, queries, locations):
        """Track inventory across multiple dark store locations"""
        results = {}
        
        for location_name, (lat, lon) in locations.items():
            self.set_location(lat, lon)
            results[location_name] = {}
            
            for query in queries:
                products = self.search(query, limit=10)
                results[location_name][query] = products
        
        return results


if __name__ == "__main__":
    # Default location
    lat = "28.6048439"
    lon = "77.2928391"
    
    if len(sys.argv) > 1:
        query = sys.argv[1]
    else:
        query = "milk"
    
    if len(sys.argv) > 3:
        lat = sys.argv[2]
        lon = sys.argv[3]
    
    tracker = BlinkitInventoryTracker(latitude=lat, longitude=lon)
    
    print("=" * 60)
    print("Blinkit Inventory Tracker")
    print(f"Location: Lat={lat}, Lon={lon}")
    print(f"Query: {query}")
    print("=" * 60)
    
    products = tracker.search(query, limit=10)
    
    if products:
        print(f"\nFound {len(products)} products:\n")
        for i, p in enumerate(products, 1):
            print(f"{i}. {p['name']}")
            print(f"   Variant: {p['variant']}")
            print(f"   Price: Rs.{p['price']} | MRP: Rs.{p['mrp']}")
            print(f"   INVENTORY: {p['inventory']}")  # Exact inventory!
            print(f"   Brand: {p['brand']}")
            print(f"   Merchant: {p['merchant_type']}")
            if p['rating']:
                print(f"   Rating: {p['rating']} ({p['rating_count']})")
            print()
    else:
        print("No products found")