"""
Blinkit Scraper
===============
Standalone scraper for Blinkit that returns rich product data.

Setup flow identical to Zepto: browser opens → user sets up → presses Enter → scraping starts.

Key fix over the original BlinkitAgent:
  - Product URLs are extracted from real DOM anchor hrefs instead of being
    constructed from name slugs (which produced broken links).
"""

import os
import time
import json
from datetime import datetime
from playwright.sync_api import sync_playwright


SESSION_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "blinkit_state.json")
BASE_URL = "https://blinkit.com"


class BlinkitScraper:
    """Full-featured Blinkit scraper with session persistence."""

    def __init__(self, session_file: str = SESSION_FILE, headless: bool = False):
        self.session_file = os.path.abspath(session_file)
        self.headless = headless

    def _session_exists(self) -> bool:
        return os.path.exists(self.session_file)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def scrape(
        self,
        query: str,
        limit: int = 10,
        force_setup: bool = False,
    ) -> list:
        """
        Search Blinkit for `query` and return up to `limit` products.

        Args:
            query:       Search term, e.g. "amul milk"
            limit:       Max products to return (default 10)
            force_setup: Pause for user to login/set pincode even if session exists.

        Returns:
            List of product dicts (see README for schema).
        """
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=self.headless,
                args=["--disable-blink-features=AutomationControlled"],
            )

            if self._session_exists() and not force_setup:
                context = browser.new_context(
                    storage_state=self.session_file,
                    viewport={"width": 1400, "height": 900},
                    locale="en-IN",
                    timezone_id="Asia/Kolkata",
                )
            else:
                context = browser.new_context(
                    viewport={"width": 1400, "height": 900},
                    locale="en-IN",
                    timezone_id="Asia/Kolkata",
                )

            # Hide webdriver flag
            context.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )
            page = context.new_page()

            # ---- setup pause -----------------------------------------------
            needs_setup = force_setup or not self._session_exists()
            if needs_setup:
                print(f"\n🌐  Opening Blinkit in browser…")
                page.goto(BASE_URL, wait_until="domcontentloaded")
                print("━" * 60)
                print("  Please do the following in the browser window:")
                print("  1. Log in to your Blinkit account")
                print("  2. Set your delivery location / pincode")
                print("━" * 60)
                input("  ✅  Press Enter here when you're ready to start scraping… ")
                os.makedirs(os.path.dirname(self.session_file), exist_ok=True)
                context.storage_state(path=self.session_file)
                print(f"  💾  Session saved → {self.session_file}\n")

            # ---- scrape ----------------------------------------------------
            print(f"\n🔍  Blinkit — searching: '{query}'")
            products = self._search(page, context, query, limit)

            # Persist any cookie/location changes
            context.storage_state(path=self.session_file)
            context.close()
            browser.close()

        return products

    def scrape_many(
        self,
        queries: list,
        limit: int = 10,
        force_setup: bool = False,
    ) -> list:
        """Scrape multiple queries in a single browser session."""
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=self.headless,
                args=["--disable-blink-features=AutomationControlled"],
            )

            if self._session_exists() and not force_setup:
                context = browser.new_context(
                    storage_state=self.session_file,
                    viewport={"width": 1400, "height": 900},
                    locale="en-IN",
                    timezone_id="Asia/Kolkata",
                )
            else:
                context = browser.new_context(
                    viewport={"width": 1400, "height": 900},
                    locale="en-IN",
                    timezone_id="Asia/Kolkata",
                )

            context.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )
            page = context.new_page()

            needs_setup = force_setup or not self._session_exists()
            if needs_setup:
                page.goto(BASE_URL, wait_until="domcontentloaded")
                print("\n🌐  Opening Blinkit…")
                print("━" * 60)
                print("  1. Log in to Blinkit")
                print("  2. Set your delivery location")
                print("━" * 60)
                input("  ✅  Press Enter when ready… ")
                os.makedirs(os.path.dirname(self.session_file), exist_ok=True)
                context.storage_state(path=self.session_file)
                print(f"  💾  Session saved\n")

            all_products = []
            for q in queries:
                print(f"\n🔍  Blinkit — searching: '{q}'")
                results = self._search(page, context, q, limit)
                all_products.extend(results)
                print(f"     ↳ {len(results)} products found")

            context.storage_state(path=self.session_file)
            context.close()
            browser.close()

        return all_products

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _search(self, page, context, query: str, limit: int) -> list:
        """Navigate to search page and extract product data."""
        search_url = f"{BASE_URL}/s/?q={query.replace(' ', '%20')}"
        page.goto(search_url, wait_until="domcontentloaded")

        # Wait for product cards
        try:
            page.wait_for_selector(
                '.tw-text-300.tw-font-semibold.tw-line-clamp-2', timeout=8000
            )
        except Exception:
            print(f"     ⚠️  No products found for '{query}' on Blinkit")
            return []

        # Small pause to let lazy-loaded images settle
        time.sleep(1.5)

        now = datetime.now().isoformat(timespec="seconds")

        results = page.evaluate(f"""
            () => {{
                const limit = {limit};
                const products = [];

                // Each product lives inside a grid cell — grab the outermost card wrapper
                const cards = document.querySelectorAll('.tw-relative.tw-flex.tw-h-full.tw-flex-col.tw-pb-3');

                for (let i = 0; i < Math.min(limit, cards.length); i++) {{
                    const card = cards[i];

                    // ---- Name ----
                    const nameElem = card.querySelector('.tw-text-300.tw-font-semibold.tw-line-clamp-2');
                    const name = nameElem ? nameElem.innerText.trim() : '';
                    if (!name) continue;

                    // ---- Pack size / weight ----
                    const weightElem = card.querySelector('.tw-text-200.tw-font-medium.tw-line-clamp-1');
                    const pack_size = weightElem ? weightElem.innerText.trim() : '';

                    // ---- Price ----
                    const priceElems = card.querySelectorAll('.tw-text-200.tw-font-semibold');
                    let price = null;
                    if (priceElems.length > 0) {{
                        const m = priceElems[0].innerText.match(/₹([\\d,]+)/);
                        if (m) price = parseFloat(m[1].replace(/,/g, ''));
                    }}

                    // ---- MRP (struck-through original price) ----
                    const origElem = card.querySelector('.tw-line-through');
                    let mrp = null;
                    if (origElem) {{
                        const m = origElem.innerText.match(/₹([\\d,]+)/);
                        if (m) mrp = parseFloat(m[1].replace(/,/g, ''));
                    }}
                    if (!mrp) mrp = price;

                    // ---- Discount ----
                    const discElem = card.querySelector('.tw-text-050');
                    let discount_pct = null;
                    if (discElem) {{
                        const m = discElem.innerText.match(/([\\d]+)%/);
                        if (m) discount_pct = parseInt(m[1]);
                    }}
                    if (!discount_pct && mrp && price && mrp > price) {{
                        discount_pct = Math.round(((mrp - price) / mrp) * 100);
                    }}

                    const savings = (mrp && price && mrp > price) ? +(mrp - price).toFixed(2) : null;

                    // ---- Brand ----
                    // Blinkit doesn't have a dedicated brand slot; use first word of name as heuristic.
                    const brand = name.split(' ')[0] || '';

                    // ---- Product URL — read from real anchor href ----
                    // Cards are wrapped in <a> or have an ancestor <a>
                    let product_url = '';
                    let product_id  = '';
                    const anchor = card.closest('a') || card.querySelector('a');
                    if (anchor) {{
                        const href = anchor.getAttribute('href') || '';
                        product_url = href.startsWith('http') ? href : 'https://blinkit.com' + href;
                        // Extract prid (product ID) from URL: /prn/.../prid/123456
                        const m = href.match(/\\/prid\\/([\\d]+)/);
                        if (m) product_id = m[1];
                    }}

                    // ---- Stock & ETA ----
                    const addButton = card.querySelector('.tw-rounded-md.tw-font-okra');
                    const in_stock  = addButton !== null && addButton.innerText.trim().toUpperCase() === 'ADD';
                    const delivery_eta = '10 mins';   // Blinkit always shows this in the header, not per-product

                    // ---- Image ----
                    const imgElem  = card.querySelector('img');
                    const image_url = imgElem ? imgElem.src : '';

                    products.push({{
                        platform: 'blinkit',
                        name,
                        brand,
                        pack_size,
                        price,
                        mrp,
                        savings,
                        discount_pct,
                        in_stock,
                        delivery_eta,
                        product_url,
                        image_url,
                        product_id,
                    }});
                }}
                return products;
            }}
        """)

        for p in results:
            p["query"]      = query
            p["scraped_at"] = now

        return results
