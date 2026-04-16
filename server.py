"""
Flask Server - API for Inventory Tracker
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
import json
from pathlib import Path
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "inventory_data"
HISTORY_DIR = DATA_DIR / "history"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
HISTORY_DIR.mkdir(exist_ok=True)

# ================== INVENTORY API ==================

@app.route('/api/inventory')
def get_inventory():
    """Get current inventory data"""
    files = sorted(HISTORY_DIR.glob("*.json"), reverse=True)
    
    if not files:
        return jsonify({"error": "No inventory data", "products": []})
    
    with open(files[0], 'r') as f:
        products = json.load(f)
    
    return jsonify({
        "timestamp": files[0].name,
        "products": products,
        "count": len(products)
    })

@app.route('/api/inventory/search')
def search_inventory():
    """Search for products (triggers new scan)"""
    query = request.args.get('q', 'milk')
    limit = int(request.args.get('limit', 20))
    store_id = request.args.get('store_id')
    
    from blinkit_tracker import BlinkitInventoryTracker
    
    tracker = BlinkitInventoryTracker(store_id=store_id)
    products, _ = tracker.search(query, limit)
    tracker.save_history(products, query)
    tracker.export_csv(products)
    tracker.export_json(products)
    tracker.check_alerts(products)
    
    return jsonify({
        "query": query,
        "store_id": store_id,
        "products": products,
        "count": len(products)
    })

@app.route('/api/alerts')
def get_alerts():
    """Get active alerts"""
    alerts_file = DATA_DIR / "alerts.json"
    
    if not alerts_file.exists():
        return jsonify({"alerts": []})
    
    with open(alerts_file, 'r') as f:
        alerts = json.load(f)
    
    cutoff = datetime.now().timestamp() - (24 * 3600)
    recent = [a for a in alerts 
              if datetime.fromisoformat(a['timestamp']).timestamp() > cutoff]
    
    return jsonify({"alerts": recent, "count": len(recent)})

@app.route('/api/history')
def get_history():
    """Get inventory history"""
    files = sorted(HISTORY_DIR.glob("*.json"), reverse=True)[:10]
    
    history = []
    for f in files:
        with open(f, 'r') as fp:
            data = json.load(fp)
            ts = f.name.replace('.json', '').split('_')[-1] if '_' in f.name else f.stem
            history.append({
                "filename": f.name,
                "timestamp": ts,
                "count": len(data)
            })
    
    return jsonify({"history": history})

@app.route('/api/locations')
def get_locations():
    """Get tracked locations"""
    locations_file = BASE_DIR / "locations.json"
    
    if not locations_file.exists():
        return jsonify({"locations": {}})
    
    with open(locations_file, 'r') as f:
        locations = json.load(f)
    
    return jsonify({"locations": locations})

@app.route('/api/stores')
def get_stores():
    """Get all stores from CSV"""
    import csv
    stores_file = BASE_DIR / "Blinkit_Store_Locations_20260416_092756.csv"
    
    if not stores_file.exists():
        return jsonify({"stores": [], "cities": []})
    
    stores = []
    cities = set()
    
    with open(stores_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            store_id = row['Store ID']
            city = row['City']
            pincode = row['Pincode']
            stores.append({"store_id": store_id, "city": city, "pincode": pincode})
            cities.add(city)
    
    return jsonify({
        "stores": stores,
        "cities": sorted(list(cities)),
        "count": len(stores)
    })


if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    print(f"Zyvro API Server running on port {port}")
    app.run(debug=True, port=port, host='0.0.0.0')