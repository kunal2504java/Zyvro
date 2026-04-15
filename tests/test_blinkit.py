"""
Test script for BlinkitAgent - Testing search_products() function
Run this file to test the search functionality
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.blinkit import BlinkitAgent

# Initialize the agent
print("=" * 60)
print("TESTING: search_products() function")
print("=" * 60)

blinkit = BlinkitAgent()

# Test 1: Search for milk
print("\nTest 1: Searching for 'milk' (limit=5)")
print("-" * 60)
try:
    products = blinkit.search_products("milk", limit=5)
    
    if products:
        print(f"\nSUCCESS: Found {len(products)} products")
        print("\nProduct Details:")
        for i, product in enumerate(products, 1):
            print(f"\n{i}. {product['name']}")
            print(f"   Weight: {product['weight']}")
            print(f"   Price: Rs.{product['price']}")
            if product['original_price']:
                print(f"   Original Price: Rs.{product['original_price']}")
                print(f"   Discount: {product['discount_percentage']}%")
                print(f"   Savings: Rs.{product['savings']}")
            print(f"   In Stock: {product['in_stock']}")
            print(f"   Quantity: {product.get('quantity', 0)}")
            print(f"   Inventory: {product.get('inventory', 'N/A')}")
            print(f"   URL: {product['url'][:80]}...")
    else:
        print("No products found")
        
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Search for chocolate
print("\n\nTest 2: Searching for 'chocolate' (limit=3)")
print("-" * 60)
try:
    products = blinkit.search_products("chocolate", limit=3)
    
    if products:
        print(f"\nSUCCESS: Found {len(products)} products")
        print("\nQuick Summary:")
        for i, product in enumerate(products, 1):
            price_str = f"Rs.{product['price']}"
            if product['savings']:
                price_str += f" (save Rs.{product['savings']})"
            print(f"   {i}. {product['name'][:50]} - {price_str}")
    else:
        print("No products found")
        
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Testing Complete!")
print("=" * 60)