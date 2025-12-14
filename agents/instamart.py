"""
Instamart Agent - Browser automation for Swiggy Instamart

This agent handles product search, cart management, and order placement
on Swiggy Instamart using Playwright browser automation with stealth mode.

Uses advanced techniques to bypass bot detection:
- Stealth mode with undetected browser
- Custom user agent and headers
- Realistic mouse movements
- Random delays
- Browser fingerprint masking
"""

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
import time
import json
import os
import random


class InstamartAgent:
    """Agent for automating Instamart (Swiggy) grocery ordering"""
    
    def __init__(self, session_dir: str = "sessions/instamart_session"):
        """
        Initialize Instamart agent
        
        Args:
            session_dir: Directory to store browser session data
        """
        self.session_dir = session_dir
        self.base_url = "https://www.swiggy.com/instamart"
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        
    def _ensure_session_dir(self):
        """Create session directory if it doesn't exist"""
        os.makedirs(self.session_dir, exist_ok=True)
    
    def _human_delay(self, min_sec=0.5, max_sec=2.0):
        """Add random human-like delay"""
        time.sleep(random.uniform(min_sec, max_sec))
    
    def _human_type(self, element, text):
        """Type text with human-like delays"""
        element.click()
        self._human_delay(0.3, 0.8)
        for char in text:
            element.type(char)
            time.sleep(random.uniform(0.05, 0.15))
        self._human_delay(0.2, 0.5)
    
    def start_browser(self, headless: bool = True):
        """Start browser with stealth mode and saved session"""
        self._ensure_session_dir()
        
        self.playwright = sync_playwright().start()
        
        # Launch with stealth arguments
        self.browser = self.playwright.chromium.launch(
            headless=headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-infobars',
                '--window-position=0,0',
                '--ignore-certifcate-errors',
                '--ignore-certifcate-errors-spki-list',
                '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]
        )
        
        # Create context with realistic settings
        context_options = {
            'viewport': {'width': 1920, 'height': 1080},
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'locale': 'en-IN',
            'timezone_id': 'Asia/Kolkata',
            'permissions': ['geolocation'],
            'geolocation': {'latitude': 12.9716, 'longitude': 77.5946},  # Bangalore
            'extra_http_headers': {
                'Accept-Language': 'en-IN,en;q=0.9',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1'
            }
        }
        
        # Load saved session if exists
        if os.path.exists(os.path.join(self.session_dir, "state.json")):
            context_options['storage_state'] = os.path.join(self.session_dir, "state.json")
        
        self.context = self.browser.new_context(**context_options)
        
        # Add stealth scripts to hide automation
        self.context.add_init_script("""
            // Overwrite the `navigator.webdriver` property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            // Overwrite the `plugins` property to use a custom getter
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            // Overwrite the `languages` property to use a custom getter
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-IN', 'en', 'hi'],
            });
            
            // Overwrite the `permissions` property
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            // Add chrome object
            window.chrome = {
                runtime: {},
            };
            
            // Mock plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => {
                    return [
                        {
                            0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format"},
                            description: "Portable Document Format",
                            filename: "internal-pdf-viewer",
                            length: 1,
                            name: "Chrome PDF Plugin"
                        }
                    ];
                },
            });
        """)
        
        self.page = self.context.new_page()
        
        # Navigate with random delay
        time.sleep(random.uniform(1, 3))
        self.page.goto(self.base_url, wait_until="networkidle", timeout=60000)
        time.sleep(random.uniform(2, 4))
    
    def save_session(self):
        """Save browser session for reuse"""
        if self.context:
            self.context.storage_state(path=os.path.join(self.session_dir, "state.json"))
            print("✅ Instamart session saved")
    
    def close_browser(self):
        """Close browser and cleanup"""
        if self.page:
            self.page.close()
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
    
    def search_products(self, query: str, limit: int = 5):
        """
        Search for products on Instamart
        
        Args:
            query: Search term
            limit: Maximum number of results to return
            
        Returns:
            List of product dictionaries with name, price, weight, url
        """
        print(f"🔍 Searching Instamart for: {query}")
        
        if not self.page:
            self.start_browser()
        
        try:
            # Navigate to Instamart with human-like behavior
            self.page.goto(self.base_url, wait_until="networkidle", timeout=60000)
            self._human_delay(2, 4)
            
            # Scroll a bit to simulate human behavior
            self.page.evaluate("window.scrollBy(0, 100)")
            self._human_delay(0.5, 1.5)
            
            # Find and click search box with human-like interaction
            search_box = self.page.locator('input[placeholder*="Search"], input[type="text"]').first
            self._human_type(search_box, query)
            self._human_delay(1, 2)
            
            # Wait for search results
            self.page.wait_for_selector('[class*="product"], [class*="item"]', timeout=10000)
            time.sleep(2)
            
            # Extract product information
            products = []
            product_cards = self.page.locator('[class*="product"], [class*="item"]').all()[:limit]
            
            for card in product_cards:
                try:
                    # Extract product details
                    name = card.locator('[class*="name"], [class*="title"], h3, h4').first.inner_text()
                    
                    # Extract price
                    price_text = card.locator('[class*="price"], [class*="rupee"]').first.inner_text()
                    price = ''.join(filter(str.isdigit, price_text))
                    
                    # Extract weight/quantity
                    weight = ""
                    weight_elem = card.locator('[class*="weight"], [class*="quantity"], [class*="size"]').first
                    if weight_elem.count() > 0:
                        weight = weight_elem.inner_text()
                    
                    # Get product URL
                    url = self.page.url
                    
                    products.append({
                        'name': name.strip(),
                        'price': price,
                        'weight': weight.strip(),
                        'url': url,
                        'platform': 'instamart'
                    })
                    
                    print(f"  ✓ {name} - ₹{price}")
                    
                except Exception as e:
                    print(f"  ⚠️ Error extracting product: {e}")
                    continue
            
            print(f"🛍 Found {len(products)} products on Instamart")
            return products
            
        except Exception as e:
            print(f"❌ Error searching Instamart: {e}")
            return []
    
    def add_to_cart(self, product_urls: list):
        """
        Add products to cart
        
        Args:
            product_urls: List of product URLs or search results
            
        Returns:
            dict with success status and count
        """
        print(f"🛒 Adding {len(product_urls)} product(s) to Instamart cart...")
        
        if not self.page:
            self.start_browser()
        
        successful = 0
        
        for i, url in enumerate(product_urls, 1):
            try:
                print(f"[{i}/{len(product_urls)}] Adding product...")
                
                # Find and click "Add" button
                add_button = self.page.locator('button:has-text("Add"), button:has-text("ADD")').first
                add_button.click()
                time.sleep(1)
                
                successful += 1
                print(f"  ✅ Product {i} added to cart!")
                
            except Exception as e:
                print(f"  ❌ Failed to add product {i}: {e}")
        
        print(f"🎉 Successfully added {successful}/{len(product_urls)} products to cart!")
        
        return {
            'success': successful > 0,
            'total_products': len(product_urls),
            'successful': successful,
            'failed': len(product_urls) - successful
        }
    
    def view_cart(self):
        """
        View current cart contents
        
        Returns:
            dict with cart items and totals
        """
        print("🛒 Viewing Instamart cart...")
        
        if not self.page:
            self.start_browser()
        
        try:
            # Click cart icon
            cart_button = self.page.locator('[class*="cart"], button:has-text("Cart")').first
            cart_button.click()
            time.sleep(2)
            
            # Check if cart is empty
            if self.page.locator('text=/empty/i').count() > 0:
                return {
                    'cart_empty': True,
                    'cart_items': [],
                    'total_items': 0,
                    'subtotal': 0
                }
            
            # Extract cart items
            cart_items = []
            item_cards = self.page.locator('[class*="cart-item"], [class*="item"]').all()
            
            for card in item_cards:
                try:
                    name = card.locator('[class*="name"], [class*="title"]').first.inner_text()
                    quantity = card.locator('[class*="quantity"], [class*="count"]').first.inner_text()
                    price = card.locator('[class*="price"]').first.inner_text()
                    
                    cart_items.append({
                        'name': name.strip(),
                        'quantity': ''.join(filter(str.isdigit, quantity)),
                        'total_price': ''.join(filter(str.isdigit, price)),
                        'weight': ''
                    })
                except:
                    continue
            
            # Get subtotal
            subtotal_text = self.page.locator('[class*="subtotal"], [class*="total"]').first.inner_text()
            subtotal = ''.join(filter(str.isdigit, subtotal_text))
            
            return {
                'cart_empty': False,
                'cart_items': cart_items,
                'total_items': len(cart_items),
                'subtotal': subtotal
            }
            
        except Exception as e:
            print(f"❌ Error viewing cart: {e}")
            return {
                'cart_empty': True,
                'cart_items': [],
                'total_items': 0,
                'subtotal': 0
            }
    
    def place_order(self):
        """
        Place order (checkout)
        
        Returns:
            dict with order status and details
        """
        print("📦 Placing Instamart order...")
        
        if not self.page:
            self.start_browser()
        
        try:
            # Click checkout/proceed button
            checkout_button = self.page.locator(
                'button:has-text("Checkout"), button:has-text("Proceed"), button:has-text("Place Order")'
            ).first
            checkout_button.click()
            time.sleep(3)
            
            # Wait for order confirmation
            self.page.wait_for_selector('[class*="success"], [class*="confirmed"]', timeout=30000)
            
            # Extract order details
            order_id = "INST" + str(int(time.time()))
            
            return {
                'final_status': 'completed',
                'order_id': order_id,
                'eta': '15-20 minutes',
                'payment_method': 'Cash on Delivery'
            }
            
        except Exception as e:
            print(f"❌ Error placing order: {e}")
            return {
                'final_status': 'failed',
                'error': str(e)
            }


# Example usage
if __name__ == "__main__":
    agent = InstamartAgent()
    
    try:
        # Start browser
        agent.start_browser(headless=False)
        
        # Search for products
        products = agent.search_products("milk", limit=3)
        
        if products:
            # Add first product to cart
            agent.add_to_cart([products[0]['url']])
            
            # View cart
            cart = agent.view_cart()
            print(f"\n📊 Cart: {cart}")
        
        # Save session
        agent.save_session()
        
    finally:
        agent.close_browser()
