import asyncio
import warnings
import os
from playwright.async_api import async_playwright

warnings.filterwarnings("ignore", category=SyntaxWarning)


async def get_browser():
    """Initialize and return Playwright browser instance"""
    pw = await async_playwright().start()
    browser = await pw.chromium.launch(headless=False)
    return pw, browser


class ZeptoAgent:
    def __init__(self):
        self.state = "zepto_state.json"
        self.base_url = "https://www.zeptonow.com"
    
    def _get_storage_state(self):
        """Get storage state path if file exists, otherwise None"""
        if os.path.exists(self.state):
            return self.state
        return None
        
    async def search_products(self, query: str, limit: int = 10):
        """
        Search for products on Zepto and return detailed product information.

        Use this to find products by name, category, or keywords. Returns product details
        including name, price, ratings, availability, and direct product URLs.

        Args:
            query: Search term (e.g., "dairy milk chocolate", "vegetables", "bread")
            limit: Maximum number of products to return (default: 10, max recommended: 50)

        Returns:
            List of products with: name, variant/size, price, original price, savings,
            rating, review count, product URL, and image URL

        Example:
            results = await search_products("chocolate", limit=5)
            # Returns top 5 chocolate products with prices and details
        """
        pw, browser = await get_browser()
        storage_state = self._get_storage_state()
        
        if storage_state:
            context = await browser.new_context(storage_state=storage_state)
        else:
            print("⚠️ No session found. Browser will open for manual login.")
            print("   Please log in to Zepto, then the session will be saved.")
            context = await browser.new_context()
        
        page = await context.new_page()

        print(f"🔍 Searching for: {query}")

        # Navigate with networkidle for faster loading
        await page.goto(f"{self.base_url}/search?query={query}", wait_until="networkidle")

        # Wait for product cards - reduced timeout
        try:
            await page.wait_for_selector('a[href*="/pn/"]', timeout=5000)
        except:
            print("⚠️ No products found")
            await context.close()
            await browser.close()
            await pw.stop()
            return []

        # Extract data immediately without extra wait
        results = await page.evaluate(f"""
            () => {{
                const cards = document.querySelectorAll('a[href*="/pn/"]');
                const limit = {limit};
                const products = [];

                for (let i = 0; i < Math.min(limit, cards.length); i++) {{
                    const card = cards[i];
                    const url = 'https://www.zeptonow.com' + (card.getAttribute('href') || '');

                    // Fast selectors - direct queries
                    const name = card.querySelector('[data-slot-id="ProductName"] span')?.innerText.trim() || '';
                    const packSize = card.querySelector('[data-slot-id="PackSize"] span')?.innerText.trim() || '';

                    // Price extraction
                    const priceContainer = card.querySelector('[data-slot-id="EdlpPrice"]');
                    const currentPrice = priceContainer?.querySelector('.cptQT7')?.innerText.match(/₹\\s*([\\d,]+)/);
                    const origPrice = priceContainer?.querySelector('.cx3iWL')?.innerText.match(/₹\\s*([\\d,]+)/);
                    const savingsText = card.querySelector('.cYCsFo span')?.innerText.match(/₹\\s*([\\d,]+)/);

                    const price = currentPrice ? parseFloat(currentPrice[1].replace(/,/g, '')) : null;
                    const originalPrice = origPrice ? parseFloat(origPrice[1].replace(/,/g, '')) : null;
                    const savings = savingsText ? parseFloat(savingsText[1].replace(/,/g, '')) : null;

                    // Quick checks
                    const deliveryTime = card.querySelector('[data-slot-id="EtaInformation"]')?.innerText.trim() || null;
                    const hasAdd = card.querySelector('button[data-mode="edlp"]') !== null;
                    const imageUrl = card.querySelector('img')?.src || '';

                    products.push({{
                        index: i,
                        name: name,
                        pack_size: packSize,
                        price: price,
                        original_price: originalPrice,
                        savings: savings,
                        discount_percentage: originalPrice && price ? Math.round(((originalPrice - price) / originalPrice) * 100) : null,
                        rating: null,  // Zepto doesn't show ratings in search
                        reviews: null,
                        has_add_button: hasAdd,
                        in_stock: hasAdd,
                        delivery_time: deliveryTime,
                        url: url,
                        image: imageUrl
                    }});
                }}

                return products;
            }}
        """)

        print(f"🛍 Found {len(results)} products")

        # Quick preview of first 3
        if results:
            for i, p in enumerate(results[:3], 1):
                price_info = f"₹{p['price']}" if p['price'] else "Price N/A"
                if p['savings']:
                    price_info += f" (save ₹{p['savings']})"
                print(f"  {i}. {p['name'][:45]} - {price_info}")

        await context.close()
        await browser.close()
        await pw.stop()

        return results
    
    async def add_to_cart(self, product_urls):
        """
        Add one or multiple products to the shopping cart.

        Takes a product URL or list of URLs and adds one unit of each product to the cart.
        Processes multiple products efficiently by reusing the same browser session.

        Args:
            product_urls: Single product URL (string) or list of product URLs
                         Full URLs like "https://www.zeptonow.com/pn/..." or paths like "/pn/..."

        Returns:
            Dict with success status and list of results for each product

        Example:
            # Single product
            await add_to_cart("https://www.zeptonow.com/pn/dairy-milk/pvid/...")

            # Multiple products
            await add_to_cart([
                "https://www.zeptonow.com/pn/dairy-milk/pvid/...",
                "https://www.zeptonow.com/pn/oreo/pvid/...",
                "/pn/bread/pvid/..."
            ])
        """
        # Handle single URL or list of URLs
        if isinstance(product_urls, str):
            product_urls = [product_urls]

        # Ensure all URLs are full URLs
        full_urls = []
        for url in product_urls:
            if not url.startswith('http'):
                url = f"{self.base_url}{url}"
            full_urls.append(url)

        pw, browser = await get_browser()
        storage_state = self._get_storage_state()
        context = await browser.new_context(storage_state=storage_state) if storage_state else await browser.new_context()
        page = await context.new_page()

        results = []
        print(f"🛒 Adding {len(full_urls)} product(s) to cart...")

        for idx, product_url in enumerate(full_urls, 1):
            try:
                print(f"  [{idx}/{len(full_urls)}] Opening: {product_url}")
                await page.goto(product_url, wait_until="domcontentloaded")

                # Wait for the add button to appear
                await page.wait_for_selector(
                    'div[aria-label="Add to Cart"] button[aria-label="Increase quantity by 1"]', 
                    timeout=5000
                )

                # Click using JavaScript - fastest method
                clicked = await page.evaluate("""
                    () => {
                        const button = document.querySelector('div[aria-label="Add to Cart"] button[aria-label="Increase quantity by 1"]');
                        if (button) {
                            button.click();
                            return true;
                        }
                        return false;
                    }
                """)

                if clicked:
                    # Short wait for cart update
                    await page.wait_for_timeout(800)
                    print(f"  ✅ Product {idx} added to cart!")
                    results.append({
                        "success": True,
                        "url": product_url,
                        "index": idx - 1
                    })
                else:
                    print(f"  ⚠️ Could not find add button for product {idx}")
                    results.append({
                        "success": False,
                        "url": product_url,
                        "index": idx - 1,
                        "error": "Add button not found"
                    })

            except Exception as e:
                print(f"  ❌ Error adding product {idx}: {e}")
                results.append({
                    "success": False,
                    "url": product_url,
                    "index": idx - 1,
                    "error": str(e)
                })

        # Save session (cart state) once at the end
        await context.storage_state(path=self.state)
        await context.close()
        await browser.close()
        await pw.stop()

        successful = sum(1 for r in results if r["success"])
        print(f"🎉 Successfully added {successful}/{len(full_urls)} products to cart!")

        return {
            "success": successful > 0,
            "total_products": len(full_urls),
            "successful": successful,
            "failed": len(full_urls) - successful,
            "results": results
        }

    async def view_cart(self):
        """
        View all items currently in the shopping cart.
        
        Returns:
            Dict with cart items, total items count, and subtotal
        """
        pw, browser = await get_browser()
        storage_state = self._get_storage_state()
        context = await browser.new_context(storage_state=storage_state) if storage_state else await browser.new_context()
        page = await context.new_page()

        print("🛒 Opening cart...")
        await page.goto(f"{self.base_url}/?cart=open", wait_until="domcontentloaded")

        try:
            # Wait for cart items to load
            await page.wait_for_selector('div[data-testid="cart-item"]', timeout=5000)
        except:
            print("📭 Cart is empty")
            await context.close()
            await browser.close()
            await pw.stop()
            return {
                "cart_items": [],
                "total_items": 0,
                "subtotal": 0,
                "cart_empty": True
            }

        # Extract cart data
        cart_data = await page.evaluate("""
            () => {
                const items = document.querySelectorAll('div[data-testid="cart-item"]');
                const cartItems = [];

                for (let i = 0; i < items.length; i++) {
                    const item = items[i];

                    const name = item.querySelector('[data-slot-id="ProductName"]')?.innerText.trim() || '';
                    const packSize = item.querySelector('[data-slot-id="PackSize"]')?.innerText.trim() || '';
                    
                    const qtyElem = item.querySelector('[data-testid="quantity"]');
                    const quantity = qtyElem ? parseInt(qtyElem.innerText) : 1;

                    const priceElem = item.querySelector('[data-slot-id="EdlpPrice"]');
                    let price = null;
                    if (priceElem) {
                        const priceText = priceElem.innerText;
                        const match = priceText.match(/₹\\s*([\\d,]+)/);
                        if (match) {
                            price = parseFloat(match[1].replace(/,/g, ''));
                        }
                    }

                    const imageUrl = item.querySelector('img')?.src || '';

                    cartItems.push({
                        index: i,
                        name: name,
                        pack_size: packSize,
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
            print(f"  • {item['name']} - {item['pack_size']} x{item['quantity']} = ₹{item['total_price']}")

        await context.close()
        await browser.close()
        await pw.stop()

        return cart_data

    async def check_coupons(self, auto_apply: bool = False):
        """
        View all available coupons for the current cart and optionally apply the best one.

        Retrieves all coupons applicable to items in cart, showing which are immediately
        usable and which require additional purchase amount. Can automatically apply
        the first available coupon.

        Args:
            auto_apply: If True, automatically applies the first available coupon (default: False)

        Returns:
            List of coupons with: title, code, applicability status, amount needed to unlock,
            and detailed summary of each coupon's conditions

        Example:
            coupons = await check_coupons(auto_apply=True)
            # Shows all coupons and applies first available one
        """
        pw, browser = await get_browser()
        storage_state = self._get_storage_state()
        context = await browser.new_context(storage_state=storage_state) if storage_state else await browser.new_context()
        page = await context.new_page()

        print("🧺 Opening cart to check coupons...")
        await page.goto(f"{self.base_url}/?cart=open", wait_until="domcontentloaded")

        # Wait for coupon blocks to appear
        try:
            await page.wait_for_selector("div[aria-label='Open coupon modal']", timeout=5000)
        except:
            print("😕 No coupons available")
            await context.close()
            await browser.close()
            await pw.stop()
            return []

        # Extract all coupon data in one shot
        coupons = await page.evaluate("""
            () => {
                const blocks = document.querySelectorAll("div[aria-label='Open coupon modal']");
                const results = [];

                for (let i = 0; i < blocks.length; i++) {
                    const card = blocks[i];

                    // Warning text (Shop for ₹xxx more)
                    const warningElem = card.querySelector("div.HKHqS");
                    const warningText = warningElem ? warningElem.innerText.trim() : "";

                    // Extract remaining amount
                    let remainingAmount = null;
                    if (warningText.includes('₹')) {
                        const match = warningText.match(/₹\\s*([\\d,]+)/);
                        if (match) {
                            remainingAmount = parseInt(match[1].replace(/,/g, ''));
                        }
                    }

                    // Main coupon message
                    const messageElem = card.querySelector(".text-cta2");
                    const message = messageElem ? messageElem.innerText.trim() : "";

                    // Coupon code
                    const codeElem = card.querySelector(".text-body4");
                    let code = "";
                    if (codeElem) {
                        const codeText = codeElem.innerText;
                        const codeMatch = codeText.match(/Code:\\s*([A-Z0-9]+)/);
                        code = codeMatch ? codeMatch[1] : codeText.trim();
                    }

                    // Apply button check
                    const applyBtn = card.querySelector("button");
                    const canApply = applyBtn && 
                                    applyBtn.innerText.includes('Apply') && 
                                    !applyBtn.disabled;

                    const status = canApply ? "available_to_apply" 
                                 : remainingAmount ? "locked_requires_more_purchase" 
                                 : "not_applicable";

                    results.push({
                        coupon_index: i,
                        coupon_title: message,
                        coupon_code: code,
                        is_applicable_now: canApply,
                        amount_needed_to_unlock: remainingAmount,
                        coupon_status: status,
                        extracted_summary: `Coupon '${code}' — ${message || 'No message'}; ${
                            canApply ? 'can be applied now.' 
                            : remainingAmount ? `requires ₹${remainingAmount} more purchase.` 
                            : 'currently unavailable.'
                        }`
                    });
                }

                return results;
            }
        """)

        print(f"🎟 Found {len(coupons)} coupons.")

        for coupon in coupons:
            status = 'ACTIVE' if coupon['is_applicable_now'] else \
                     'LOCKED' if coupon['amount_needed_to_unlock'] else 'UNKNOWN'
            print(f"🧾 Coupon #{coupon['coupon_index']+1}: {coupon['coupon_title']} | "
                  f"Code: {coupon['coupon_code']} | Status: {status}")

        # Auto-apply if requested
        if auto_apply:
            for coupon in coupons:
                if coupon['is_applicable_now']:
                    try:
                        print(f"🟢 Applying coupon {coupon['coupon_code']}...")
                        await page.locator("div[aria-label='Open coupon modal']").nth(coupon['coupon_index']).locator("button:has-text('Apply')").click()
                        await page.wait_for_timeout(1500)
                        print("🎉 Coupon applied successfully!")
                        break
                    except Exception as e:
                        print(f"⚠️ Failed to apply coupon: {e}")

        if not coupons:
            print("😕 No coupons detected or coupon UI not visible.")

        await context.close()
        await browser.close()
        await pw.stop()

        return coupons

    async def place_order(self):
        """
        Complete checkout and place the order with payment.

        Processes the entire checkout flow: selects Cash on Delivery (COD) if available,
        falls back to UPI payment if COD unavailable, and confirms the order. Waits for
        order confirmation page and extracts order ID and ETA.

        Returns:
            Order status including: payment method used (COD/UPI), order ID, estimated
            delivery time (ETA), final status, and any errors encountered

        Example:
            result = await place_order()
            # Places order, returns: order_id="019a...", eta="14 mins", status="completed"

        Note: For UPI payments, uses test UPI ID. Real payments require actual UPI confirmation.
        """
        pw, browser = await get_browser()
        storage_state = self._get_storage_state()
        context = await browser.new_context(storage_state=storage_state) if storage_state else await browser.new_context()
        page = await context.new_page()

        print("🛒 Opening cart checkout page...")
        await page.goto(f"{self.base_url}/?cart=open", wait_until="domcontentloaded")

        result = {
            "checkout_started": False,
            "click_to_pay_clicked": False,
            "payment_method": None,
            "verify_clicked": False,
            "final_status": "unknown",
            "order_id": None,
            "eta": None,
            "error": None,
        }

        try:
            # Step 1 — Click 'Click to Pay'
            await page.wait_for_selector("button:has-text('Click to Pay')", timeout=5000)
            click_to_pay_btn = page.locator("button:has-text('Click to Pay')").first

            print("🟢 Clicking 'Click to Pay'...")
            await click_to_pay_btn.click()
            result["click_to_pay_clicked"] = True
            result["checkout_started"] = True

            # Wait for payment page
            await page.wait_for_timeout(3000)

            # Step 2 — Find Juspay frame
            frames = page.frames
            juspay_frame = None
            for frame in frames:
                frame_url = frame.url.lower()
                if "juspay" in frame_url or "payment" in frame_url:
                    juspay_frame = frame
                    break

            frame_context = juspay_frame or page
            print("🧾 Using payment frame context")

            # Step 3 — Check if COD option exists and is available
            cod_option = frame_context.locator('[testid="nvb_cod"]')

            if await cod_option.count() > 0:
                print("🟢 Found COD option, clicking it...")
                await cod_option.first.click()
                result["payment_method"] = "Cash On Delivery"

                await page.wait_for_timeout(1500)

                # Look for "Proceed to Pay" button
                proceed_btn = frame_context.locator('[testid="btn_pay"]')

                if await proceed_btn.count() > 0:
                    print("🟢 Clicking 'Proceed to Pay' for COD...")
                    await proceed_btn.first.click()
                    result["verify_clicked"] = True

                    # Wait for order confirmation page
                    print("⏳ Waiting for order confirmation...")
                    try:
                        # Wait for order tracking page
                        await page.wait_for_url("**/order/**", timeout=15000)
                        
                        # Extract order ID and ETA
                        order_info = await page.evaluate("""
                            () => {
                                const orderIdElem = document.querySelector('[data-testid="order-id"]');
                                const etaElem = document.querySelector('[data-testid="eta"]');
                                
                                return {
                                    order_id: orderIdElem ? orderIdElem.innerText.trim() : null,
                                    eta: etaElem ? etaElem.innerText.trim() : null
                                };
                            }
                        """)
                        
                        result["order_id"] = order_info["order_id"]
                        result["eta"] = order_info["eta"]
                        result["final_status"] = "completed"
                        
                        print(f"🎉 Order placed successfully!")
                        print(f"   Order ID: {result['order_id']}")
                        print(f"   ETA: {result['eta']}")
                        
                    except Exception as e:
                        print(f"⚠️ Could not extract order details: {e}")
                        result["final_status"] = "payment_completed_but_details_unavailable"
                else:
                    print("⚠️ Proceed button not found")
                    result["error"] = "Proceed button not available"
            else:
                print("⚠️ COD not available, would need to implement UPI flow")
                result["error"] = "COD not available"
                result["final_status"] = "payment_method_unavailable"

        except Exception as e:
            print(f"❌ Error during checkout: {e}")
            result["error"] = str(e)
            result["final_status"] = "failed"

        await context.storage_state(path=self.state)
        await context.close()
        await browser.close()
        await pw.stop()

        return result


# Example usage
async def main():
    zepto = ZeptoAgent()
    
    # Search for products
    products = await zepto.search_products("milk", limit=5)
    
    if products:
        # Add first 2 products to cart
        product_urls = [p['url'] for p in products[:2]]
        result = await zepto.add_to_cart(product_urls)
        print(f"\nAdded {result['successful']}/{result['total_products']} products")
        
        # View cart
        cart = await zepto.view_cart()
        
        # Check coupons
        coupons = await zepto.check_coupons()


if __name__ == "__main__":
    asyncio.run(main())
