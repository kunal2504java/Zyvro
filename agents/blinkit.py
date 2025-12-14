# ========================================
# CELL 1: Install and Setup (Run FIRST after kernel restart)
# ========================================
# Uncomment and run if you don't have these packages:
# !pip install playwright nest-asyncio
# !playwright install chromium

import nest_asyncio
nest_asyncio.apply()

print("✅ nest_asyncio applied - ready to use!")


# ========================================
# CELL 2: Import and Define BlinkitAgent
# ========================================
from playwright.sync_api import sync_playwright
import time

class BlinkitAgent:
    def __init__(self):
        self.state = "data/blinkit_state.json"
        self.base_url = "https://blinkit.com"
        
    def search_products(self, query: str, limit: int = 10):
        """
        Search for products on Blinkit and return detailed product information.
        """
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(storage_state=self.state)
            page = context.new_page()

            print(f"🔍 Searching for: {query}")

            # Navigate to search page
            search_url = f"{self.base_url}/s/?q={query.replace(' ', '%20')}"
            page.goto(search_url, wait_until="domcontentloaded")

            try:
                # Wait for product results - NEW SELECTOR
                page.wait_for_selector('.tw-text-300.tw-font-semibold.tw-line-clamp-2', timeout=5000)
            except:
                print("⚠️ No products found")
                context.close()
                browser.close()
                return []

            # Extract product data - UPDATED FOR NEW BLINKIT STRUCTURE
            results = page.evaluate(f"""
                () => {{
                    const limit = {limit};
                    const products = [];
                    
                    // Find all product cards
                    const productCards = document.querySelectorAll('.tw-relative.tw-flex.tw-h-full.tw-flex-col.tw-pb-3');
                    
                    for (let i = 0; i < Math.min(limit, productCards.length); i++) {{
                        const card = productCards[i];
                        
                        // Product name - using new Tailwind classes
                        const nameElem = card.querySelector('.tw-text-300.tw-font-semibold.tw-line-clamp-2');
                        const name = nameElem ? nameElem.innerText.trim() : '';
                        
                        // Weight/size - using new Tailwind classes
                        const weightElem = card.querySelector('.tw-text-200.tw-font-medium.tw-line-clamp-1');
                        const weight = weightElem ? weightElem.innerText.trim() : '';
                        
                        // Current price - using new Tailwind classes
                        const priceElems = card.querySelectorAll('.tw-text-200.tw-font-semibold');
                        let price = null;
                        if (priceElems.length > 0) {{
                            const priceText = priceElems[0].innerText.trim();
                            const match = priceText.match(/₹([\\d,]+)/);
                            if (match) {{
                                price = parseFloat(match[1].replace(/,/g, ''));
                            }}
                        }}
                        
                        // Original price (if discounted) - line-through style
                        const originalPriceElem = card.querySelector('.tw-line-through');
                        let originalPrice = null;
                        if (originalPriceElem) {{
                            const originalText = originalPriceElem.innerText.trim();
                            const match = originalText.match(/₹([\\d,]+)/);
                            if (match) {{
                                originalPrice = parseFloat(match[1].replace(/,/g, ''));
                            }}
                        }}
                        
                        // Discount percentage - from the badge
                        const discountElem = card.querySelector('.tw-text-050');
                        let discount = null;
                        if (discountElem) {{
                            const discountText = discountElem.innerText.trim();
                            const match = discountText.match(/([\\d]+)%/);
                            if (match) {{
                                discount = parseInt(match[1]);
                            }}
                        }}
                        
                        // Product URL - construct from product ID
                        let url = '';
                        const productId = card.getAttribute('id');
                        if (productId) {{
                            // Blinkit product URLs follow this pattern: /p/product-name/prid/ID
                            // We'll construct a basic URL with the ID
                            const productName = name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
                            url = `https://blinkit.com/p/${{productName}}/prid/${{productId}}`;
                        }}
                        
                        // Product image
                        const imgElem = card.querySelector('img');
                        const image = imgElem ? imgElem.src : '';
                        
                        // Check if ADD button exists
                        const addButton = card.querySelector('.tw-rounded-md.tw-font-okra');
                        const inStock = addButton !== null && addButton.innerText.includes('ADD');
                        
                        products.push({{
                            index: i,
                            name: name,
                            weight: weight,
                            price: price,
                            original_price: originalPrice,
                            discount_percentage: discount,
                            savings: originalPrice && price ? originalPrice - price : null,
                            delivery_time: '10 minutes',
                            in_stock: inStock,
                            url: url,
                            image: image
                        }});
                    }}

                    return products;
                }}
            """)

            print(f"🛒 Found {len(results)} products")

            if results:
                for i, p in enumerate(results[:3], 1):
                    price_info = f"₹{p['price']}" if p['price'] else "Price N/A"
                    if p['savings']:
                        price_info += f" (save ₹{p['savings']})"
                    print(f"  {i}. {p['name'][:45]} - {price_info}")

            context.close()
            browser.close()

            return results
    
    def add_to_cart(self, product_urls, product_names=None):
        """Add one or multiple products to the shopping cart by clicking on product cards.
        
        Args:
            product_urls: List of product URLs or single URL
            product_names: Optional list of product names (used for searching)
        """
        if isinstance(product_urls, str):
            product_urls = [product_urls]

        # Extract product IDs and names from URLs
        product_ids = []
        search_terms = []
        
        for idx, url in enumerate(product_urls):
            # Extract ID from URL like: https://blinkit.com/p/product-name/prid/505525
            if '/prid/' in url:
                product_id = url.split('/prid/')[-1]
                product_ids.append(product_id)
                
                # Extract product name from URL for searching
                if '/p/' in url:
                    name_part = url.split('/p/')[1].split('/prid/')[0]
                    # Convert URL slug to search term (e.g., "amul-gold-milk" -> "amul gold milk")
                    search_term = name_part.replace('-', ' ')
                    search_terms.append(search_term)
                else:
                    search_terms.append(None)
            else:
                product_ids.append(None)
                search_terms.append(None)
        
        # Override with provided product names if available
        if product_names:
            if isinstance(product_names, str):
                search_terms = [product_names]
            else:
                search_terms = product_names

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(storage_state=self.state)
            page = context.new_page()

            results = []
            print(f"🛒 Adding {len(product_ids)} product(s) to cart...")

            for idx, (product_id, search_term) in enumerate(zip(product_ids, search_terms), 1):
                if not product_id or not search_term:
                    print(f"  ⚠️ Product {idx}: Invalid URL or search term")
                    results.append({
                        "success": False,
                        "url": product_urls[idx-1],
                        "index": idx - 1,
                        "error": "Invalid product URL"
                    })
                    continue

                try:
                    print(f"  [{idx}/{len(product_ids)}] Searching for: {search_term}")
                    
                    # Navigate to search page with product name to find it
                    search_query = search_term.replace(' ', '%20')
                    page.goto(f"{self.base_url}/s/?q={search_query}", wait_until="domcontentloaded")
                    time.sleep(3)  # Increased wait time for page to fully load
                    
                    # Wait for product cards to appear
                    try:
                        page.wait_for_selector('.tw-text-300.tw-font-semibold.tw-line-clamp-2', timeout=5000)
                    except:
                        print(f"  ⚠️ Products not loaded for: {search_term}")
                    
                    # Click the first ADD button on the search results page with improved detection
                    add_clicked = page.evaluate("""
                        () => {
                            // Strategy 1: Look for buttons with specific Tailwind classes
                            let buttons = document.querySelectorAll('.tw-rounded-md.tw-font-okra');
                            for (const button of buttons) {
                                const text = (button.innerText || button.textContent || '').trim().toUpperCase();
                                if (text === 'ADD') {
                                    // Check if button is visible
                                    const rect = button.getBoundingClientRect();
                                    if (rect.width > 0 && rect.height > 0) {
                                        button.click();
                                        return {success: true, method: 'tailwind-class'};
                                    }
                                }
                            }
                            
                            // Strategy 2: Look for any button with role="button" and ADD text
                            buttons = document.querySelectorAll('[role="button"]');
                            for (const button of buttons) {
                                const text = (button.innerText || button.textContent || '').trim().toUpperCase();
                                if (text === 'ADD') {
                                    const rect = button.getBoundingClientRect();
                                    if (rect.width > 0 && rect.height > 0) {
                                        button.click();
                                        return {success: true, method: 'role-button'};
                                    }
                                }
                            }
                            
                            // Strategy 3: Look for buttons with green background (ADD buttons are usually green)
                            buttons = document.querySelectorAll('button, div[role="button"]');
                            for (const button of buttons) {
                                const text = (button.innerText || button.textContent || '').trim().toUpperCase();
                                const style = window.getComputedStyle(button);
                                const bgColor = style.backgroundColor;
                                
                                if (text === 'ADD' && (bgColor.includes('green') || button.className.includes('green'))) {
                                    button.click();
                                    return {success: true, method: 'green-button'};
                                }
                            }
                            
                            // Strategy 4: Look in product cards specifically
                            const productCards = document.querySelectorAll('.tw-relative.tw-flex.tw-h-full.tw-flex-col');
                            if (productCards.length > 0) {
                                const firstCard = productCards[0];
                                const addButton = firstCard.querySelector('button, [role="button"]');
                                if (addButton) {
                                    const text = (addButton.innerText || addButton.textContent || '').trim().toUpperCase();
                                    if (text === 'ADD') {
                                        addButton.click();
                                        return {success: true, method: 'product-card'};
                                    }
                                }
                            }
                            
                            return {success: false, method: 'none'};
                        }
                    """)
                    
                    if add_clicked['success']:
                        time.sleep(1.5)  # Wait for cart update
                        print(f"  ✅ Product {idx} added to cart! (method: {add_clicked['method']})")
                        results.append({
                            "success": True,
                            "url": product_urls[idx-1],
                            "index": idx - 1
                        })
                    else:
                        print(f"  ⚠️ Could not find ADD button for product {idx}")
                        print(f"     Tried all detection methods, none worked")
                        results.append({
                            "success": False,
                            "url": product_urls[idx-1],
                            "index": idx - 1,
                            "error": "ADD button not found - product may be out of stock"
                        })

                except Exception as e:
                    print(f"  ❌ Error adding product {idx}: {e}")
                    results.append({
                        "success": False,
                        "url": product_urls[idx-1],
                        "index": idx - 1,
                        "error": str(e)
                    })

            context.storage_state(path=self.state)
            context.close()
            browser.close()

            successful = sum(1 for r in results if r["success"])
            print(f"🎉 Successfully added {successful}/{len(product_ids)} products to cart!")

            return {
                "success": successful > 0,
                "total_products": len(product_ids),
                "successful": successful,
                "failed": len(product_ids) - successful,
                "results": results
            }

    def view_cart(self):
        """View all items currently in the shopping cart."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(storage_state=self.state)
            page = context.new_page()

            print("🛒 Opening cart...")
            
            # Go to homepage
            page.goto(self.base_url, wait_until="domcontentloaded")
            time.sleep(3)
            
            # Click the cart button to open cart modal/overlay
            print("Clicking cart button...")
            try:
                # Try to find and click the cart button
                cart_button = page.locator('[class*="CartButton"]').first
                cart_button.click()
                time.sleep(3)
                print("✅ Cart opened")
            except Exception as e:
                print("📭 Cart is empty")
                context.close()
                browser.close()
                return {
                    "cart_items": [],
                    "total_items": 0,
                    "subtotal": 0,
                    "cart_empty": True
                }

            cart_data = page.evaluate("""
                () => {
                    // Debug: log what we're finding
                    console.log('Looking for cart items...');
                    
                    // Try multiple selectors to find cart items
                    let items = document.querySelectorAll('[class*="CartProduct__Container"]');
                    console.log('CartProduct__Container found:', items.length);
                    
                    if (items.length === 0) {
                        items = document.querySelectorAll('[class*="DefaultProductCard__Container"]');
                        console.log('DefaultProductCard__Container found:', items.length);
                    }
                    
                    if (items.length === 0) {
                        // Try finding any product-like containers
                        items = document.querySelectorAll('[class*="Product"]');
                        console.log('Generic Product containers found:', items.length);
                    }
                    
                    const cartItems = [];

                    for (let i = 0; i < items.length; i++) {
                        const item = items[i];

                        // Product name - use flexible selector
                        let nameElem = item.querySelector('[class*="ProductTitle"]');
                        const name = nameElem ? nameElem.innerText.trim() : '';

                        // Product weight/variant - use flexible selector
                        let weightElem = item.querySelector('[class*="ProductVariant"]');
                        const weight = weightElem ? weightElem.innerText.trim() : '';

                        // Quantity - find the quantity display
                        let qtyContainer = item.querySelector('[class*="AddToCart"][class*="Button"]');
                        let quantity = 0;
                        if (qtyContainer) {
                            const qtyText = qtyContainer.innerText.trim();
                            // Extract first number from text
                            const match = qtyText.match(/\\d+/);
                            if (match) {
                                quantity = parseInt(match[0]);
                            }
                        }

                        // Price - use flexible selector
                        let priceElem = item.querySelector('[class*="Price"]');
                        let price = null;
                        if (priceElem) {
                            const priceText = priceElem.innerText.trim();
                            const match = priceText.match(/₹([\\d,]+)/);
                            if (match) {
                                price = parseFloat(match[1].replace(/,/g, ''));
                            }
                        }

                        // Image
                        const imgElem = item.querySelector('img');
                        const imageUrl = imgElem ? imgElem.src : '';

                        cartItems.push({
                            index: i,
                            name: name,
                            weight: weight,
                            quantity: quantity,
                            price: price,
                            total_price: price ? price * quantity : null,
                            image_url: imageUrl
                        });
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

            print(f"🛍️ Found {cart_data['total_items']} items in cart")
            print(f"💰 Subtotal: ₹{cart_data['subtotal']}")

            for item in cart_data['cart_items']:
                print(f"  • {item['name']} - {item['weight']} x{item['quantity']} = ₹{item['total_price']}")

            context.close()
            browser.close()

            return cart_data
    
    def update_cart_quantity(self, item_index: int, action: str = "increase"):
        """Increase or decrease the quantity of a specific cart item."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(storage_state=self.state)
            page = context.new_page()

            print(f"🛒 Opening cart to {action} quantity...")
            page.goto(f"{self.base_url}/cart", wait_until="domcontentloaded")

            try:
                page.wait_for_selector('[data-test-id="cart-product"]', timeout=5000)

                cart_items = page.locator('[data-test-id="cart-product"]')
                item = cart_items.nth(item_index)

                qty_elem = item.locator('[data-test-id="cart-product-qty"]')
                old_qty = int(qty_elem.inner_text())

                if action == "increase":
                    button = item.locator('[data-test-id="increase-qty"]')
                    print(f"➕ Increasing quantity from {old_qty}...")
                else:
                    button = item.locator('[data-test-id="decrease-qty"]')
                    print(f"➖ Decreasing quantity from {old_qty}...")

                button.click()
                time.sleep(0.8)

                try:
                    new_qty = int(qty_elem.inner_text())
                    print(f"✅ Quantity updated: {old_qty} → {new_qty}")
                    result = {
                        "success": True,
                        "item_index": item_index,
                        "old_quantity": old_qty,
                        "new_quantity": new_qty,
                        "removed": False
                    }
                except:
                    print(f"🗑️ Item removed from cart (quantity reached 0)")
                    result = {
                        "success": True,
                        "item_index": item_index,
                        "old_quantity": old_qty,
                        "new_quantity": 0,
                        "removed": True
                    }

            except Exception as e:
                print(f"❌ Error updating quantity: {e}")
                result = {
                    "success": False,
                    "error": str(e)
                }

            context.storage_state(path=self.state)
            context.close()
            browser.close()

            return result

    def clear_cart(self):
        """Remove all items from the shopping cart at once."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(storage_state=self.state)
            page = context.new_page()

            print("🛒 Opening cart to clear all items...")
            page.goto(f"{self.base_url}/cart", wait_until="domcontentloaded")

            try:
                try:
                    page.wait_for_selector('[data-test-id="cart-product"]', timeout=3000)
                except:
                    print("📭 Cart is already empty!")
                    result = {
                        "success": True,
                        "items_removed": 0,
                        "message": "Cart was already empty"
                    }
                    context.close()
                    browser.close()
                    return result

                cart_items = page.locator('[data-test-id="cart-product"]')
                item_count = cart_items.count()

                print(f"🗑️ Found {item_count} items to remove...")

                removed_count = page.evaluate("""
                    () => {
                        const items = document.querySelectorAll('[data-test-id="cart-product"]');
                        let count = 0;

                        for (const item of items) {
                            const qtyElem = item.querySelector('[data-test-id="cart-product-qty"]');
                            const quantity = qtyElem ? parseInt(qtyElem.innerText) : 0;
                            const decreaseBtn = item.querySelector('[data-test-id="decrease-qty"]');

                            if (decreaseBtn && quantity > 0) {
                                for (let i = 0; i < quantity; i++) {
                                    decreaseBtn.click();
                                }
                                count++;
                            }
                        }

                        return count;
                    }
                """)

                time.sleep(2)

                print(f"✅ Successfully cleared {removed_count} items from cart!")
                result = {
                    "success": True,
                    "items_removed": removed_count,
                    "message": "Cart cleared successfully"
                }

            except Exception as e:
                print(f"❌ Error clearing cart: {e}")
                result = {
                    "success": False,
                    "error": str(e),
                    "items_removed": 0
                }

            context.storage_state(path=self.state)
            context.close()
            browser.close()

            return result

    def get_product_details(self, product_url: str):
        """Get comprehensive information about a specific product."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(storage_state=self.state)
            page = context.new_page()

            if not product_url.startswith('http'):
                product_url = f"{self.base_url}{product_url}"

            print(f"📦 Fetching product details...")
            page.goto(product_url, wait_until="domcontentloaded")

            try:
                page.wait_for_selector('.Product__UpdatedTitle-sc-11dk8zk-9', timeout=5000)

                product_data = page.evaluate("""
                    () => {
                        const nameElem = document.querySelector('.Product__UpdatedTitle-sc-11dk8zk-9');
                        const name = nameElem ? nameElem.innerText.trim() : '';

                        const weightElem = document.querySelector('.Product__UpdatedWeightAndPiecesWrapper-sc-11dk8zk-10');
                        const weight = weightElem ? weightElem.innerText.trim() : '';

                        const priceElem = document.querySelector('.ProductPricing__Price-sc-16pk4i7-0');
                        let price = null;
                        if (priceElem) {
                            const priceText = priceElem.innerText.trim();
                            const match = priceText.match(/₹([\\d,]+)/);
                            if (match) {
                                price = parseFloat(match[1].replace(/,/g, ''));
                            }
                        }

                        const originalPriceElem = document.querySelector('.ProductPricing__OriginalPrice-sc-16pk4i7-1');
                        let originalPrice = null;
                        if (originalPriceElem) {
                            const originalText = originalPriceElem.innerText.trim();
                            const match = originalText.match(/₹([\\d,]+)/);
                            if (match) {
                                originalPrice = parseFloat(match[1].replace(/,/g, ''));
                            }
                        }

                        const discountElem = document.querySelector('.ProductPricing__DiscountText-sc-16pk4i7-3');
                        let discount = null;
                        if (discountElem) {
                            const discountText = discountElem.innerText.trim();
                            const match = discountText.match(/([\\d]+)%/);
                            if (match) {
                                discount = parseInt(match[1]);
                            }
                        }

                        const descriptionElem = document.querySelector('[data-test-id="product-description"]');
                        const description = descriptionElem ? descriptionElem.innerText.trim() : '';

                        const imgElem = document.querySelector('.Product__UpdatedImageContainer-sc-11dk8zk-1 img');
                        const image = imgElem ? imgElem.src : '';

                        const brandElem = document.querySelector('[data-test-id="product-brand"]');
                        const brand = brandElem ? brandElem.innerText.trim() : '';

                        const deliveryTime = '10 minutes';

                        const addButton = document.querySelector('[data-test-id="add-button-pdp"]');
                        const inStock = addButton !== null;

                        return {
                            name: name,
                            brand: brand,
                            weight: weight,
                            price: price,
                            original_price: originalPrice,
                            discount_percentage: discount,
                            savings: originalPrice && price ? originalPrice - price : null,
                            description: description,
                            delivery_time: deliveryTime,
                            in_stock: inStock,
                            image: image,
                            url: window.location.href
                        };
                    }
                """)

                print(f"✅ Product: {product_data['name']}")
                print(f"   Weight: {product_data['weight']}")
                print(f"   Price: ₹{product_data['price']}")
                if product_data['savings']:
                    print(f"   Savings: ₹{product_data['savings']} ({product_data['discount_percentage']}% off)")
                print(f"   Delivery: {product_data['delivery_time']}")
                print(f"   In Stock: {product_data['in_stock']}")

                result = {
                    "success": True,
                    "product": product_data
                }

            except Exception as e:
                print(f"❌ Error fetching product details: {e}")
                result = {
                    "success": False,
                    "error": str(e)
                }

            context.close()
            browser.close()

            return result

    def place_order(self):
        """Complete checkout and place the order."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(storage_state=self.state)
            page = context.new_page()

            print("🛒 Opening cart...")
            # Go to homepage first
            page.goto(self.base_url, wait_until="domcontentloaded")
            time.sleep(3)
            
            # Click cart button to open cart modal (same as view_cart)
            print("🟢 Opening cart modal...")
            try:
                cart_button = page.locator('[class*="CartButton"]').first
                cart_button.click()
                time.sleep(3)
                print("✅ Cart modal opened")
            except Exception as e:
                print(f"❌ Could not open cart: {e}")

            result = {
                "checkout_started": False,
                "payment_page_reached": False,
                "payment_method": None,
                "order_id": None,
                "final_status": "unknown",
                "error": None
            }

            try:
                # First check if cart has items
                print("� Cohecking if cart has items...")
                cart_check = page.evaluate("""
                    () => {
                        const bodyText = document.body.innerText.toLowerCase();
                        const isEmpty = bodyText.includes('cart is empty') || 
                                       bodyText.includes('no items') ||
                                       bodyText.includes('your cart is empty');
                        
                        // Count visible product elements
                        const products = document.querySelectorAll('[class*="product"], [class*="item"]');
                        
                        return {
                            isEmpty: isEmpty,
                            productCount: products.length
                        };
                    }
                """)
                
                if cart_check['isEmpty'] or cart_check['productCount'] == 0:
                    result["error"] = "Cart is empty. Please add items first."
                    result["final_status"] = "cart_empty"
                    print("❌ Cart is empty")
                    context.storage_state(path=self.state)
                    context.close()
                    browser.close()
                    return result
                
                print(f"✅ Cart has {cart_check['productCount']} items")
                
                # Look for Proceed button in cart modal
                print("🟢 Looking for Proceed button in cart modal...")
                time.sleep(2)  # Wait for cart modal to fully load
                
                checkout_clicked = page.evaluate("""
                    () => {
                        // Strategy 1: Look for AmountContainer (the actual clickable element)
                        const amountContainer = document.querySelector('[class*="CheckoutStrip__AmountContainer"]');
                        if (amountContainer) {
                            const rect = amountContainer.getBoundingClientRect();
                            if (rect.width > 0 && rect.height > 0) {
                                amountContainer.click();
                                return {success: true, text: 'AmountContainer', method: 'amount-container'};
                            }
                        }
                        
                        // Strategy 2: Look for StripContainer
                        const stripContainer = document.querySelector('[class*="CheckoutStrip__StripContainer"]');
                        if (stripContainer) {
                            const rect = stripContainer.getBoundingClientRect();
                            if (rect.width > 0 && rect.height > 0) {
                                stripContainer.click();
                                return {success: true, text: 'StripContainer', method: 'strip-container'};
                            }
                        }
                        
                        // Strategy 3: Look for any clickable element with "Proceed" text
                        const allElements = document.querySelectorAll('div[onclick], div[role="button"], button');
                        for (const elem of allElements) {
                            const text = String(elem.innerText || '').trim();
                            if (text.includes('Proceed') || text.includes('PROCEED')) {
                                const rect = elem.getBoundingClientRect();
                                if (rect.width > 0 && rect.height > 0) {
                                    elem.click();
                                    return {success: true, text: text, method: 'clickable-proceed'};
                                }
                            }
                        }
                        
                        return {success: false, text: null, method: 'none'};
                    }
                """)
                
                if not checkout_clicked['success']:
                    result["error"] = "Checkout button not found. Cart might be empty or page structure changed."
                    result["final_status"] = "checkout_button_not_found"
                    print("❌ Could not find checkout button")
                    print("   Tried all detection methods")
                    context.storage_state(path=self.state)
                    context.close()
                    browser.close()
                    return result
                
                print(f"✅ Clicked checkout button: '{checkout_clicked['text']}' (method: {checkout_clicked['method']})")
                result["checkout_started"] = True
                time.sleep(7)  # Increased from 5s to 7s for page transition

                # Check if we reached payment/checkout page
                current_url = page.url
                print(f"📍 Current URL: {current_url}")
                
                if '/checkout' in current_url or '/payment' in current_url:
                    result["payment_page_reached"] = True
                    result["final_status"] = "reached_payment_page"
                    result["payment_method"] = "Manual interaction required"
                    print("✅ Reached payment page successfully!")
                    print("⚠️ Manual payment interaction required to complete order")
                    print("   Please complete payment in the browser window")
                else:
                    result["final_status"] = "checkout_in_progress"
                    print("⚠️ Checkout flow in progress - may need additional steps")

            except Exception as e:
                result["error"] = str(e)
                result["final_status"] = "failed"
                print(f"❌ Error during checkout: {e}")

            context.storage_state(path=self.state)
            context.close()
            browser.close()

            return result

print("✅ BlinkitAgent class loaded successfully!")


# ========================================
# CELL 3: Usage Examples
# ========================================
# blinkit = BlinkitAgent()
# products = blinkit.search_products("milk", limit=5)
# blinkit.add_to_cart(products[0]['url'])
# cart = blinkit.view_cart()
# blinkit.update_cart_quantity(item_index=0, action="increase")
# blinkit.clear_cart()
# details = blinkit.get_product_details(products[0]['url'])
# blinkit.place_order()
