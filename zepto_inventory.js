/**
 * Zepto Inventory Extractor
 * Works by extracting from HTML (escaped JSON in page source)
 */

(function() {
    if (window._zeptoExtractorLoaded) return;
    window._zeptoExtractorLoaded = true;
    
    window._zeptoProducts = window._zeptoProducts || [];
    window._zeptoHistory = window._zeptoHistory || {};
    
    const config = {
        debug: true,
        lowStockThreshold: 5
    };
    
    function log() {
        console.log('[Zepto]', ...arguments);
    }
    
    function warn() {
        console.warn('[Zepto]', ...arguments);
    }
    
    function extractFromHTML() {
        try {
            var html = document.documentElement.innerHTML;
            
            // Unescape HTML entities
            html = html.replace(/\\"/g, '"');
            
            // Find all products: baseProductId followed by availableQuantity
            var pattern = /baseProductId":"([^"]+)".*?availableQuantity\D*(\d+)/g;
            var match;
            var newProducts = [];
            var seen = new Set();
            
            while ((match = pattern.exec(html)) !== null) {
                var productId = match[1];
                var qty = parseInt(match[2]) || 0;
                
                if (seen.has(productId)) continue;
                seen.add(productId);
                
                newProducts.push({
                    baseProductId: productId,
                    variant_id: productId,
                    inventory: qty,
                    in_stock: qty > 0,
                    timestamp: new Date().toISOString()
                });
            }
            
            if (config.debug && newProducts.length > 0) {
                log('Extracted', newProducts.length, 'products from page');
            }
            
            return newProducts;
        } catch (e) {
            console.error('[Zepto Extract Error]', e);
            return [];
        }
    }
    
    function addProducts(newProducts) {
        for (var i = 0; i < newProducts.length; i++) {
            var product = newProducts[i];
            var existing = null;
            
            for (var j = 0; j < window._zeptoProducts.length; j++) {
                if (window._zeptoProducts[j].variant_id === product.variant_id) {
                    existing = window._zeptoProducts[j];
                    break;
                }
            }
            
            if (existing) {
                var oldQty = existing.inventory;
                Object.assign(existing, product);
                
                if (oldQty !== product.inventory && config.debug) {
                    warn('[CHANGE]', product.variant_id, ':', oldQty, '→', product.inventory);
                }
            } else {
                window._zeptoProducts.push(product);
            }
            
            if (product.inventory <= config.lowStockThreshold && product.in_stock) {
                warn('[LOW STOCK]', product.variant_id, ':', product.inventory, 'left');
            }
        }
        
        window._zeptoProducts = window._zeptoProducts.slice(0, 100);
    }
    
    function refresh() {
        var products = extractFromHTML();
        addProducts(products);
        log('Total products:', window._zeptoProducts.length);
        return window._zeptoProducts;
    }
    
    function getProducts(filter) {
        if (!filter) return window._zeptoProducts;
        return window._zeptoProducts.filter(function(p) {
            for (var key in filter) {
                if (p[key] !== filter[key]) return false;
            }
            return true;
        });
    }
    
    function getLowStock(threshold) {
        return window._zeptoProducts.filter(function(p) {
            return p.in_stock && p.inventory <= threshold;
        });
    }
    
    function exportJSON() {
        return JSON.stringify(window._zeptoProducts, null, 2);
    }
    
    function clear() {
        window._zeptoProducts = [];
        log('Cleared');
    }
    
    window.zeptoInventory = {
        init: function() {
            return refresh();
        },
        refresh: refresh,
        getProducts: getProducts,
        getLowStock: getLowStock,
        exportJSON: exportJSON,
        clear: clear,
        products: window._zeptoProducts
    };
    
    log('Ready. Run: zeptoInventory.init() or zeptoInventory.refresh()');
})();