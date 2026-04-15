"""
Flask Server - Serves Landing Page + Dashboard + Inventory API
"""
from flask import Flask, render_template, jsonify, request
import json
import os
from pathlib import Path
from datetime import datetime

app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')

# Paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "inventory_data"
HISTORY_DIR = DATA_DIR / "history"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
HISTORY_DIR.mkdir(exist_ok=True)

# ================== ROUTES ==================

@app.route('/')
def landing_page():
    """Landing page"""
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """Dashboard page - serves the Next.js dashboard"""
    # For now, redirect to where the Next.js app would be
    # In production, you'd proxy to the Next.js dev server
    return render_template('dashboard.html')

# ================== INVENTORY API ==================

@app.route('/api/inventory')
def get_inventory():
    """Get current inventory data"""
    # Get latest history file
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
    
    # Run the tracker
    from blinkit_tracker import BlinkitInventoryTracker
    
    tracker = BlinkitInventoryTracker()
    products, _ = tracker.search(query, limit)
    
    # Save to history
    tracker.save_history(products, query)
    
    return jsonify({
        "query": query,
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
    
    # Return last 24 hours
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
            history.append({
                "filename": f.name,
                "timestamp": f.name.replace('.json', '').split('_')[-1],
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

@app.route('/api/export/<format>')
def export_data(format):
    """Export inventory data"""
    files = sorted(HISTORY_DIR.glob("*.json"), reverse=True)
    
    if not files:
        return jsonify({"error": "No data"})
    
    with open(files[0], 'r') as f:
        products = json.load(f)
    
    if format == 'csv':
        import csv
        from io import StringIO
        
        output = StringIO()
        if products:
            writer = csv.DictWriter(output, fieldnames=products[0].keys())
            writer.writeheader()
            writer.writerows(products)
        
        return output.getvalue(), 200, {'Content-Type': 'text/csv'}
    
    return jsonify(products)

# ================== MAIN ==================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting Zyvro server on port {port}")
    print(f"  Landing page: http://localhost:{port}/")
    print(f"  Dashboard: http://localhost:{port}/dashboard")
    print(f"  API: http://localhost:{port}/api/inventory")
    
    app.run(debug=True, port=port, host='0.0.0.0')