# Multi-Platform Ordering Agents

Automated ordering system for Zepto, Blinkit, and Zomato using browser automation and MCP.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Set Up Sessions
```bash
python setup_session.py
```
This will open browsers for you to log in to Zepto and Blinkit. Sessions are saved for future use.

### 3. Test the Agents
```bash
# Test Zepto
python test_zepto.py

# Test Blinkit
python test_blinkit.py
```

## 📦 What's Included

### Platform Agents
- **zepto.py** - Zepto ordering agent (async)
- **blinkit.py** - Blinkit ordering agent (sync)
- **zomato.py** - Zomato restaurant search (MCP-based)

### WhatsApp Integration
- **whatsapp_bot.py** - Twilio-based WhatsApp bot (production-ready)

### Utilities
- **setup_session.py** - Session setup wizard
- **test_zepto.py** - Zepto agent tests
- **test_blinkit.py** - Blinkit agent tests

## 💻 Usage Examples

### Zepto Agent
```python
import asyncio
from zepto import ZeptoAgent

async def main():
    zepto = ZeptoAgent()
    
    # Search products
    products = await zepto.search_products("milk", limit=5)
    
    # Add to cart
    urls = [p['url'] for p in products[:2]]
    await zepto.add_to_cart(urls)
    
    # View cart
    cart = await zepto.view_cart()
    print(f"Cart total: ₹{cart['subtotal']}")
    
    # Check coupons
    await zepto.check_coupons(auto_apply=True)
    
    # Place order
    order = await zepto.place_order()
    print(f"Order ID: {order['order_id']}")

asyncio.run(main())
```

### Blinkit Agent
```python
from blinkit import BlinkitAgent

blinkit = BlinkitAgent()

# Search products
products = blinkit.search_products("bread", limit=5)

# Add to cart
urls = [p['url'] for p in products[:2]]
blinkit.add_to_cart(urls)

# View cart
cart = blinkit.view_cart()
print(f"Cart: {cart['total_items']} items, ₹{cart['subtotal']}")
```

### Zomato Agent
```python
import asyncio
from zomato import ZomatoAgent

async def main():
    zomato = ZomatoAgent()
    await zomato.initialize()
    
    # Search restaurants
    await zomato.search_restaurants("biryani", location="Bangalore")
    
    # Get order history
    await zomato.get_order_history()
    
    await zomato.close()

asyncio.run(main())
```

## 📱 WhatsApp Bot (Twilio)

For production WhatsApp integration, use the Twilio-based bot:

### Setup
1. Create Twilio account at https://www.twilio.com
2. Set up WhatsApp sandbox
3. Configure environment variables:
```bash
set TWILIO_ACCOUNT_SID=your_sid
set TWILIO_AUTH_TOKEN=your_token
```

4. Run the bot:
```bash
python whatsapp_bot.py
```

5. Expose with ngrok:
```bash
ngrok http 5000
```

6. Set webhook in Twilio console to: `https://your-ngrok-url/webhook`

### Usage
Send WhatsApp messages:
- `search for milk on zepto`
- `search for bread on blinkit`
- `add 1` (after search)
- `view cart`
- `checkout`

See `WHATSAPP_FINAL_SUMMARY.md` for detailed setup guide.

## 🔧 Features

### Zepto Agent
- ✅ Product search
- ✅ Add to cart
- ✅ View cart
- ✅ Check coupons (with auto-apply)
- ✅ Place order (COD/UPI)

### Blinkit Agent
- ✅ Product search
- ✅ Add to cart
- ✅ View cart
- 🚧 Update quantity (in progress)
- 🚧 Checkout (in progress)

### Zomato Agent
- ✅ Restaurant search
- ✅ Get menu
- ✅ Order history
- ✅ Natural language queries

## 📁 File Structure

```
blinkit_mcp/
├── zepto.py                    # Zepto agent
├── blinkit.py                  # Blinkit agent
├── zomato.py                   # Zomato agent
├── whatsapp_bot.py             # Twilio WhatsApp bot
├── setup_session.py            # Session setup
├── test_zepto.py               # Zepto tests
├── test_blinkit.py             # Blinkit tests
├── requirements.txt            # Dependencies
├── zepto_state.json            # Zepto session
├── blinkit_state.json          # Blinkit session
├── README.md                   # This file
└── WHATSAPP_FINAL_SUMMARY.md   # WhatsApp integration guide
```

## 🔐 Session Management

Sessions are stored in JSON files:
- `zepto_state.json` - Zepto login session
- `blinkit_state.json` - Blinkit login session

If sessions expire, run `python setup_session.py` again.

## 🎯 Common Use Cases

### Automated Grocery Shopping
```python
import asyncio
from zepto import ZeptoAgent

async def weekly_groceries():
    zepto = ZeptoAgent()
    items = ["milk", "bread", "eggs", "butter"]
    
    for item in items:
        products = await zepto.search_products(item, limit=1)
        if products:
            await zepto.add_to_cart(products[0]['url'])
    
    await zepto.check_coupons(auto_apply=True)
    order = await zepto.place_order()
    return order

asyncio.run(weekly_groceries())
```

### Price Comparison
```python
import asyncio
from zepto import ZeptoAgent
from blinkit import BlinkitAgent

async def compare_prices(item):
    zepto = ZeptoAgent()
    blinkit = BlinkitAgent()
    
    zepto_products = await zepto.search_products(item, limit=1)
    blinkit_products = blinkit.search_products(item, limit=1)
    
    print(f"Zepto: ₹{zepto_products[0]['price']}")
    print(f"Blinkit: ₹{blinkit_products[0]['price']}")

asyncio.run(compare_prices("milk"))
```

## 🐛 Troubleshooting

### "FileNotFoundError: zepto_state.json"
Run `python setup_session.py` to create session files.

### "Session expired"
Delete `*_state.json` files and run `python setup_session.py` again.

### Products not found
Platform UI may have changed. Check if selectors need updating.

## 📚 Documentation

- **README.md** - This file (quick start and usage)
- **WHATSAPP_FINAL_SUMMARY.md** - Complete WhatsApp integration guide
- **requirements.txt** - Python dependencies

## 🚀 Future Platforms

Planned support for:
- Swiggy
- Instamart
- Bistro
- Amazon
- Flipkart
- Myntra

## 📄 License

MIT

## 🙏 Acknowledgments

Built with:
- Playwright (browser automation)
- Selenium (WhatsApp Web)
- Twilio (WhatsApp Business API)
- LangChain (Zomato MCP)
