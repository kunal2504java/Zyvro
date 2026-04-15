"""
Blinkit Inventory Tracker - API based with session storage
Uses Playwright to login and save session, then fetches inventory via API
"""
import json
import os
import asyncio
from typing import List, Dict, Optional
from dataclasses import dataclass
from playwright.async_api import async_playwright
import nest_asyncio
nest_asyncio.apply()

@dataclass
class ProductInventory:
    product_id: str
    name: str
    variant: str
    price: float
    mrp: float
    inventory: int
    merchant_id: str
    merchant_type: str
    eta: str
    brand: str
    image_url: str
    rating: Optional[float] = None
    rating_count: Optional[str] = None

class BlinkitInventoryTracker:
    def __init__(self, latitude: str = None, longitude: str = None, state_file: str = "data/blinkit_api_state.json"):
        self.latitude = latitude or "28.6048439"
        self.longitude = longitude or "77.2928391"
        self.state_file = state_file
        self.api_url = "https://blinkit.com/v1/layout/search"
        self.base_url = "https://blinkit.com"
    
    def set_location(self, latitude: str, longitude: str):
        """Update tracking location"""
        self.latitude = latitude
        self.longitude = longitude
        print(f"Location updated to: Lat={latitude}, Lon={longitude}")
    
    async def login_and_save_session(self):
        """Open browser for manual login and save session"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            
            print("Please login to Blinkit manually...")
            print("Navigate to: https://blinkit.com")
            
            await page.goto(self.base_url)
            
            # Wait for user to login
            print("After logging in, press Enter here...")
            input()
            
            # Save session state
            await context.storage_state(path=self.state_file)
            print(f"Session saved to: {self.state_file}")
            
            await browser.close()
    
    async def search(self, query: str, limit: int = 20) -> List[ProductInventory]:
        """Search products and get inventory via API"""
        if not os.path.exists(self.state_file):
            print(f"No session file found: {self.state_file}")
            print("Please run login_and_save_session() first to authenticate")
            return []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(storage_state=self.state_file)
            page = await context.new_page()
            
            # Navigate to establish session
            await page.goto(self.base_url)
            
            # Update location cookies
            await page.evaluate(f"""
                () => {{
                    document.cookie = "gr_1_lat={self.latitude}; path=/";
                    document.cookie = "gr_1_lon={self.longitude}; path=/";
                    document.cookie = "gr_1_locality=1; path=/";
                }}
            """)
            
            # Make API request
            api_response = await page.evaluate(f"""
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
                        headers: {{"Content-Type": "application/json"}},
                        body: JSON.stringify(body),
                        credentials: "include"
                    }});
                    
                    return await response.json();
                }}
            """)
            
            await browser.close()
            
            if not api_response.get("is_success"):
                print(f"API Error: {api_response}")
                return []
            
            return self._parse_response(api_response, limit)
    
    def _parse_response(self, data: dict, limit: int) -> List[ProductInventory]:
        products = []
        
        try:
            snippets = data.get("response", {}).get("snippets", [])
            
            for snippet in snippets:
                if len(products) >= limit:
                    break
                    
                snippet_data = snippet.get("data", {})
                identity = snippet_data.get("identity", {})
                product_id = identity.get("id", "")
                
                if not product_id or not product_id.isdigit():
                    continue
                
                name = snippet_data.get("name", {}).get("text", "")
                variant = snippet_data.get("variant", {}).get("text", "")
                
                normal_price_text = snippet_data.get("normal_price", {}).get("text", "₹0")
                price = float(normal_price_text.replace("₹", "").replace(",", ""))
                
                mrp_text = snippet_data.get("mrp", {}).get("text", "₹0")
                mrp = float(mrp_text.replace("₹", "").replace(",", "")) if mrp_text else price
                
                # This is the actual inventory from API!
                inventory = snippet_data.get("inventory", 0)
                merchant_id = str(snippet_data.get("merchant_id", ""))
                merchant_type = snippet_data.get("merchant_type", "express")
                eta = snippet_data.get("eta_tag", {}).get("title", {}).get("text", "earliest")
                
                brand = snippet_data.get("brand_name", {}).get("text", "")
                image_url = snippet_data.get("image", {}).get("url", "")
                
                rating_data = snippet_data.get("rating", {})
                rating = None
                rating_count = None
                if rating_data:
                    bar = rating_data.get("bar", {})
                    rating = bar.get("value")
                    title = bar.get("title", {})
                    if title:
                        rating_count = title.get("text", "")
                
                product = ProductInventory(
                    product_id=product_id,
                    name=name,
                    variant=variant,
                    price=price,
                    mrp=mrp,
                    inventory=inventory,
                    merchant_id=merchant_id,
                    merchant_type=merchant_type,
                    eta=eta,
                    brand=brand,
                    image_url=image_url,
                    rating=rating,
                    rating_count=rating_count
                )
                products.append(product)
                
        except Exception as e:
            print(f"Parse error: {e}")
        
        return products
    
    async def track_inventory(self, queries: List[str], location: tuple = None):
        """Track inventory for multiple products at a location"""
        if location:
            self.set_location(*location)
        
        print(f"\nTracking inventory at: Lat={self.latitude}, Lon={self.longitude}")
        print("=" * 60)
        
        results = {}
        for query in queries:
            print(f"\nSearching: {query}")
            products = await self.search(query, limit=10)
            results[query] = products
            
            for p in products:
                print(f"  - {p.name} ({p.variant}): Inventory={p.inventory}, Price=Rs.{p.price}")
        
        return results


async def main():
    import sys
    
    tracker = BlinkitInventoryTracker(
        latitude="28.6048439",
        longitude="77.2928391"
    )
    
    # Check command line args
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "login":
            # Step 1: Login and save session
            print("=" * 60)
            print("Blinkit Session Login")
            print("=" * 60)
            await tracker.login_and_save_session()
            
        elif command == "track":
            # Step 2: Track inventory
            query = sys.argv[2] if len(sys.argv) > 2 else "milk"
            
            print("=" * 60)
            print("Blinkit Inventory Tracker")
            print(f"Location: Lat={tracker.latitude}, Lon={tracker.longitude}")
            print("=" * 60)
            
            products = await tracker.search(query, limit=10)
            
            if products:
                print(f"\nFound {len(products)} products:\n")
                for i, p in enumerate(products, 1):
                    print(f"{i}. {p.name}")
                    print(f"   Variant: {p.variant}")
                    print(f"   Price: Rs.{p.price} | MRP: Rs.{p.mrp}")
                    print(f"   INVENTORY: {p.inventory}")  # Real inventory!
                    print(f"   Brand: {p.brand}")
                    print(f"   Merchant: {p.merchant_type}")
                    if p.rating:
                        print(f"   Rating: {p.rating} ({p.rating_count})")
                    print()
            else:
                print("No products found. Did you login first?")
                
        elif command == "track-multi":
            # Track multiple products
            queries = sys.argv[2:] if len(sys.argv) > 2 else ["milk", "bread", "eggs"]
            await tracker.track_inventory(queries)
            
        else:
            print("Usage:")
            print("  python blinkit_api_tracker.py login    # Login and save session")
            print("  python blinkit_api_tracker.py track <query>    # Track inventory")
            print("  python blinkit_api_tracker.py track-multi <queries...>  # Track multiple")
    else:
        print("Commands:")
        print("  login    - Login to Blinkit and save session")
        print("  track    - Track inventory (use: track <product>)")
        print("  track-multi - Track multiple products")


if __name__ == "__main__":
    asyncio.run(main())