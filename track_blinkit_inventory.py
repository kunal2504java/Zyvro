"""
Blinkit Inventory Tracker - Uses existing agent
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.blinkit import BlinkitAgent

def main():
    query = sys.argv[1] if len(sys.argv) > 1 else "milk"
    lat = sys.argv[2] if len(sys.argv) > 2 else "28.6048439"
    lon = sys.argv[3] if len(sys.argv) > 3 else "77.2928391"
    
    print("=" * 60)
    print("Blinkit Inventory Tracker")
    print(f"Location: Lat={lat}, Lon={lon}")
    print(f"Query: {query}")
    print("=" * 60)
    
    agent = BlinkitAgent()
    agent.latitude = lat
    agent.longitude = lon
    
    products = agent.search_products(query, limit=10)
    
    if products:
        print(f"\nFound {len(products)} products:\n")
        for i, p in enumerate(products, 1):
            print(f"{i}. {p['name']}")
            print(f"   Variant: {p.get('weight', 'N/A')}")
            print(f"   Price: Rs.{p['price']}")
            print(f"   In Stock: {p.get('in_stock', False)}")
            print(f"   Inventory: {p.get('inventory', 'See API for exact')}")
            print()
    else:
        print("No products found")

if __name__ == "__main__":
    main()