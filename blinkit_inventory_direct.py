"""
Blinkit Inventory Tracker - Direct API with location only (no login required)
"""
import requests
import json

class BlinkitInventoryTracker:
    def __init__(self, latitude="28.6048439", longitude="77.2928391"):
        self.latitude = latitude
        self.longitude = longitude
        self.api_url = "https://blinkit.com/v1/layout/search"
        self.base_url = "https://blinkit.com"
        
        self.session = requests.Session()
        self._setup_session()
    
    def _setup_session(self):
        # Set location cookies
        self.session.cookies.set("gr_1_lat", self.latitude, domain="blinkit.com")
        self.session.cookies.set("gr_1_lon", self.longitude, domain="blinkit.com")
        self.session.cookies.set("gr_1_locality", "1", domain="blinkit.com")
        
        # Required headers from your example
        self.session.headers.update({
            "authority": "blinkit.com",
            "method": "POST",
            "path": "/v1/layout/search",
            "scheme": "https",
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8,hi;q=0.7",
            "access_token": "null",
            "app_client": "consumer_web",
            "app_version": "1010101010",
            "auth_key": "c761ec3633c22afad934fb17a66385c1c06c5472b4898b866b7306186d0bb477",
            "device_id": "0179875a70e4433f",
            "lat": self.latitude,
            "lon": self.longitude,
            "origin": "https://blinkit.com",
            "referer": "https://blinkit.com/s/",
            "rn_bundle_version": "1009003012",
            "sec-ch-ua": '"Google Chrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
            "sec-ch-ua-mobile": "?1",
            "sec-ch-ua-platform": '"Android"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "session_uuid": "cdbb2d42-4451-45b3-9f43-74abb349f4ae",
            "web_app_version": "1008010016",
            "Content-Type": "application/json"
        })
    
    def set_location(self, latitude, longitude):
        """Update location for tracking different dark stores"""
        self.latitude = latitude
        self.longitude = longitude
        
        # Update cookies
        self.session.cookies.set("gr_1_lat", latitude, domain="blinkit.com")
        self.session.cookies.set("gr_1_lon", longitude, domain="blinkit.com")
        
        # Update headers
        self.session.headers.update({
            "lat": latitude,
            "lon": longitude
        })
    
    def search(self, query, limit=20):
        """Search products and get EXACT inventory"""
        params = {
            "q": query,
            "search_type": "type_to_search"
        }
        
        body = {
            "applied_filters": None,
            "monet_assets": [{"name": "ads_vertical_banner", "processed": 0, "total": 0}],
            "postback_meta": {
                "processedGroupIds": [446538],
                "pageMeta": {"scrollMeta": [{"entitiesCount": 167}]},
                "excludedGroupIds": [642039, 642040, 733086, 2520540, 2143654, 1937936, 1937938, 2625128, 2625124, 2557981, 2557979]
            },
            "previous_search_query": "",
            "processed_rails": {
                "similar_brand_rail": {"total_count": 1, "processed_count": 1, "processed_product_ids": [], "processed_rail_entities": None},
                "usecase_grid_rail": {"total_count": 0, "processed_count": 1, "processed_product_ids": [], "processed_rail_entities": [{"id": "9028"}]}
            },
            "similar_entities": [],
            "sort": "",
            "vertical_cards_processed": 11
        }
        
        response = self.session.post(self.api_url, params=params, json=body)
        
        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            return []
        
        data = response.json()
        return self._parse_response(data, limit)
    
    def _parse_response(self, data, limit):
        products = []
        
        if not data.get("is_success"):
            print("API returned unsuccessful response")
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
    
    def track_multiple_locations(self, queries, locations):
        """Track inventory across multiple dark store locations"""
        results = {}
        
        for location_name, (lat, lon) in locations.items():
            print(f"\n{'='*60}")
            print(f"Location: {location_name} (Lat: {lat}, Lon: {lon})")
            print(f"{'='*60}")
            
            self.set_location(lat, lon)
            
            location_results = {}
            for query in queries:
                print(f"\nSearching: {query}")
                products = self.search(query, limit=10)
                location_results[query] = products
                
                for p in products:
                    print(f"  - {p['name']} ({p['variant']}): Inventory={p['inventory']}, Price=Rs.{p['price']}")
            
            results[location_name] = location_results
        
        return results


if __name__ == "__main__":
    import sys
    
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
    print("Blinkit Inventory Tracker (Direct API)")
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
        print("No products found. Check if location coordinates are valid.")