"""
Test script for ZeptoAgent

Run this to verify that the Zepto agent is working correctly.
"""

import asyncio
from zepto import ZeptoAgent


async def test_search():
    """Test product search functionality"""
    print("\n" + "="*60)
    print("Test 1: Search Products")
    print("="*60)
    
    zepto = ZeptoAgent()
    products = await zepto.search_products("milk", limit=3)
    
    assert len(products) > 0, "No products found"
    assert products[0]['name'], "Product name is empty"
    assert products[0]['price'] is not None, "Product price is missing"
    
    print(f"✅ Found {len(products)} products")
    return products


async def test_add_to_cart(products):
    """Test adding products to cart"""
    print("\n" + "="*60)
    print("Test 2: Add to Cart")
    print("="*60)
    
    zepto = ZeptoAgent()
    
    # Add first product to cart
    product_url = products[0]['url']
    result = await zepto.add_to_cart(product_url)
    
    assert result['success'], "Failed to add product to cart"
    assert result['successful'] == 1, "Product was not added successfully"
    
    print(f"✅ Added {result['successful']} product to cart")
    return result


async def test_view_cart():
    """Test viewing cart contents"""
    print("\n" + "="*60)
    print("Test 3: View Cart")
    print("="*60)
    
    zepto = ZeptoAgent()
    cart = await zepto.view_cart()
    
    assert 'cart_items' in cart, "Cart items not found"
    assert cart['total_items'] > 0, "Cart is empty"
    
    print(f"✅ Cart has {cart['total_items']} items")
    print(f"   Subtotal: ₹{cart['subtotal']}")
    return cart


async def test_check_coupons():
    """Test checking available coupons"""
    print("\n" + "="*60)
    print("Test 4: Check Coupons")
    print("="*60)
    
    zepto = ZeptoAgent()
    coupons = await zepto.check_coupons()
    
    print(f"✅ Found {len(coupons)} coupons")
    if coupons:
        print(f"   First coupon: {coupons[0]['coupon_code']}")
    return coupons


async def main():
    """Run all tests"""
    print("\n🧪 Running Zepto Agent Tests")
    print("="*60)
    
    try:
        # Test 1: Search
        products = await test_search()
        
        # Test 2: Add to cart
        await test_add_to_cart(products)
        
        # Test 3: View cart
        await test_view_cart()
        
        # Test 4: Check coupons
        await test_check_coupons()
        
        print("\n" + "="*60)
        print("✅ All Tests Passed!")
        print("="*60)
        
    except Exception as e:
        print("\n" + "="*60)
        print(f"❌ Test Failed: {e}")
        print("="*60)
        raise


if __name__ == "__main__":
    asyncio.run(main())
