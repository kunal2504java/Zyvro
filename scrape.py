#!/usr/bin/env python3
"""
scrape.py — Zyvro Product Scraper CLI
======================================

Usage examples
--------------
# Single query, both platforms, save CSV + JSON
python scrape.py --query "amul milk" --platforms zepto blinkit

# Multiple queries at once
python scrape.py --queries "milk" "eggs" "bread" --platforms zepto --limit 20

# Read queries from a file (one per line)
python scrape.py --queries-file queries.txt --platforms blinkit --limit 15

# Force setup (re-login / change pincode)
python scrape.py --query "milk" --setup

# Only print to terminal, don't save files
python scrape.py --query "milk" --export none

# Export only JSON
python scrape.py --query "milk" --export json

Run headless (faster, no visible browser — requires saved session):
python scrape.py --query "milk" --headless
"""

import argparse
import asyncio
import sys
import os

# Make sure imports resolve whether we run from project root or anywhere
sys.path.insert(0, os.path.dirname(__file__))

from scraper.zepto_scraper import ZeptoScraper
from scraper.blinkit_scraper import BlinkitScraper
from scraper.exporter import print_table, export_all


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def load_queries_file(path: str) -> list:
    with open(path, encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]


def banner():
    print("""
╔══════════════════════════════════════════════╗
║        Zyvro — Product Scraper  🛒           ║
╚══════════════════════════════════════════════╝
""")


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Scrape product data from Zepto and/or Blinkit.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # ── Input ──────────────────────────────────────────────────────────
    query_group = parser.add_mutually_exclusive_group(required=True)
    query_group.add_argument(
        "--query",
        metavar="QUERY",
        help='Single search query, e.g. --query "amul milk"',
    )
    query_group.add_argument(
        "--queries",
        nargs="+",
        metavar="QUERY",
        help='Multiple queries, e.g. --queries milk eggs bread',
    )
    query_group.add_argument(
        "--queries-file",
        metavar="FILE",
        help="Path to a .txt file with one search query per line",
    )

    # ── Platforms ──────────────────────────────────────────────────────
    parser.add_argument(
        "--platforms",
        nargs="+",
        choices=["zepto", "blinkit"],
        default=["zepto", "blinkit"],
        metavar="PLATFORM",
        help="Platforms to scrape: zepto blinkit (default: both)",
    )

    # ── Scrape options ─────────────────────────────────────────────────
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        metavar="N",
        help="Max products per query per platform (default: 10)",
    )
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Pause before scraping so you can log in / set pincode (forces interactive setup even if session exists)",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode (requires a saved session; use --setup first if not logged in)",
    )

    # ── Export ─────────────────────────────────────────────────────────
    parser.add_argument(
        "--export",
        choices=["csv", "json", "both", "none"],
        default="both",
        help="Export format (default: both). 'none' prints only to terminal.",
    )

    args = parser.parse_args()

    # ── Resolve queries list ────────────────────────────────────────────
    if args.query:
        queries = [args.query]
    elif args.queries:
        queries = args.queries
    else:
        queries = load_queries_file(args.queries_file)

    if not queries:
        print("❌  No queries provided. Exiting.")
        sys.exit(1)

    banner()
    print(f"  Platforms : {', '.join(args.platforms)}")
    print(f"  Queries   : {', '.join(repr(q) for q in queries)}")
    print(f"  Limit     : {args.limit} per query per platform")
    print(f"  Export    : {args.export}")
    print(f"  Headless  : {args.headless}")
    print(f"  Setup     : {args.setup}\n")

    all_products: list = []

    # ──────────────────────────────────────────────────────────────────
    # ZEPTO
    # ──────────────────────────────────────────────────────────────────
    if "zepto" in args.platforms:
        print("━" * 60)
        print("  🟣  ZEPTO")
        print("━" * 60)

        zepto = ZeptoScraper(headless=args.headless)

        if len(queries) == 1:
            results = asyncio.run(
                zepto.scrape(queries[0], limit=args.limit, force_setup=args.setup)
            )
        else:
            results = asyncio.run(
                zepto.scrape_many(queries, limit=args.limit, force_setup=args.setup)
            )

        print(f"\n  ✅  Zepto total: {len(results)} products")
        all_products.extend(results)

    # ──────────────────────────────────────────────────────────────────
    # BLINKIT
    # ──────────────────────────────────────────────────────────────────
    if "blinkit" in args.platforms:
        print("━" * 60)
        print("  🟢  BLINKIT")
        print("━" * 60)

        blinkit = BlinkitScraper(headless=args.headless)

        if len(queries) == 1:
            results = blinkit.scrape(queries[0], limit=args.limit, force_setup=args.setup)
        else:
            results = blinkit.scrape_many(queries, limit=args.limit, force_setup=args.setup)

        print(f"\n  ✅  Blinkit total: {len(results)} products")
        all_products.extend(results)

    # ──────────────────────────────────────────────────────────────────
    # Output
    # ──────────────────────────────────────────────────────────────────
    print("\n" + "━" * 60)
    print("  RESULTS")
    print("━" * 60)

    print_table(all_products)

    if args.export != "none" and all_products:
        print("  Saving files…")
        files = export_all(all_products, fmt=args.export)
        print(f"\n  {len(files)} file(s) written to output/")

    print("\n  Done. 🎉\n")


if __name__ == "__main__":
    main()
