"""
Zepto Scraper
=============
Standalone scraper for Zepto that returns rich product data.

Setup flow (--setup or no saved session):
  Browser opens → user logs in & sets pincode → presses Enter → session saved → scraping starts.

On subsequent runs with a saved session the browser goes straight to the search page.
Use --setup to force the interactive pause even when a session already exists.
"""

import os
import asyncio
import json
from datetime import datetime
from playwright.async_api import async_playwright


SESSION_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "zepto_state.json")
BASE_URL = "https://www.zeptonow.com"


class ZeptoScraper:
    """Full-featured Zepto scraper with session persistence."""

    def __init__(self, session_file: str = SESSION_FILE, headless: bool = False):
        self.session_file = os.path.abspath(session_file)
        self.headless = headless

    def _session_exists(self) -> bool:
        return os.path.exists(self.session_file)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def scrape(
        self,
        query: str,
        limit: int = 10,
        force_setup: bool = False,
    ) -> list[dict]:
        """
        Search Zepto for `query` and return up to `limit` products.

        Args:
            query:       Search term, e.g. "amul milk"
            limit:       Max products to return (default 10)
            force_setup: If True, pause for the user to login/set pincode even
                         when a session file already exists.

        Returns:
            List of product dicts (see README for schema).
        """
        pw = await async_playwright().start()
        browser = await pw.chromium.launch(headless=self.headless)

        # Load saved session or start fresh
        if self._session_exists() and not force_setup:
            context = await browser.new_context(storage_state=self.session_file)
        else:
            context = await browser.new_context(
                viewport={"width": 1400, "height": 900},
                locale="en-IN",
                timezone_id="Asia/Kolkata",
            )

        page = await context.new_page()

        # ---- setup pause if needed ----------------------------------------
        needs_setup = force_setup or not self._session_exists()
        if needs_setup:
            print(f"\n🌐  Opening Zepto in browser…")
            await page.goto(BASE_URL, wait_until="domcontentloaded")
            print("━" * 60)
            print("  Please do the following in the browser window:")
            print("  1. Log in to your Zepto account")
            print("  2. Set your delivery pincode / location")
            print("━" * 60)
            input("  ✅  Press Enter here when you're ready to start scraping… ")
            # Save session so next run skips this step
            os.makedirs(os.path.dirname(self.session_file), exist_ok=True)
            await context.storage_state(path=self.session_file)
            print(f"  💾  Session saved → {self.session_file}\n")

        # ---- scrape -------------------------------------------------------
        products = await self._search(page, query, limit)

        # Persist any cookie changes (e.g. location cookies set this run)
        await context.storage_state(path=self.session_file)

        await context.close()
        await browser.close()
        await pw.stop()

        return products

    async def scrape_many(
        self,
        queries: list[str],
        limit: int = 10,
        force_setup: bool = False,
    ) -> list[dict]:
        """Scrape multiple queries in a single browser session."""
        pw = await async_playwright().start()
        browser = await pw.chromium.launch(headless=self.headless)

        if self._session_exists() and not force_setup:
            context = await browser.new_context(storage_state=self.session_file)
        else:
            context = await browser.new_context(
                viewport={"width": 1400, "height": 900},
                locale="en-IN",
                timezone_id="Asia/Kolkata",
            )

        page = await context.new_page()

        needs_setup = force_setup or not self._session_exists()
        if needs_setup:
            await page.goto(BASE_URL, wait_until="domcontentloaded")
            print("\n🌐  Opening Zepto…")
            print("━" * 60)
            print("  1. Log in to Zepto")
            print("  2. Set your delivery pincode")
            print("━" * 60)
            input("  ✅  Press Enter when ready… ")
            os.makedirs(os.path.dirname(self.session_file), exist_ok=True)
            await context.storage_state(path=self.session_file)
            print(f"  💾  Session saved\n")

        all_products: list[dict] = []
        for q in queries:
            print(f"\n🔍  Zepto — searching: '{q}'")
            results = await self._search(page, q, limit)
            all_products.extend(results)
            print(f"     ↳ {len(results)} products found")

        await context.storage_state(path=self.session_file)
        await context.close()
        await browser.close()
        await pw.stop()

        return all_products

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _search(self, page, query: str, limit: int) -> list[dict]:
        """Navigate to search page and extract product data."""
        url = f"{BASE_URL}/search?query={query.replace(' ', '%20')}"
        await page.goto(url, wait_until="networkidle")

        # Wait for at least one product card
        try:
            await page.wait_for_selector('a[href*="/pn/"]', timeout=8000)
        except Exception:
            print(f"     ⚠️  No products found for '{query}' on Zepto")
            return []

        now = datetime.now().isoformat(timespec="seconds")

        results: list[dict] = await page.evaluate(f"""
            () => {{
                const cards = document.querySelectorAll('a[href*="/pn/"]');
                const limit = {limit};
                const products = [];

                for (let i = 0; i < Math.min(limit, cards.length); i++) {{
                    const card = cards[i];
                    const href = card.getAttribute('href') || '';
                    const url = 'https://www.zeptonow.com' + href;

                    // Product ID from URL slug  e.g. /pn/amul-gold/pvid/abc123
                    const pvid_match = href.match(/\\/pvid\\/([^/?]+)/);
                    const product_id = pvid_match ? pvid_match[1] : '';

                    const name = card.querySelector('[data-slot-id="ProductName"] span')?.innerText.trim() || '';
                    const pack_size = card.querySelector('[data-slot-id="PackSize"] span')?.innerText.trim() || '';
                    const delivery_eta = card.querySelector('[data-slot-id="EtaInformation"]')?.innerText.trim() || '';

                    // Brand: often the first word of the name or a dedicated element
                    const brandElem = card.querySelector('[data-slot-id="BrandName"]');
                    const brand = brandElem ? brandElem.innerText.trim() : (name.split(' ')[0] || '');

                    // Pricing
                    const priceContainer = card.querySelector('[data-slot-id="EdlpPrice"]');
                    const priceMatch = priceContainer?.querySelector('.cptQT7')?.innerText.match(/₹\\s*([\\d,]+)/);
                    const origMatch  = priceContainer?.querySelector('.cx3iWL')?.innerText.match(/₹\\s*([\\d,]+)/);
                    const saveMatch  = card.querySelector('.cYCsFo span')?.innerText.match(/₹\\s*([\\d,]+)/);

                    const price    = priceMatch ? parseFloat(priceMatch[1].replace(/,/g,'')) : null;
                    const mrp      = origMatch  ? parseFloat(origMatch[1].replace(/,/g,''))  : price;
                    const savings  = saveMatch  ? parseFloat(saveMatch[1].replace(/,/g,''))  : (mrp && price ? mrp - price : null);
                    const disc_pct = (mrp && price && mrp > price)
                                     ? Math.round(((mrp - price) / mrp) * 100) : null;

                    const in_stock  = card.querySelector('button[data-mode="edlp"]') !== null;
                    const image_url = card.querySelector('img')?.src || '';

                    if (!name) continue;
                    products.push({{
                        platform:     'zepto',
                        name,
                        brand,
                        pack_size,
                        price,
                        mrp,
                        savings,
                        discount_pct: disc_pct,
                        in_stock,
                        delivery_eta,
                        product_url:  url,
                        image_url,
                        product_id,
                    }});
                }}
                return products;
            }}
        """)

        scraped_at = now
        query_tag  = query
        for p in results:
            p["query"]      = query_tag
            p["scraped_at"] = scraped_at

        return results
