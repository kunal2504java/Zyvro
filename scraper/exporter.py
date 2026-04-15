"""
Exporter
========
Saves scrape results to CSV / JSON and pretty-prints to terminal.

Output directory:  <project_root>/output/
Filename template: {platform}_{query}_{YYYYMMDD_HHMMSS}.{ext}
                   (spaces in query replaced with underscore)
"""

import os
import csv
import json
from datetime import datetime
from collections import defaultdict


OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output")

# Canonical column order for CSV / table output
COLUMNS = [
    "platform",
    "query",
    "name",
    "brand",
    "pack_size",
    "price",
    "mrp",
    "savings",
    "discount_pct",
    "in_stock",
    "delivery_eta",
    "product_url",
    "image_url",
    "product_id",
    "scraped_at",
]


def _ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def _make_filename(platform: str, query: str, ext: str) -> str:
    ts    = datetime.now().strftime("%Y%m%d_%H%M%S")
    q_tag = query.replace(" ", "_")[:30]
    return os.path.join(OUTPUT_DIR, f"{platform}_{q_tag}_{ts}.{ext}")


# ------------------------------------------------------------------
# CSV
# ------------------------------------------------------------------

def export_csv(products: list, filename: str = None) -> str:
    """
    Write products to a CSV file.

    Args:
        products: list of product dicts (all from the same platform+query, or mixed)
        filename: override output path (auto-generated if None)

    Returns:
        Absolute path of the written CSV file.
    """
    if not products:
        print("  ⚠️  No products to export.")
        return ""

    _ensure_output_dir()

    # Group by (platform, query) if no filename given so we get clean files
    if filename is None:
        platforms = list({p.get("platform", "unknown") for p in products})
        queries   = list({p.get("query", "unknown") for p in products})
        platform  = platforms[0] if len(platforms) == 1 else "multi"
        query     = queries[0]   if len(queries)   == 1 else "multi"
        filename  = _make_filename(platform, query, "csv")

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for row in products:
            writer.writerow({col: row.get(col, "") for col in COLUMNS})

    print(f"  📄  CSV saved → {filename}")
    return filename


# ------------------------------------------------------------------
# JSON
# ------------------------------------------------------------------

def export_json(products: list, filename: str = None) -> str:
    """
    Write products to a formatted JSON file.

    Returns:
        Absolute path of the written JSON file.
    """
    if not products:
        print("  ⚠️  No products to export.")
        return ""

    _ensure_output_dir()

    if filename is None:
        platforms = list({p.get("platform", "unknown") for p in products})
        queries   = list({p.get("query", "unknown") for p in products})
        platform  = platforms[0] if len(platforms) == 1 else "multi"
        query     = queries[0]   if len(queries)   == 1 else "multi"
        filename  = _make_filename(platform, query, "json")

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

    print(f"  📄  JSON saved → {filename}")
    return filename


# ------------------------------------------------------------------
# Terminal table
# ------------------------------------------------------------------

def print_table(products: list, max_name: int = 40, max_rows: int = 200):
    """
    Pretty-print a results table to stdout.

    Args:
        products:  list of product dicts
        max_name:  max characters to show for product name (truncated with …)
        max_rows:  cap terminal output at this many rows
    """
    if not products:
        print("  (no products to display)")
        return

    displayed = products[:max_rows]

    # ── Header ──────────────────────────────────────────────────────
    header = f"{'#':<4}  {'Platform':<9}  {'Query':<18}  {'Name':<{max_name}}  {'Pack':<12}  {'Price':>7}  {'MRP':>7}  {'Disc%':>5}  {'Stock':<6}  {'ETA':<10}"
    sep    = "─" * len(header)
    print(f"\n{sep}")
    print(header)
    print(sep)

    for i, p in enumerate(displayed, 1):
        name  = str(p.get("name", ""))
        name  = name if len(name) <= max_name else name[: max_name - 1] + "…"
        query = str(p.get("query", ""))[:18]
        pack  = str(p.get("pack_size", ""))[:12]
        price = f"₹{p['price']}"   if p.get("price")    else "—"
        mrp   = f"₹{p['mrp']}"     if p.get("mrp")      else "—"
        disc  = f"{p['discount_pct']}%" if p.get("discount_pct") else "—"
        stock = "✅" if p.get("in_stock") else "❌"
        eta   = str(p.get("delivery_eta", ""))[:10]
        platform = str(p.get("platform", ""))[:9]

        print(
            f"{i:<4}  {platform:<9}  {query:<18}  {name:<{max_name}}  "
            f"{pack:<12}  {price:>7}  {mrp:>7}  {disc:>5}  {stock:<6}  {eta:<10}"
        )

    print(sep)
    if len(products) > max_rows:
        print(f"  … {len(products) - max_rows} more rows not shown (export to CSV/JSON to see all)")
    print(f"  Total: {len(products)} product(s)\n")


# ------------------------------------------------------------------
# Utility: export per-platform-per-query (for bulk runs)
# ------------------------------------------------------------------

def export_all(products: list, fmt: str = "both") -> list:
    """
    Export a mixed list of products, grouping by (platform, query).
    Creates one file per group.

    Args:
        products: mixed list of product dicts
        fmt:      "csv" | "json" | "both" | "none"

    Returns:
        List of file paths written.
    """
    if fmt == "none" or not products:
        return []

    # Group
    groups = defaultdict(list)
    for p in products:
        key = (p.get("platform", "unknown"), p.get("query", "unknown"))
        groups[key].append(p)

    files = []
    for (platform, query), group in groups.items():
        if fmt in ("csv", "both"):
            f = export_csv(group, _make_filename(platform, query, "csv"))
            if f:
                files.append(f)
        if fmt in ("json", "both"):
            f = export_json(group, _make_filename(platform, query, "json"))
            if f:
                files.append(f)

    return files
