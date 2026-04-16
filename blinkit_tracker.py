"""
Blinkit Inventory Tracker - Full featured with export, alerts, scheduling
Usage:
    python blinkit_tracker.py <product> [lat] [lon]
    python blinkit_tracker.py <product> --store-id <store_id>
    python blinkit_tracker.py <product> --locations <file.json>
    python blinkit_tracker.py --export csv|json
    python blinkit_tracker.py --schedule <interval_minutes>
"""
import os
import sys
import json
import csv
import time
import threading
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright
import nest_asyncio
nest_asyncio.apply()

class BlinkitInventoryTracker:
    def __init__(self, latitude=None, longitude=None, store_id=None):
        self.base_url = "https://blinkit.com"
        self.state_file = "data/blinkit_state.json"
        self.lat = latitude or "28.6048439"
        self.lon = longitude or "77.2928391"
        self.store_id = store_id
        self.data_dir = Path("inventory_data")
        self.alerts_file = self.data_dir / "alerts.json"
        self.history_dir = self.data_dir / "history"
        
        # Create directories
        self.data_dir.mkdir(exist_ok=True)
        self.history_dir.mkdir(exist_ok=True)
    
    def set_location(self, lat, lon):
        self.lat = lat
        self.lon = lon
        self.store_id = None
        print(f"Location set to: Lat={lat}, Lon={lon}")
    
    def set_store_id(self, store_id):
        self.store_id = store_id
        print(f"Store set to ID: {store_id}")
    
    def _load_state(self):
        return None  # Don't use cached state - always get fresh location
    
    def search(self, query, limit=20):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()
            
            api_data = []
            
            def handle_response(response):
                url = response.url
                if "layout/search" in url or "/v1/" in url:
                    try:
                        data = response.json()
                        if data.get("is_success"):
                            api_data.append(data)
                    except:
                        pass
            
            page.on("response", handle_response)
            
            if self.store_id:
                url = f"{self.base_url}/s/?q={query}&store_id={self.store_id}"
            else:
                url = f"{self.base_url}/s/?q={query}&lat={self.lat}&lon={self.lon}"
            
            page.goto(url, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(2000)
            
            context.storage_state(path=self.state_file)
            browser.close()
            
            products = []
            store_info = None
            
            for api_resp in api_data:
                if store_info is None:
                    store_info = api_resp.get("response", {}).get("location", {})
                
                for snippet in api_resp.get("response", {}).get("snippets", []):
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
                        "mrp": float(d.get("mrp", {}).get("text", "₹0").replace("₹", "").replace(",", "") or 0),
                        "inventory": d.get("inventory", 0),
                        "brand": d.get("brand_name", {}).get("text", ""),
                        "eta": d.get("eta_tag", {}).get("title", {}).get("text", "earliest"),
                        "merchant_id": d.get("merchant_id", ""),
                        "merchant_type": d.get("merchant_type", ""),
                        "timestamp": datetime.now().isoformat()
                    })
            
            return products, store_info
    
    def export_csv(self, products, filename=None):
        """Export products to CSV"""
        if not products:
            print("No products to export")
            return
        
        filename = filename or f"inventory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = self.data_dir / filename
        
        # Get all possible fields from products
        fieldnames = list(products[0].keys()) if products else []
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(products)
        
        print(f"Exported to CSV: {filepath}")
        return filepath
    
    def export_json(self, products, filename=None):
        """Export products to JSON"""
        if not products:
            print("No products to export")
            return
        
        filename = filename or f"inventory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.data_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(products, f, indent=2, ensure_ascii=False)
        
        print(f"Exported to JSON: {filepath}")
        return filepath
    
    def save_history(self, products, location_name="default"):
        """Save inventory snapshot to history"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = self.history_dir / f"{location_name}_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(products, f, indent=2)
        
        return filename
    
    def load_history(self, location_name=None, limit=10):
        """Load historical inventory data"""
        if location_name:
            files = sorted(self.history_dir.glob(f"{location_name}_*.json"), reverse=True)
        else:
            files = sorted(self.history_dir.glob("*.json"), reverse=True)
        
        files = files[:limit]
        history = []
        
        for f in files:
            with open(f, 'r') as fp:
                data = json.load(fp)
                history.append({
                    "filename": f.name,
                    "data": data
                })
        
        return history
    
    def check_alerts(self, products, threshold=5):
        """Check for low stock items and generate alerts"""
        alerts = []
        
        for p in products:
            if p['inventory'] < threshold:
                alerts.append({
                    "type": "LOW_STOCK",
                    "product_id": p['product_id'],
                    "name": p['name'],
                    "variant": p['variant'],
                    "inventory": p['inventory'],
                    "threshold": threshold,
                    "timestamp": datetime.now().isoformat()
                })
        
        # Save alerts
        if alerts:
            # Load existing alerts
            existing = []
            if self.alerts_file.exists():
                with open(self.alerts_file, 'r') as f:
                    existing = json.load(f)
            
            # Add new alerts
            existing.extend(alerts)
            
            # Keep only last 100 alerts
            existing = existing[-100:]
            
            with open(self.alerts_file, 'w') as f:
                json.dump(existing, f, indent=2)
        
        return alerts
    
    def get_active_alerts(self, since_hours=24):
        """Get active alerts from the last N hours"""
        if not self.alerts_file.exists():
            return []
        
        with open(self.alerts_file, 'r') as f:
            alerts = json.load(f)
        
        # Filter by time
        cutoff = datetime.now().timestamp() - (since_hours * 3600)
        recent_alerts = []
        
        for a in alerts:
            alert_time = datetime.fromisoformat(a['timestamp']).timestamp()
            if alert_time > cutoff:
                recent_alerts.append(a)
        
        return recent_alerts
    
    def clear_alerts(self):
        """Clear all alerts"""
        if self.alerts_file.exists():
            self.alerts_file.unlink()
        print("Alerts cleared")


class InventoryScheduler:
    """Background scheduler for inventory monitoring"""
    
    def __init__(self, tracker, interval_minutes=30):
        self.tracker = tracker
        self.interval_minutes = interval_minutes
        self.running = False
        self.thread = None
        self.monitored_products = []
        self.monitored_locations = {}
    
    def add_product(self, query):
        """Add product to monitor"""
        self.monitored_products.append(query)
    
    def add_location(self, name, lat, lon):
        """Add location to monitor"""
        self.monitored_locations[name] = {"lat": lat, "lon": lon}
    
    def start(self):
        """Start scheduled monitoring"""
        if self.running:
            print("Scheduler already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_schedule, daemon=True)
        self.thread.start()
        print(f"Scheduler started - checking every {self.interval_minutes} minutes")
    
    def stop(self):
        """Stop scheduled monitoring"""
        self.running = False
        if self.thread:
            print("Scheduler stopped")
    
    def _run_schedule(self):
        """Main scheduler loop"""
        while self.running:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Running scheduled inventory check...")
            
            for loc_name, location in self.monitored_locations.items():
                self.tracker.set_location(location["lat"], location["lon"])
                
                for product in self.monitored_products:
                    print(f"  Checking {product} at {loc_name}...")
                    products, _ = self.tracker.search(product, limit=20)
                    
                    # Save to history
                    self.tracker.save_history(products, f"{loc_name}_{product}")
                    
                    # Check alerts
                    alerts = self.tracker.check_alerts(products)
                    if alerts:
                        print(f"    ALERTS: {len(alerts)} low stock items!")
                        for a in alerts:
                            print(f"      - {a['name']} ({a['variant']}): {a['inventory']} left")
            
            # Sleep until next interval
            time.sleep(self.interval_minutes * 60)


def main():
    # Defaults
    lat, lon = "28.6048439", "77.2928391"
    query = "milk"
    store_id = None
    locations_file = None
    export_format = None
    schedule_interval = None
    
    # Parse arguments
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        
        if arg == "--store-id":
            if i + 1 < len(sys.argv):
                store_id = sys.argv[i + 1]
                i += 2
        elif arg == "--locations":
            if i + 1 < len(sys.argv):
                locations_file = sys.argv[i + 1]
                i += 2
        elif arg == "--export":
            if i + 1 < len(sys.argv):
                export_format = sys.argv[i + 1]
                i += 2
        elif arg == "--schedule":
            if i + 1 < len(sys.argv):
                schedule_interval = int(sys.argv[i + 1])
                i += 2
        elif arg == "--alerts":
            # Show active alerts
            tracker = BlinkitInventoryTracker()
            alerts = tracker.get_active_alerts()
            if alerts:
                print(f"Active alerts (last 24h): {len(alerts)}")
                for a in alerts:
                    print(f"  [{a['inventory']}] {a['name']} ({a['variant']})")
            else:
                print("No active alerts")
            return
        elif arg == "--clear-alerts":
            tracker = BlinkitInventoryTracker()
            tracker.clear_alerts()
            return
        elif arg == "--history":
            tracker = BlinkitInventoryTracker()
            history = tracker.load_history(limit=5)
            for h in history:
                print(f"  {h['filename']}: {len(h['data'])} products")
            return
        else:
            query = arg
            if i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith("-"):
                lat = sys.argv[i + 1]
                lon = sys.argv[i + 2]
                i += 3
            else:
                i += 1
    
    tracker = BlinkitInventoryTracker(lat, lon, store_id)
    
    # Handle export
    if export_format:
        products, _ = tracker.search(query, limit=20)
        if export_format == "csv":
            tracker.export_csv(products)
        elif export_format == "json":
            tracker.export_json(products)
        return
    
    # Handle scheduled monitoring
    if schedule_interval:
        scheduler = InventoryScheduler(tracker, schedule_interval)
        
        # Add default monitoring
        scheduler.add_product("milk")
        scheduler.add_product("bread")
        scheduler.add_location("Dwarka", lat, lon)
        
        # If locations file provided, add those
        if locations_file and os.path.exists(locations_file):
            with open(locations_file, 'r') as f:
                locations = json.load(f)
                for name, loc in locations.items():
                    if "lat" in loc:
                        scheduler.add_location(name, loc["lat"], loc["lon"])
        
        print(f"Starting scheduled monitoring (every {schedule_interval} min)...")
        print("Press Ctrl+C to stop")
        
        try:
            scheduler.start()
            # Keep main thread alive
            while scheduler.running:
                time.sleep(1)
        except KeyboardInterrupt:
            scheduler.stop()
        return
    
    # Normal search mode
    print("=" * 60)
    print("Blinkit Inventory Tracker")
    if store_id:
        print(f"Store ID: {store_id}")
    else:
        print(f"Location: Lat={lat}, Lon={lon}")
    print(f"Query: {query}")
    print("=" * 60)
    
    products, store_info = tracker.search(query, limit=15)
    
    if store_info:
        print(f"\nStore: {store_info.get('name', 'Unknown')}")
    
    # Check and display alerts
    alerts = tracker.check_alerts(products, threshold=5)
    
    if products:
        print(f"\nFound {len(products)} products")
        if alerts:
            print(f"WARNING: {len(alerts)} LOW STOCK ITEMS:")
        
        for i, p in enumerate(products, 1):
            stock_status = "LOW" if p['inventory'] < 5 else "OK"
            alert_marker = " (!)" if p['inventory'] < 5 else ""
            
            print(f"{i}. {p['name']}")
            print(f"   {p['variant']} | Rs.{p['price']} | Stock: {p['inventory']} ({stock_status}){alert_marker}")
            print(f"   Brand: {p['brand']} | ETA: {p['eta']}")
            print()
        
        # Auto-export
        tracker.export_csv(products)
        tracker.export_json(products)
        tracker.save_history(products, query)
    else:
        print("No products found")


if __name__ == "__main__":
    main()