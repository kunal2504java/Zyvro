"""
Standalone Instamart Test Script

Test Instamart agent functionality independently:
- Setup session (login)
- Search products
- Add to cart
- View cart
- Checkout

Run this to test Instamart without affecting Zepto/Blinkit.
"""

import asyncio
from instamart import InstamartAgent


def print_header(title):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def print_products(products):
    """Print product list"""
    if not products:
        print("❌ No products found")
        return
    
    print(f"\n✅ Found {len(products)} products:\n")
    for i, p in enumerate(products, 1):
        print(f"{i}. {p['name']}")
        print(f"   Weight: {p.get('weight', 'N/A')}")
        print(f"   Price: ₹{p['price']}")
        print(f"   URL: {p['url'][:50]}...")
        print()


def print_cart(cart):
    """Print cart contents"""
    if cart['cart_empty']:
        print("🛒 Cart is empty")
        return
    
    print(f"\n🛒 Cart Contents ({cart['total_items']} items):\n")
    for item in cart['cart_items']:
        print(f"• {item['name']}")
        print(f"  Quantity: {item['quantity']}")
        print(f"  Price: ₹{item['total_price']}")
        print()
    
    print(f"💰 Subtotal: ₹{cart['subtotal']}")


async def test_instamart_full_flow():
    """Test complete Instamart flow"""
    
    print_header("🕵️  Instamart Standalone Test")
    print("\nThis will test Instamart functionality step by step.")
    print("Make sure you've run the advanced setup first!")
    print("\nRequired: python blinkit_mcp/setup_instamart_advanced.py")
    
    input("\nPress Enter to continue...")
    
    # Initialize agent
    print_header("1️⃣  Initializing Instamart Agent")
    agent = InstamartAgent()
    
    try:
        # Start browser
        print("\n🚀 Starting stealth browser...")
        agent.start_browser(headless=False)
        print("✅ Browser started successfully")
        
        # Test 1: Search products
        print_header("2️⃣  Testing Product Search")
        search_query = input("\nEnter product to search (or press Enter for 'milk'): ").strip()
        if not search_query:
            search_query = "milk"
        
        print(f"\n🔍 Searching for: {search_query}")
        products = agent.search_products(search_query, limit=5)
        print_products(products)
        
        if not products:
            print("\n❌ Search failed. Check if you're logged in.")
            print("   Run: python blinkit_mcp/setup_instamart_advanced.py")
            return
        
        # Test 2: Add to cart
        print_header("3️⃣  Testing Add to Cart")
        add_choice = input("\nAdd first product to cart? (y/n): ").lower().strip()
        
        if add_choice == 'y':
            print("\n🛒 Adding first product to cart...")
            result = agent.add_to_cart([products[0]['url']])
            
            if result['success']:
                print(f"✅ Added {result['successful']}/{result['total_products']} products")
            else:
                print("❌ Failed to add to cart")
        
        # Test 3: View cart
        print_header("4️⃣  Testing View Cart")
        view_choice = input("\nView cart contents? (y/n): ").lower().strip()
        
        if view_choice == 'y':
            print("\n👀 Fetching cart...")
            cart = agent.view_cart()
            print_cart(cart)
        
        # Test 4: Checkout (optional)
        print_header("5️⃣  Testing Checkout")
        print("\n⚠️  WARNING: This will place a REAL order!")
        checkout_choice = input("Proceed with checkout? (yes/no): ").lower().strip()
        
        if checkout_choice == 'yes':
            print("\n📦 Placing order...")
            order_result = agent.place_order()
            
            if order_result['final_status'] == 'completed':
                print("\n🎉 Order placed successfully!")
                print(f"   Order ID: {order_result.get('order_id', 'N/A')}")
                print(f"   ETA: {order_result.get('eta', 'N/A')}")
                print(f"   Payment: {order_result.get('payment_method', 'N/A')}")
            else:
                print(f"\n❌ Checkout failed: {order_result.get('error', 'Unknown error')}")
        else:
            print("\n⏭️  Skipping checkout")
        
        # Save session
        print_header("6️⃣  Saving Session")
        agent.save_session()
        print("✅ Session saved for future use")
        
        # Summary
        print_header("✅ Test Complete!")
        print("\n📊 Test Results:")
        print(f"   ✓ Browser: Working")
        print(f"   ✓ Search: {'Working' if products else 'Failed'}")
        print(f"   ✓ Add to Cart: {'Tested' if add_choice == 'y' else 'Skipped'}")
        print(f"   ✓ View Cart: {'Tested' if view_choice == 'y' else 'Skipped'}")
        print(f"   ✓ Checkout: {'Tested' if checkout_choice == 'yes' else 'Skipped'}")
        
        print("\n🎯 Next Steps:")
        print("   1. If all tests passed, Instamart is ready!")
        print("   2. Run: python blinkit_mcp/whatsapp_bot.py")
        print("   3. Test via WhatsApp: 'Search for milk on Instamart'")
        
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        print("\n🔧 Troubleshooting:")
        print("   1. Run setup: python blinkit_mcp/setup_instamart_advanced.py")
        print("   2. Make sure you're logged in to Swiggy")
        print("   3. Check your internet connection")
        print("   4. Try with a different network (mobile hotspot)")
        
    finally:
        print("\n🔒 Closing browser...")
        agent.close_browser()
        print("✅ Browser closed")


def test_session_only():
    """Quick test to check if session exists and is valid"""
    print_header("🔍 Quick Session Check")
    
    import os
    session_file = "sessions/instamart_session/state.json"
    
    if os.path.exists(session_file):
        print(f"\n✅ Session file found: {session_file}")
        print("   Session appears to be set up")
        
        # Try to load and validate
        try:
            with open(session_file, 'r') as f:
                import json
                data = json.load(f)
                cookies = data.get('cookies', [])
                print(f"   Cookies: {len(cookies)} found")
                
                if cookies:
                    print("\n✅ Session looks valid!")
                    print("\n🎯 Ready to test full flow")
                else:
                    print("\n⚠️  Session exists but has no cookies")
                    print("   You may need to run setup again")
        except Exception as e:
            print(f"\n❌ Error reading session: {e}")
    else:
        print(f"\n❌ No session file found")
        print(f"   Expected location: {session_file}")
        print("\n🔧 Run setup first:")
        print("   python blinkit_mcp/setup_instamart_advanced.py")


def main():
    """Main test menu"""
    print("\n" + "="*70)
    print("  🕵️  Instamart Standalone Test Suite")
    print("="*70)
    print("\nChoose test mode:")
    print("  1. Quick session check (fast)")
    print("  2. Full functionality test (recommended)")
    print("  3. Setup new session")
    print("  4. Exit")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == '1':
        test_session_only()
    elif choice == '2':
        asyncio.run(test_instamart_full_flow())
    elif choice == '3':
        print("\n🔧 Running setup...")
        print("   Execute: python blinkit_mcp/setup_instamart_advanced.py")
        import subprocess
        subprocess.run(["python", "blinkit_mcp/setup_instamart_advanced.py"])
    elif choice == '4':
        print("\n👋 Goodbye!")
    else:
        print("\n❌ Invalid choice")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
