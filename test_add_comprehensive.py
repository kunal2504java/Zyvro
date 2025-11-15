"""
Comprehensive test for add_to_cart with multiple product categories
"""

from blinkit import BlinkitAgent

print("=" * 60)
print("🧪 COMPREHENSIVE TEST: add_to_cart()")
print("=" * 60)

blinkit = BlinkitAgent()

# Test different product categories
test_categories = [
    ("bread", 2),
    ("chocolate", 2),
    ("chips", 2)
]

all_results = []

for category, limit in test_categories:
    print(f"\n{'='*60}")
    print(f"📦 Testing Category: {category.upper()}")
    print("=" * 60)
    
    # Search for products
    print(f"\n🔍 Searching for {category}...")
    products = blinkit.search_products(category, limit=limit)
    
    if not products:
        print(f"❌ No {category} products found!")
        continue
    
    print(f"✅ Found {len(products)} products")
    
    # Add to cart
    product_urls = [p['url'] for p in products]
    
    print(f"\n🛒 Adding {len(product_urls)} {category} products to cart...")
    result = blinkit.add_to_cart(product_urls)
    
    all_results.append({
        'category': category,
        'result': result
    })
    
    # Show results
    print(f"\n📊 Results for {category}:")
    print(f"   ✅ Added: {result['successful']}/{result['total_products']}")
    print(f"   ❌ Failed: {result['failed']}")

# Final summary
print(f"\n\n{'='*60}")
print("📈 OVERALL SUMMARY")
print("=" * 60)

total_tested = sum(r['result']['total_products'] for r in all_results)
total_success = sum(r['result']['successful'] for r in all_results)
total_failed = sum(r['result']['failed'] for r in all_results)

print(f"\nTotal products tested: {total_tested}")
print(f"✅ Successfully added: {total_success}")
print(f"❌ Failed: {total_failed}")
print(f"📊 Success rate: {(total_success/total_tested*100):.1f}%")

print(f"\nBreakdown by category:")
for r in all_results:
    cat = r['category']
    res = r['result']
    rate = (res['successful']/res['total_products']*100) if res['total_products'] > 0 else 0
    print(f"  {cat.capitalize()}: {res['successful']}/{res['total_products']} ({rate:.0f}%)")

if total_success == total_tested:
    print(f"\n🎉 PERFECT! All products added successfully!")
elif total_success > 0:
    print(f"\n⚠️ Partial success - some products failed")
else:
    print(f"\n❌ All products failed")

print("\n" + "=" * 60)
print("🏁 Comprehensive Test Complete!")
print("=" * 60)
