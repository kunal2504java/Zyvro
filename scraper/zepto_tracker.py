"""
Zepto Inventory Tracker - Multiple location approaches
"""
import os
import sys
import json
import re
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright

LOCATION_COORDS = {
    "mumbai": {"lat": "19.0760", "lng": "72.8777"},
    "bangalore": {"lat": "12.9716", "lng": "77.5946"},
    "delhi": {"lat": "28.6139", "lng": "77.2090"},
    "gurugram": {"lat": "28.4595", "lng": "77.0266"},
    "pune": {"lat": "18.5204", "lng": "73.8567"},
    "hyderabad": {"lat": "17.3850", "lng": "78.4867"},
    "chennai": {"lat": "13.0827", "lng": "80.2707"},
    "kolkata": {"lat": "22.5726", "lng": "88.3639"},
    "noida": {"lat": "28.5355", "lng": "77.3910"},
    "ghaziabad": {"lat": "28.6692", "lng": "77.4538"},
}

# Also try different Bangalore coordinates for different stores
BANGALORE_STORES = [
    {"lat": "12.97", "lng": "77.59", "name": "BTM"},
    {"lat": "13.03", "lng": "77.55", "name": "Whitefield"},
    {"lat": "12.92", "lng": "77.68", "name": "Kengeri"},
]

def set_geolocation(page, lat, lng):
    """Try to set geolocation via CDP"""
    try:
        page.context._impl._channel.update_geolocation({
            "latitude": float(lat),
            "longitude": float(lng),
            "accuracy": 1
        })
        print(f"Geolocation set via CDP: {lat}, {lng}")
        return True
    except Exception as e:
        print(f"CDP geolocation failed: {e}")
        return False

def inject_location_override(page, lat, lng):
    """Inject JavaScript to override geolocation"""
    script = f"""
    // Override geolocation API
    if (navigator.geolocation) {{
        var origGetCurrentPosition = navigator.geolocation.getCurrentPosition;
        navigator.geolocation.getCurrentPosition = function(success, error, options) {{
            success({{
                coords: {{
                    latitude: {lat},
                    longitude: {lng},
                    accuracy: 1,
                    altitude: 0,
                    heading: 0,
                    speed: 0
                }},
                timestamp: Date.now()
            }});
        }};
        
        var origWatchPosition = navigator.geolocation.watchPosition;
        navigator.geolocation.watchPosition = function(success, error, options) {{
            success({{
                coords: {{
                    latitude: {lat},
                    longitude: {lng},
                    accuracy: 1,
                    altitude: 0,
                    heading: 0,
                    speed: 0
                }},
                timestamp: Date.now()
            }});
            return 1;
        }};
    }}
    
    // Set localStorage
    localStorage.setItem('latitude', '{lat}');
    localStorage.setItem('longitude', '{lng}');
    localStorage.setItem('userLocation', JSON.stringify({{
        latitude: {lat},
        longitude: {lng}
    }}));
    localStorage.setItem('prev_store_id', '');
    
    // Set cookies
    document.cookie = 'latitude={lat}; path=/; max-age=31536000';
    document.cookie = 'longitude={lng}; path=/; max-age=31536000';
    
    console.log('Location override injected: {lat}, {lng}');
    """
    try:
        page.evaluate(script)
        print(f"Injected location override: {lat}, {lng}")
        return True
    except Exception as e:
        print(f"Injection failed: {e}")
        return False

class ZeptoInventoryTracker:
    def __init__(self, location="mumbai"):
        self.base_url = "https://zepto.com"
        self.location = (location or "mumbai").lower()
        self.data_dir = Path("inventory_data/zepto")
        self.data_dir.mkdir(exist_ok=True)
    
    def search(self, query, limit=20):
        coords = LOCATION_COORDS.get(self.location, LOCATION_COORDS["mumbai"])
        lat, lng = coords["lat"], coords["lng"]
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            
            # Try to set geolocation via context
            page = browser.new_page()
            
            # Method 1: Set geolocation in context
            try:
                page.context.set_geolocation({
                    "latitude": float(lat),
                    "longitude": float(lng),
                    "accuracy": 1
                })
                print(f"Set context geolocation: {lat}, {lng}")
            except:
                pass
            
            # Navigate
            page.goto(self.base_url, wait_until="load", timeout=30000)
            page.wait_for_timeout(2000)
            
            # Method 2: Inject location override
            inject_location_override(page, lat, lng)
            page.wait_for_timeout(1000)
            
            # Reload to trigger location detection
            page.reload()
            page.wait_for_timeout(3000)
            
            # Search
            page.keyboard.type(query)
            page.keyboard.press("Enter")
            page.wait_for_timeout(8000)
            
            # Scroll
            for _ in range(3):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(500)
            
            html = page.content().replace('\\"', '"')
            
            # Extract store ID
            store_match = re.search(r'"storeId":\s*"([^"]+)"', html)
            store_id = store_match.group(1) if store_match else None
            
            # Extract products
            pattern = r'baseProductId":"([^"]+)".*?availableQuantity\D*(\d+)'
            matches = re.findall(pattern, html)
            
            products = []
            seen = set()
            for match in matches:
                if match[0] in seen:
                    continue
                seen.add(match[0])
                products.append({
                    "baseProductId": match[0],
                    "variant_id": match[0],
                    "inventory": int(match[1]),
                    "in_stock": int(match[1]) > 0,
                    "store_id": store_id,
                    "location_requested": self.location,
                    "lat": lat,
                    "lng": lng,
                    "timestamp": datetime.now().isoformat()
                })
            
            browser.close()
            return products[:limit], store_id
    
    def export_json(self, products, filename=None):
        if not products:
            return
        filename = filename or f"zepto_{self.location}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.data_dir / filename
        with open(filepath, "w") as f:
            json.dump(products, f, indent=2)
        print(f"Exported: {filepath}")


def main():
    query = "pepsi"
    location = "bangalore"
    
    for arg in sys.argv[1:]:
        if arg in ["-l", "--location"] and sys.argv.index(arg) + 1 < len(sys.argv):
            location = sys.argv[sys.argv.index(arg) + 1]
        elif not arg.startswith("-"):
            query = arg
    
    tracker = ZeptoInventoryTracker(location)
    products, store = tracker.search(query, 15)
    
    if products:
        print(f"\nFound {len(products)} products")
        print(f"Requested location: {location}")
        print(f"Active store: {store}")
        tracker.export_json(products)


if __name__ == "__main__":
    main()