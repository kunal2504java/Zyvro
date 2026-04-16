"""
Zepto Inventory Tracker
Uses Playwright to extract inventory from HTML page source
"""
import os
import sys
import json
import re
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright

class ZeptoInventoryTracker:
    def __init__(self, location="mumbai"):
        self.base_url = "https://zepto.com"
        self.location = location
        self.data_dir = Path("inventory_data/zepto")
        self.data_dir.mkdir(exist_ok=True)
    
    def search(self, query, limit=20):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            
            page.goto(self.base_url, wait_until="load", timeout=30000)
            page.wait_for_timeout(3000)
            
            # Search
            page.keyboard.type(query)
            page.keyboard.press("Enter")
            page.wait_for_timeout(8000)
            
            # Scroll to load more
            for _ in range(3):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(1000)
            
            # Get HTML and extract products
            html = page.content()
            html = html.replace('\\"', '"')
            
            # Extract products
            pattern = r'baseProductId":"([^"]+)".*?availableQuantity\D*(\d+)'
            matches = re.findall(pattern, html)
            
            products = []
            seen = set()
            
            for match in matches:
                product_id = match[0]
                qty = int(match[1])
                
                if product_id in seen:
                    continue
                seen.add(product_id)
                
                products.append({
                    "baseProductId": product_id,
                    "variant_id": product_id,
                    "inventory": qty,
                    "in_stock": qty > 0,
                    "timestamp": datetime.now().isoformat()
                })
            
            browser.close()
            
            return products[:limit], None
    
    def export_json(self, products, filename=None):
        if not products:
            print("No products to export")
            return
        
        filename = filename or f"zepto_inventory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.data_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(products, f, indent=2)
        
        print(f"Exported to JSON: {filepath}")
        return filepath


def main():
    query = "milk"
    location = "mumbai"
    
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--location" or arg == "-l":
            if i + 1 < len(sys.argv):
                location = sys.argv[i + 1]
                i += 2
        else:
            query = arg
            i += 1
    
    tracker = ZeptoInventoryTracker(location)
    
    print(f"Searching Zepto for '{query}' in {location}")
    
    products, _ = tracker.search(query, limit=15)
    
    if products:
        print(f"\nFound {len(products)} products")
        
        # Group by inventory level
        low = [p for p in products if p['inventory'] <= 5]
        med = [p for p in products if 5 < p['inventory'] <= 20]
        high = [p for p in products if p['inventory'] > 20]
        
        print(f"\nStock Summary:")
        print(f"  Low (1-5): {len(low)}")
        print(f"  Medium (6-20): {len(med)}")
        print(f"  High (20+): {len(high)}")
        
        print(f"\nSample products:")
        for i, p in enumerate(products[:10], 1):
            print(f"  {i}. ID: {p['variant_id'][:20]}... Stock: {p['inventory']}")
        
        tracker.export_json(products)
    else:
        print("No products found")


if __name__ == "__main__":
    main()