/**
 * Zepto Inventory Extractor
 * Hooks into Next.js hydration to extract product inventory
 */

(function() {
  'use strict';

  window.zeptoProducts = window.zeptoProducts || [];
  window.zeptoInventoryHistory = window.zeptoInventoryHistory || {};

  const config = {
    debug: false,
    pollInterval: null,
    scrollDelay: 2000,
    lowStockThreshold: 5
  };

  let originalPush = null;
  let processedChunkIds = new Set();

  function log(...args) {
    if (config.debug) console.log('[Zepto]', ...args);
  }

  function error(...args) {
    console.error('[Zepto Error]', ...args);
  }

  function initZeptoExtractor(options = {}) {
    Object.assign(config, options);
    log('Initializing Zepto Extractor');
    hookNextData();
    autoScroll();
  }

  function hookNextData() {
    if (typeof window.__next_f !== 'undefined' && typeof window.__next_f.push === 'function') {
      originalPush = window.__next_f.push;
      window.__next_f.push = function(chunk) {
        processChunk(chunk);
        return originalPush.apply(this, arguments);
      };
      log('Hooked into window.__next_f.push');
    } else {
      error('window.__next_f not found, retrying...');
      setTimeout(hookNextData, 1000);
    }
  }

  function processChunk(chunk) {
    if (!chunk || !Array.isArray(chunk) return;
    if (chunk.length < 2) return;

    const chunkId = chunk[0];
    if (processedChunkIds.has(chunkId)) return;
    processedChunkIds.add(chunkId);

    const stringData = chunk[1];
    if (typeof stringData !== 'string') return;

    if (stringData.includes('PRODUCT_GRID') || stringData.includes('preSearchData')) {
      log('Found PRODUCT_GRID chunk');
      extractProducts(stringData);
    }
  }

  function extractProducts(stringData) {
    try {
      const products = [];

      const productGridMatch = stringData.match(/"PRODUCT_GRID"\s*:\s*\{[\s\S]*?\}/g);
      if (!productGridMatch) {
        log('No PRODUCT_GRID found in chunk');
        return;
      }

      for (const gridData of productGridMatch) {
        const itemsMatch = gridData.match(/"items"\s*:\s*\[([\s\S]*?)\]/);
        if (!itemsMatch || !itemsMatch[1]) continue;

        try {
          const itemsData = JSON.parse('[' + itemsMatch[1] + ']');
          for (const item of itemsData) {
            const product = parseProductItem(item);
            if (product) products.push(product);
          }
        } catch (e) {
          log('Failed to parse items:', e.message);
        }
      }

      if (products.length > 0) {
        deduplicateAndStore(products);
        trackChanges();
        log(`Extracted ${products.length} products`);
      }
    } catch (e) {
      error('extractProducts:', e.message);
    }
  }

  function parseProductItem(item) {
    try {
      const cardData = item.cardData || item.data || item;
      if (!cardData) return null;

      const variantId = cardData.variantId || cardData.variant_id || cardData.id || null;
      if (!variantId) return null;

      const name = cardData.title || cardData.name || cardData.productName || '';
      const brand = cardData.brandName || cardData.brand || '';
      const variant = cardData.variantTitle || cardData.variant || '';

      let price = 0;
      if (cardData.price) {
        price = parseFloat(String(cardData.price).replace(/[^0-9.]/g, '')) || 0;
      } else if (cardData.mrp) {
        price = parseFloat(String(cardData.mrp).replace(/[^0-9.]/g, '')) || 0;
      }

      let mrp = 0;
      if (cardData.mrp) {
        mrp = parseFloat(String(cardData.mrp).replace(/[^0-9.]/g, '')) || 0;
      }

      const inventory = parseInt(cardData.availableQuantity || cardData.inventory || cardData.stock || 0);
      const maxAllowed = parseInt(cardData.maxAllowedQuantity || cardData.maxAllowed || cardData.max_allowed || 99) || 99;
      const inStock = !cardData.outOfStock && !cardData.out_of_stock && inventory > 0;

      const result = {
        name: String(name).trim(),
        brand: String(brand).trim(),
        variant: String(variant).trim(),
        product_id: String(cardData.productId || cardData.product_id || ''),
        variant_id: String(variantId),
        price: price,
        mrp: mrp,
        inventory: inventory,
        max_allowed: maxAllowed,
        in_stock: inStock,
        store_id: cardData.merchantId || cardData.store_id || cardData.assignedStoreId || '',
        timestamp: new Date().toISOString()
      };

      if (inventory <= config.lowStockThreshold && inStock) {
        console.warn(`[Zepto LOW STOCK] ${name} - ${variant}: ${inventory} left`);
      }

      return result;
    } catch (e) {
      error('parseProductItem:', e.message);
      return null;
    }
  }

  function deduplicateAndStore(newProducts) {
    for (const product of newProducts) {
      const existing = window.zeptoProducts.find(p => p.variant_id === product.variant_id);
      if (existing) {
        Object.assign(existing, product);
      } else {
        window.zeptoProducts.push(product);
      }
    }
    log(`Total products: ${window.zeptoProducts.length}`);
  }

  function trackChanges() {
    for (const product of window.zeptoProducts) {
      const key = product.variant_id;
      const prev = window.zeptoInventoryHistory[key];

      if (prev && prev.inventory !== product.inventory) {
        console.warn(`[INVENTORY CHANGE] ${product.name}: ${prev.inventory} → ${product.inventory}`);
      }

      window.zeptoInventoryHistory[key] = {
        inventory: product.inventory,
        timestamp: product.timestamp
      };
    }
  }

  function autoScroll() {
    try {
      const scrollable = document.querySelector('[style*="overflow-y: auto"], [style*="overflow-y: scroll"]');
      if (scrollable) {
        scrollable.scrollTop = scrollable.scrollHeight;
        log('Auto-scrolled');
      } else {
        window.scrollTo(0, document.body.scrollHeight);
      }
    } catch (e) {
      log('Auto-scroll failed:', e.message);
    }
  }

  function startPolling(intervalMs = 30000) {
    if (config.pollInterval) {
      clearInterval(config.pollInterval);
    }

    log(`Starting polling every ${intervalMs}ms`);
    config.pollInterval = setInterval(() => {
      autoScroll();
      triggerRefresh();
    }, intervalMs);
  }

  function stopPolling() {
    if (config.pollInterval) {
      clearInterval(config.pollInterval);
      config.pollInterval = null;
      log('Polling stopped');
    }
  }

  function triggerRefresh() {
    log('Triggering page refresh simulation');
  }

  function getProducts(filter = {}) {
    if (!filter) return window.zeptoProducts;

    return window.zeptoProducts.filter(p => {
      for (const key in filter) {
        if (p[key] !== filter[key]) return false;
      }
      return true;
    });
  }

  function getLowStockProducts(threshold = 5) {
    return window.zeptoProducts.filter(p => p.in_stock && p.inventory <= threshold);
  }

  function exportJSON() {
    return JSON.stringify(window.zeptoProducts, null, 2);
  }

  function clearData() {
    window.zeptoProducts = [];
    window.zeptoInventoryHistory = {};
    processedChunkIds.clear();
    log('Data cleared');
  }

  function setDebug(enabled = true) {
    config.debug = enabled;
    log('Debug:', enabled);
  }

  window.zeptoExtractor = {
    init: initZeptoExtractor,
    startPolling,
    stopPolling,
    getProducts,
    getLowStockProducts,
    exportJSON,
    clearData,
    setDebug,
    autoScroll,
    config
  };

  console.log('[Zepto] Extractor ready. Run: zeptoExtractor.init()');
})();