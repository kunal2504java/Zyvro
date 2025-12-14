"""
BigBasket Agent - Automated ordering for BigBasket
Supports: search, add to cart, view cart, checkout
"""

from playwright.sync_api import sync_playwright
import time
import os
import json


class BigBasketAgent:
    def __init__(self):
        self.state = "data/bigbasket_state.json"
        self.base_url = "https://www.bigbasket.com"
        
    def _get_storage_state(self):
        """Get storage state path if file exists, otherwise None"""
        if os.path.exists(self.state):
            return self.state
        return None
    
    def search_products(self, query: str, limit: int = 10):
        """
        Search for products on BigBasket and return detailed product information.
        
        Args:
            query: Search term (e.g., "milk", "vegetables", "rice")
            limit: Maximum number of products to return (default: 10)
            
        Returns:
            List of products with name, price, weight, discount, URL, etc.
        """
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            
            storage_state = self._get_storage_state()
            if storage_state:
                context = browser.new_context(storage_state=storage_state)
            else:
                print("⚠️ No session found. Browser will open for manual login.")
                print("   Please log in to BigBasket, then the session will be saved.")
                context = browser.new_context()
            
            page = context.new_page()

            print(f"🔍 Searching for: {query}")

            # Navigate to search page
            search_url = f"{self.base_url}/ps/?q={query.replace(' ', '%20')}"
            page.goto(search_url, wait_until="domcontentloaded")

            try:
                # Wait for product cards
                page.wait_for_selector('[qa="product"]', timeout=5000)
            except:
                print("⚠️ No products found")
                context.close()
                browser.close()
                return []

            # Extract product data
            results = page.evaluate(f"""
                () => {{
                    const limit = {limit};
                    const products = [];
                    
                    // Find all product cards
                    const productCards = document.querySelectorAll('[qa="product"]');
                    
                    for (let i = 0; i < Math.min(limit, productCards.length); i++) {{
                        const card = productCards[i];
                        
                        // Product name
                        const nameElem = card.querySelector('h3');
                        const name = nameElem ? nameElem.innerText.trim() : '';
                        
                        // Weight/size
                        const weightElem = card.querySelector('[qa="product_weight"]');
                        const weight = weightElem ? weightElem.innerText.trim() : '';
                        
                        // Current price
                        const priceElem = card.querySelector('[qa="product_price"]');
                        let price = null;
                        if (priceElem) {{
                            const priceText = priceElem.innerText.trim();
                            const match = priceText.match(/₹([\\d,]+)/);
                            if (match) {{
                                price = parseFloat(match[1].replace(/,/g, ''));
                            }}
                        }}
                        
                        // Original price (MRP)
                        const mrpElem = card.querySelector('[qa="product_mrp"]');
                        let originalPrice = null;
                        if (mrpElem) {{
                            const mrpText = mrpElem.innerText.trim();
                            const match = mrpText.match(/₹([\\d,]+)/);
                            if (match) {{
                                originalPrice = parseFloat(match[1].replace(/,/g, ''));
                            }}
                        }}
                        
                        // Discount
                        let discount = null;
                        if (price && originalPrice && originalPrice > price) {{
                            discount = Math.round(((originalPrice - price) / originalPrice) * 100);
                        }}
                        
                        // Product URL
                        const linkElem = card.querySelector('a[href*="/pd/"]');
                        const url = linkElem ? 'https://www.bigbasket.com' + linkElem.getAttribute('href') : '';
                        
                        // Image URL
                        const imgElem = card.querySelector('img');
                        const imageUrl = imgElem ? imgElem.getAttribute('src') : '';
                        
                        // Availability
                        const addButton = card.querySelector('[qa="add"]');
                        const available = addButton !== null;
                        
                        if (name && price) {{
                            products.push({{
                                name: name,
                                weight: weight,
                                price: price,
                                original_price: originalPrice,
                                discount: discount,
                                url: url,
                                image_url: imageUrl,
                                available: available
                            }});
                        }}
                    }}
                    
                    return products;
                }}
            """)

            print(f"🛍 Found {len(results)} products")
            for i, product in enumerate(results, 1):
                savings = f" (save ₹{product['original_price'] - product['price']})" if product.get('original_price') else ""
                print(f"{i}. {product['name']} - ₹{product['price']}{savings}")

            # Save session state
            context.storage_state(path=self.state)
            
            context.close()
            browser.close()
            
            return results
    
    def add_to_cart(self, product_urls: list):
        """
        Add products to cart by visiting their URLs and clicking add button.
        
        Args:
            product_urls: List of BigBasket product URLs
            
        Returns:
            dict with success status and count of added products
        """
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(storage_state=self.state)
            page = context.new_page()

            successful = 0
            failed = 0

            for url in product_urls:
                try:
                    print(f"➕ Adding product: {url}")
                    page.goto(url, wait_until="domcontentloaded")
                    
                    # Wait for add button
                    page.wait_for_selector('[qa="add"]', timeout=3000)
                    
                    # Click add button
                    page.click('[qa="add"]')
                    
                    # Wait a moment for cart to update
                    time.sleep(1)
                    
                    successful += 1
                    print(f"✅ Added to cart")
                    
                except Exception as e:
                    print(f"❌ Failed to add: {str(e)}")
                    failed += 1

            # Save session
            context.storage_state(path=self.state)
            
            context.close()
            browser.close()

            return {
                'success': successful > 0,
                'total_products': len(product_urls),
                'successful': successful,
                'failed': failed
            }
    
    def view_cart(self):
        """
        View current cart contents with items, quantities, and prices.
        
        Returns:
            dict with cart items, total items, subtotal, and cart status
        """
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(storage_state=self.state)
            page = context.new_page()

            print("🛒 Opening cart...")
            
            # Go to cart page
            page.goto(f"{self.base_url}/basket/", wait_until="domcontentloaded")
            
            # Wait for cart to load
            time.sleep(2)
            
            # Check if cart is empty
            empty_cart = page.query_selector('text=Your basket is empty')
            if empty_cart:
                print("🛒 Cart is empty")
                context.close()
                browser.close()
                return {
                    'cart_empty': True,
                    'cart_items': [],
                    'total_items': 0,
                    'subtotal': 0
                }
            
            # Extract cart data
            cart_data = page.evaluate("""
                () => {
                    const items = [];
                    const cartItems = document.querySelectorAll('[qa="cart_item"]');
                    
                    cartItems.forEach(item => {
                        const nameElem = item.querySelector('h3');
                        const name = nameElem ? nameElem.innerText.trim() : '';
                        
                        const weightElem = item.querySelector('[qa="item_weight"]');
                        const weight = weightElem ? weightElem.innerText.trim() : '';
                        
                        const qtyElem = item.querySelector('[qa="quantity"]');
                        const quantity = qtyElem ? parseInt(qtyElem.innerText.trim()) : 1;
                        
                        const priceElem = item.querySelector('[qa="item_price"]');
                        let price = 0;
                        if (priceElem) {
                            const match = priceElem.innerText.match(/₹([\\d,]+)/);
                            if (match) {
                                price = parseFloat(match[1].replace(/,/g, ''));
                            }
                        }
                        
                        if (name) {
                            items.push({
                                name: name,
                                weight: weight,
                                quantity: quantity,
                                price: price,
                                total_price: price * quantity
                            });
                        }
                    });
                    
                    // Get subtotal
                    const subtotalElem = document.querySelector('[qa="subtotal"]');
                    let subtotal = 0;
                    if (subtotalElem) {
                        const match = subtotalElem.innerText.match(/₹([\\d,]+)/);
                        if (match) {
                            subtotal = parseFloat(match[1].replace(/,/g, ''));
                        }
                    }
                    
                    return {
                        items: items,
                        subtotal: subtotal
                    };
                }
            """)
            
            total_items = sum(item['quantity'] for item in cart_data['items'])
            
            print(f"\n🛒 Cart Contents:")
            print(f"Total Items: {total_items}")
            for item in cart_data['items']:
                print(f"  • {item['name']} ({item['weight']}) x{item['quantity']} = ₹{item['total_price']}")
            print(f"Subtotal: ₹{cart_data['subtotal']}")
            
            context.close()
            browser.close()
            
            return {
                'cart_empty': False,
                'cart_items': cart_data['items'],
                'total_items': total_items,
                'subtotal': cart_data['subtotal']
            }
    
    def place_order(self):
        """
        Complete checkout and place order.
        
        Returns:
            dict with order status, order ID, delivery time, and payment method
        """
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(storage_state=self.state)
            page = context.new_page()

            print("🛒 Starting checkout...")
            
            # Go to cart
            page.goto(f"{self.base_url}/basket/", wait_until="domcontentloaded")
            time.sleep(2)
            
            try:
                # Click proceed to checkout
                page.click('[qa="proceed_checkout"]', timeout=5000)
                print("✅ Proceeding to checkout...")
                
                # Wait for checkout page
                page.wait_for_url('**/checkout/**', timeout=10000)
                time.sleep(2)
                
                # Select delivery slot (if needed)
                slot_button = page.query_selector('[qa="select_slot"]')
                if slot_button:
                    slot_button.click()
                    time.sleep(1)
                    # Select first available slot
                    first_slot = page.query_selector('[qa="slot_option"]')
                    if first_slot:
                        first_slot.click()
                        time.sleep(1)
                
                # Select payment method (Cash on Delivery by default)
                cod_option = page.query_selector('[qa="cod"]')
                if cod_option:
                    cod_option.click()
                    print("✅ Selected Cash on Delivery")
                    time.sleep(1)
                
                # Click place order
                page.click('[qa="place_order"]', timeout=5000)
                print("✅ Placing order...")
                
                # Wait for order confirmation
                page.wait_for_url('**/order-confirmation/**', timeout=15000)
                time.sleep(2)
                
                # Extract order details
                order_data = page.evaluate("""
                    () => {
                        const orderIdElem = document.querySelector('[qa="order_id"]');
                        const orderId = orderIdElem ? orderIdElem.innerText.trim() : null;
                        
                        const deliveryElem = document.querySelector('[qa="delivery_time"]');
                        const deliveryTime = deliveryElem ? deliveryElem.innerText.trim() : null;
                        
                        return {
                            order_id: orderId,
                            delivery_time: deliveryTime
                        };
                    }
                """)
                
                print(f"\n🎉 Order placed successfully!")
                if order_data['order_id']:
                    print(f"Order ID: {order_data['order_id']}")
                if order_data['delivery_time']:
                    print(f"Delivery Time: {order_data['delivery_time']}")
                
                context.storage_state(path=self.state)
                context.close()
                browser.close()
                
                return {
                    'final_status': 'completed',
                    'order_id': order_data['order_id'],
                    'delivery_time': order_data['delivery_time'],
                    'payment_method': 'Cash on Delivery'
                }
                
            except Exception as e:
                print(f"❌ Checkout failed: {str(e)}")
                context.close()
                browser.close()
                
                return {
                    'final_status': 'failed',
                    'error': str(e)
                }


# Example usage
if __name__ == "__main__":
    agent = BigBasketAgent()
    
    # Search for products
    products = agent.search_products("milk", limit=5)
    
    if products:
        # Add first product to cart
        agent.add_to_cart([products[0]['url']])
        
        # View cart
        agent.view_cart()
        
        # Place order (uncomment to actually place order)
        # agent.place_order()
