"""
Standalone Checkout Test Script for Blinkit

This script tests the checkout functionality step by step with detailed logging.
Run this to debug and fix the checkout flow without using WhatsApp.

Usage:
    python test_checkout.py
"""

from playwright.sync_api import sync_playwright
import time

def test_checkout():
    """Test Blinkit checkout flow step by step"""
    
    print("="*70)
    print("🧪 BLINKIT CHECKOUT TEST")
    print("="*70)
    
    state_file = "blinkit_state.json"
    base_url = "https://blinkit.com"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=state_file)
        page = context.new_page()
        
        try:
            # Step 1: Go to homepage
            print("\n📍 Step 1: Opening Blinkit homepage...")
            page.goto(base_url, wait_until="domcontentloaded")
            time.sleep(3)
            print("✅ Homepage loaded")
            
            # Step 2: Click cart button using Playwright locator (same as blinkit.py)
            print("\n📍 Step 2: Clicking cart button...")
            try:
                cart_button = page.locator('[class*="CartButton"]').first
                cart_button.click()
                time.sleep(3)
                print("✅ Cart button clicked successfully")
                cart_result = {'success': True, 'method': 'playwright-locator'}
            except Exception as e:
                print(f"❌ Could not click cart button: {e}")
                cart_result = {'success': False, 'method': 'none'}
                
                # Try JavaScript fallback
                print("   Trying JavaScript fallback...")
                cart_result = page.evaluate("""
                    () => {
                        const allElements = document.querySelectorAll('*');
                        const cartCandidates = [];
                        
                        for (const elem of allElements) {
                            const className = String(elem.className || '');
                            
                            if (className.includes('Cart') || className.includes('cart')) {
                                const rect = elem.getBoundingClientRect();
                                cartCandidates.push({
                                    tag: elem.tagName,
                                    className: className.substring(0, 100),
                                    width: Math.round(rect.width),
                                    height: Math.round(rect.height),
                                    visible: rect.width > 0 && rect.height > 0
                                });
                                
                                if (rect.width > 0 && rect.height > 0 && rect.width < 200) {
                                    elem.click();
                                    return {
                                        success: true,
                                        method: 'cart-class',
                                        element: className.substring(0, 100),
                                        candidates: cartCandidates
                                    };
                                }
                            }
                        }
                        
                        return {
                            success: false,
                            method: 'none',
                            candidates: cartCandidates
                        };
                    }
                """)
            
            print(f"\n📊 Found {len(cart_result.get('candidates', []))} cart-related elements:")
            for i, candidate in enumerate(cart_result.get('candidates', [])[:5], 1):
                print(f"  {i}. {candidate['tag']} - {candidate['className'][:50]}")
                print(f"     Size: {candidate['width']}x{candidate['height']}, Visible: {candidate['visible']}")
            
            if not cart_result['success']:
                print("\n❌ Could not find cart button!")
                print("   Please check the browser window and manually click the cart icon")
                input("   Press Enter after clicking cart button...")
            else:
                if 'element' in cart_result:
                    print(f"\n✅ Clicked cart button: {cart_result.get('element', 'CartButton')}")
                else:
                    print(f"\n✅ Clicked cart button (method: {cart_result['method']})")
                time.sleep(3)
            
            # Step 2.5: Display cart contents
            print("\n📍 Step 2.5: Viewing cart contents...")
            cart_data = page.evaluate("""
                () => {
                    // Use a more specific selector to avoid duplicates
                    const items = document.querySelectorAll('[class*="CartProduct__Container"], [data-test-id="cart-product"]');
                    const cartItems = [];
                    const seenProducts = new Set();

                    for (let i = 0; i < items.length; i++) {
                        const item = items[i];
                        
                        const nameElem = item.querySelector('[class*="ProductTitle"], [class*="Name"]');
                        const name = nameElem ? nameElem.innerText.trim() : '';
                        
                        // Skip if we've already seen this product (avoid duplicates)
                        if (seenProducts.has(name)) {
                            continue;
                        }
                        
                        const weightElem = item.querySelector('[class*="ProductVariant"], [class*="Weight"]');
                        const weight = weightElem ? weightElem.innerText.trim() : '';
                        
                        const qtyElem = item.querySelector('[class*="quantity"]');
                        const quantity = qtyElem ? parseInt(qtyElem.innerText) || 1 : 1;
                        
                        const priceElem = item.querySelector('[class*="Price"]');
                        let price = null;
                        if (priceElem) {
                            const priceText = priceElem.innerText.trim();
                            const match = priceText.match(/₹([\\d,]+)/);
                            if (match) {
                                price = parseFloat(match[1].replace(/,/g, ''));
                            }
                        }
                        
                        if (name) {
                            seenProducts.add(name);
                            cartItems.push({
                                name: name,
                                weight: weight,
                                quantity: quantity,
                                price: price,
                                total_price: price ? price * quantity : null
                            });
                        }
                    }

                    const subtotal = cartItems.reduce((sum, item) => sum + (item.total_price || 0), 0);
                    const totalItems = cartItems.reduce((sum, item) => sum + item.quantity, 0);

                    return {
                        cart_items: cartItems,
                        total_items: totalItems,
                        subtotal: subtotal,
                        cart_empty: cartItems.length === 0
                    };
                }
            """)
            
            if cart_data['cart_empty']:
                print("📭 Cart is empty!")
                print("   Please add items to cart first")
                input("\n   Press Enter to continue anyway...")
            else:
                print(f"\n🛍️ Cart Summary:")
                print(f"   Total Items: {cart_data['total_items']}")
                print(f"   Subtotal: ₹{cart_data['subtotal']}")
                print(f"\n   Items in cart:")
                for item in cart_data['cart_items']:
                    print(f"   • {item['name']} - {item['weight']} x{item['quantity']} = ₹{item['total_price']}")
                print()
            
            # Step 3: Look for Proceed button in cart modal
            print("\n📍 Step 3: Looking for Proceed button in cart modal...")
            proceed_result = page.evaluate("""
                () => {
                    console.log('=== SEARCHING FOR PROCEED BUTTON ===');
                    
                    const proceedCandidates = [];
                    
                    // Strategy 1: Look for CheckoutStrip
                    const checkoutStrip = document.querySelector('[class*="CheckoutStrip"]');
                    if (checkoutStrip) {
                        const className = String(checkoutStrip.className || '');
                        const text = String(checkoutStrip.innerText || '');
                        console.log('Found CheckoutStrip:', className);
                        proceedCandidates.push({
                            method: 'checkout-strip',
                            className: className.substring(0, 100),
                            text: text.substring(0, 100)
                        });
                        checkoutStrip.click();
                        return {
                            success: true,
                            method: 'checkout-strip',
                            text: text.substring(0, 100),
                            candidates: proceedCandidates
                        };
                    }
                    
                    // Strategy 2: Look for "Proceed" text
                    const allElements = document.querySelectorAll('div, button, [role="button"]');
                    for (const elem of allElements) {
                        const text = String(elem.innerText || elem.textContent || '').trim();
                        
                        if (text === 'Proceed' || text === 'PROCEED' || text.includes('Proceed')) {
                            const rect = elem.getBoundingClientRect();
                            const className = String(elem.className || '');
                            proceedCandidates.push({
                                method: 'proceed-text',
                                tag: elem.tagName,
                                className: className.substring(0, 100),
                                text: text.substring(0, 50),
                                width: Math.round(rect.width),
                                height: Math.round(rect.height),
                                visible: rect.width > 0 && rect.height > 0
                            });
                            
                            if (rect.width > 0 && rect.height > 0) {
                                console.log('Clicking Proceed element:', className);
                                elem.click();
                                return {
                                    success: true,
                                    method: 'proceed-text',
                                    text: text.substring(0, 50),
                                    candidates: proceedCandidates
                                };
                            }
                        }
                    }
                    
                    // Strategy 3: Look for CTAText class
                    const ctaElements = document.querySelectorAll('[class*="CTAText"]');
                    for (const elem of ctaElements) {
                        const text = String(elem.innerText || '').trim();
                        const className = String(elem.className || '');
                        proceedCandidates.push({
                            method: 'cta-text',
                            className: className.substring(0, 100),
                            text: text.substring(0, 50)
                        });
                        
                        if (text === 'Proceed') {
                            console.log('Clicking CTAText element');
                            elem.click();
                            return {
                                success: true,
                                method: 'cta-text',
                                text: text,
                                candidates: proceedCandidates
                            };
                        }
                    }
                    
                    return {
                        success: false,
                        method: 'none',
                        candidates: proceedCandidates
                    };
                }
            """)
            
            print(f"\n📊 Found {len(proceed_result.get('candidates', []))} proceed-related elements:")
            for i, candidate in enumerate(proceed_result.get('candidates', [])[:10], 1):
                print(f"  {i}. Method: {candidate['method']}")
                print(f"     Text: {candidate.get('text', 'N/A')[:50]}")
                if 'className' in candidate:
                    print(f"     Class: {candidate['className'][:50]}")
            
            if not proceed_result['success']:
                print("\n❌ Could not find Proceed button!")
                print("   Cart modal might be empty or button has different structure")
                print("\n🔍 Debugging info:")
                print("   1. Check if cart modal is visible in browser")
                print("   2. Look for a button with 'Proceed' or 'Checkout' text")
                print("   3. Check browser console for any errors")
                input("\n   Press Enter to continue...")
            else:
                print(f"\n✅ Clicked Proceed button: '{proceed_result['text']}' (method: {proceed_result['method']})")
                time.sleep(7)
            
            # Step 4: Check current URL
            print("\n📍 Step 4: Checking if we reached checkout page...")
            current_url = page.url
            print(f"   Current URL: {current_url}")
            
            if '/checkout' in current_url or '/payment' in current_url:
                print("\n🎉 SUCCESS! Reached checkout/payment page!")
                print("   The checkout flow is working correctly")
            else:
                print("\n⚠️  Not on checkout page yet")
                print("   You may need to complete additional steps manually")
            
            # Keep browser open for inspection
            print("\n" + "="*70)
            print("✅ Test Complete!")
            print("="*70)
            print("\nBrowser will stay open for inspection.")
            print("Check the page and see what's happening.")
            input("\nPress Enter to close browser and exit...")
            
        except Exception as e:
            print(f"\n❌ Error during test: {e}")
            import traceback
            traceback.print_exc()
            input("\nPress Enter to close browser...")
        
        finally:
            context.storage_state(path=state_file)
            context.close()
            browser.close()


if __name__ == "__main__":
    print("\n🚀 Starting Blinkit Checkout Test")
    print("   Make sure you have items in your cart!")
    print("   Session file: blinkit_state.json")
    input("\nPress Enter to start test...")
    
    test_checkout()
    
    print("\n👋 Test finished!")
