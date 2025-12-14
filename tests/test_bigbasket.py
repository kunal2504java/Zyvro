"""
Test script for BigBasket agent
"""

import sys
sys.path.append('..')

from agents.bigbasket import BigBasketAgent


def test_search():
    """Test product search"""
    print("\n" + "="*60)
    print("TEST 1: Search Products")
    print("="*60)
    
    agent = BigBasketAgent()
    products = agent.search_products("milk", limit=5)
    
    print(f"\n✅ Found {len(products)} products")
    return products


def test_add_to_cart(products):
    """Test adding products to cart"""
    print("\n" + "="*60)
    print("TEST 2: Add to Cart")
    print("="*60)
    
    if not products:
        print("❌ No products to add")
        return
    
    agent = BigBasketAgent()
    
    # Add first 2 products
    urls = [p['url'] for p in products[:2]]
    result = agent.add_to_cart(urls)
    
    print(f"\n✅ Added {result['successful']}/{result['total_products']} products")


def test_view_cart():
    """Test viewing cart"""
    print("\n" + "="*60)
    print("TEST 3: View Cart")
    print("="*60)
    
    agent = BigBasketAgent()
    cart = agent.view_cart()
    
    if cart['cart_empty']:
        print("🛒 Cart is empty")
    else:
        print(f"✅ Cart has {cart['total_items']} items")
        print(f"   Subtotal: ₹{cart['subtotal']}")


def test_checkout():
    """Test checkout process"""
    print("\n" + "="*60)
    print("TEST 4: Checkout (DRY RUN)")
    print("="*60)
    
    print("⚠️ Skipping actual checkout to avoid placing real order")
    print("   Uncomment in code to test full checkout flow")
    
    # Uncomment to test actual checkout:
    # agent = BigBasketAgent()
    # result = agent.place_order()
    # print(f"Order Status: {result['final_status']}")


if __name__ == "__main__":
    print("\n🧪 BigBasket Agent Test Suite")
    print("="*60)
    
    # Run tests
    products = test_search()
    test_add_to_cart(products)
    test_view_cart()
    test_checkout()
    
    print("\n" + "="*60)
    print("✅ All tests completed!")
    print("="*60)
