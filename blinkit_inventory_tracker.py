"""
Blinkit Inventory Tracker - Intercepts API from page navigation
Uses Playwright to navigate to search page and capture inventory data
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
    url: str = ""

class BlinkitInventoryTracker:
    def __init__(self, latitude: str = None, longitude: str = None, state_file: str = None):
        self.latitude = latitude or "28.6048439"
        self.longitude = longitude or "77.2928391"
        self.state_file = state_file or "data/blinkit_state.json"
        self.base_url = "https://blinkit.com"
        self._inventory_data = {}  # Cache for inventory
    
    def set_location(self, latitude: str, longitude: str):
        """Update tracking location"""
        self.latitude = latitude
        self.longitude = longitude
    
    def _get_storage_state(self):
        if os.path.exists(self.state_file):
            return self.state_file
        return None
    
    async def search(self, query: str, limit: int = 20) -> List[ProductInventory]:
        """Search and get inventory - captures API response during navigation"""
        storage_state = self._get_storage_state()
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            
            context = await browser.new_context(
                storage_state=storage_state,
                viewport={"width": 1920, "height": 1080}
            )
            
            page = await context.new_page()
            
            # Set location cookies
            await context.add_cookies([
                {"name": "gr_1_lat", "value": self.latitude, "domain": "blinkit.com", "path": "/"},
                {"name": "gr_1_lon", "value": self.longitude, "domain": "blinkit.com", "path": "/"},
                {"name": "gr_1_locality", "value": "1", "domain": "blinkit.com", "path": "/"}
            ])
            
            # Navigate to search page - this triggers the API
            search_url = f"{self.base_url}/s/?q={query.replace(' ', '%20')}"
            print(f"Navigating to: {search_url}")
            
            # Wait for network to settle after API calls
            await page.goto(search_url, wait_until="networkidle", timeout=30000)
            
            # Wait for products to load
            await page.wait_for_selector('[class*="product"]', timeout=10000)
            
            # Wait a bit more for API data to populate
            await page.wait_for_timeout(2000)
            
            # Extract products with inventory - using API data pattern
            products = await page.evaluate(f"""
                async () => {{
                    const limit = {limit};
                    const products = [];
                    
                    // Method 1: Look for product cards with data attributes
                    const cards = document.querySelectorAll('[data-product-id], [class*="product-card"]');
                    
                    for (const card of cards) {{
                        if (products.length >= limit) break;
                        
                        // Try to get product ID
                        let productId = card.getAttribute('data-product-id');
                        if (!productId) {{
                            const link = card.querySelector('a[href*="/prid/"]');
                            if (link) {{
                                const match = link.href.match(/\\/prid\\/(\\d+)/);
                                if (match) productId = match[1];
                            }}
                        }}
                        
                        // Get name
                        let name = '';
                        const nameElem = card.querySelector('[class*="name"], [class*="title"], h2, h3');
                        if (nameElem) name = nameElem.innerText.trim();
                        
                        // Get variant
                        let variant = '';
                        const variantElem = card.querySelector('[class*="variant"], [class*="weight"]');
                        if (variantElem) variant = variantElem.innerText.trim();
                        
                        // Get price
                        let price = 0;
                        const priceElem = card.querySelector('[class*="price"], [class*="Price"]');
                        if (priceElem) {{
                            const match = priceElem.innerText.match(/₹([\\d,]+)/);
                            if (match) price = parseFloat(match[1].replace(/,/g, ''));
                        }}
                        
                        // Check if in stock
                        const addBtn = card.querySelector('[class*="add"], button');
                        const inStock = addBtn && addBtn.innerText.toLowerCase().includes('add');
                        
                        // Inventory - check for stock indicators
                        let inventory = 0;
                        const cardText = card.innerText;
                        
                        // Look for "Only X left" or "X in stock" patterns
                        const onlyLeft = cardText.match(/only\\s*(\\d+)\\s*left/i);
                        const inStockMatch = cardText.match(/(\\d+)\\s*in\\s*stock/i);
                        const leftMatch = cardText.match(/(\\d+)\\s*left/i);
                        
                        if (onlyLeft) inventory = parseInt(onlyLeft[1]);
                        else if (inStockMatch) inventory = parseInt(inStockMatch[1]);
                        else if (leftMatch) inventory = parseInt(leftMatch[1]);
                        else if (inStock) inventory = 99;  // Available but count unknown
                        
                        // Get URL
                        let url = '';
                        const link = card.querySelector('a[href*="/p/"]');
                        if (link) url = link.href;
                        
                        // Get image
                        let imageUrl = '';
                        const img = card.querySelector('img');
                        if (img) imageUrl = img.src;
                        
                        if (productId && name) {{
                            products.push({{
                                product_id: productId,
                                name: name,
                                variant: variant,
                                price: price,
                                inventory: inventory,
                                url: url,
                                image_url: imageUrl
                            }});
                        }}
                    }}
                    
                    return products;
                }}
            """)
            
            # Try to get more detailed inventory from API response
            # Intercept the API response if possible
            inventory_map = await self._fetch_inventory_from_api(page, query)
            
            await context.storage_state(path=self.state_file)
            await browser.close()
            
            # Merge inventory data
            result = []
            for p in products:
                product_id = str(p.get('product_id', ''))
                inventory = inventory_map.get(product_id, p.get('inventory', 0))
                
                result.append(ProductInventory(
                    product_id=product_id,
                    name=p.get('name', ''),
                    variant=p.get('variant', ''),
                    price=p.get('price', 0),
                    mrp=p.get('price', 0),
                    inventory=inventory,
                    merchant_id='',
                    merchant_type='express',
                    eta='earliest',
                    brand='',
                    image_url=p.get('image_url', ''),
                    url=p.get('url', '')
                ))
            
            return result
    
    async def _fetch_inventory_from_api(self, page, query: str) -> Dict[str, int]:
        """Try to fetch inventory from API endpoint"""
        try:
            # Make API request using page context
            inventory_data = await page.evaluate(f"""
                async () => {{
                    try {{
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
                                excludedGroupIds: [642039, 642040, 733086, 2520540]
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
                        
                        const response = await fetch("https://blinkit.com/v1/layout/search?" + params, {{
                            method: "POST",
                            headers: {{"Content-Type": "application/json"}},
                            body: JSON.stringify(body),
                            credentials: "include"
                        }});
                        
                        const data = await response.json();
                        return data;
                    }} catch (e) {{
                        console.error("API error:", e);
                        return {{}};
                    }}
                }}
            """)
            
            if inventory_data.get("is_success"):
                inventory_map = {}
                snippets = inventory_data.get("response", {}).get("snippets", [])
                for snippet in snippets:
                    data = snippet.get("data", {})
                    product_id = str(data.get("identity", {}).get("id", ""))
                    inventory = data.get("inventory", 0)
                    if product_id:
                        inventory_map[product_id] = inventory
                return inventory_map
                
        except Exception as e:
            print(f"API fetch error: {e}")
        
        return {}
    
    async def get_product_inventory(self, product_id: str) -> Optional[ProductInventory]:
        """Get inventory for a specific product"""
        # Navigate to product page and get inventory
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(storage_state=self._get_storage_state())
            page = await context.new_page()
            
            # Navigate to product
            product_url = f"{self.base_url}/prid/{product_id}"
            await page.goto(product_url, wait_until="networkidle")
            
            # Extract inventory from page
            inventory_data = await page.evaluate("""
                () => {
                    // Look for inventory display
                    const bodyText = document.body.innerText;
                    
                    // Try to find inventory count
                    const inventoryMatch = bodyText.match(/(\d+)\s*(items?|pcs?|units?)\s*(available|in stock)/i);
                    const leftMatch = bodyText.match(/only\s*(\d+)\s*left/i);
                    
                    let inventory = 0;
                    if (inventoryMatch) inventory = parseInt(inventoryMatch[1]);
                    else if (leftMatch) inventory = parseInt(leftMatch[1]);
                    
                    return { inventory };
                }
            """)
            
            await browser.close()
            
            return ProductInventory(
                product_id=product_id,
                name="",
                variant="",
                price=0,
                mrp=0,
                inventory=inventory_data.get("inventory", 0),
                merchant_id="",
                merchant_type="",
                eta="",
                brand="",
                image_url=""
            )


async def main():
    import sys
    
    # Default location
    lat = "28.6048439"
    lon = "77.2928391"
    
    # Parse args
    query = "milk"
    if len(sys.argv) > 1:
        query = sys.argv[1]
    if len(sys.argv) > 3:
        lat = sys.argv[2]
        lon = sys.argv[3]
    
    tracker = BlinkitInventoryTracker(latitude=lat, longitude=lon)
    
    print("=" * 60)
    print("Blinkit Inventory Tracker")
    print(f"Location: Lat={lat}, Lon={lon}")
    print(f"Query: {query}")
    print("=" * 60)
    
    products = await tracker.search(query, limit=10)
    
    if products:
        print(f"\nFound {len(products)} products:\n")
        for i, p in enumerate(products, 1):
            print(f"{i}. {p.name}")
            print(f"   Variant: {p.variant}")
            print(f"   Price: Rs.{p.price}")
            print(f"   INVENTORY: {p.inventory}")
            print(f"   URL: {p.url[:60]}..." if p.url else "   URL: N/A")
            print()
    else:
        print("No products found")


if __name__ == "__main__":
    asyncio.run(main())