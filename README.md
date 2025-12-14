# Multi-Platform Grocery Ordering Bot

WhatsApp bot for ordering from Zepto, Blinkit, Instamart, and BigBasket through natural language conversations in English and Hinglish.

## 📁 Project Structure

```
blinkit_mcp/
├── agents/              # Platform-specific ordering agents
│   ├── zepto.py        # Zepto agent
│   ├── blinkit.py      # Blinkit agent
│   ├── instamart.py    # Instamart agent
│   ├── bigbasket.py    # BigBasket agent
│   └── zomato_simple.py # Zomato agent (optional)
├── utils/              # Utility modules
│   └── conversation_ai.py # AI conversation handler (Gemini)
├── tests/              # Test scripts
│   ├── test_*.py       # Various test files
│   └── setup_*.py      # Setup scripts
├── data/               # Data files (state, selectors)
│   ├── *_state.json    # Session state files
│   └── blinkit_selectors.json
├── whatsapp_session/   # WhatsApp session data
├── whatsapp_bot.py     # Main WhatsApp bot
├── requirements.txt    # Python dependencies
├── .env               # Environment variables
└── README.md          # This file
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Set Up Environment Variables
Create a `.env` file in the root directory:
```env
# Twilio (for WhatsApp)
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

# Google AI (for conversation)
GOOGLE_API_KEY=your_gemini_api_key
```

### 3. Set Up Sessions
```bash
cd blinkit_mcp
python tests/setup_session.py
```
This will open browsers for you to log in to Zepto and Blinkit. Sessions are saved for future use.

### 4. Run the WhatsApp Bot
```bash
python whatsapp_bot.py
```

### 5. Expose to Internet (for WhatsApp webhook)
```bash
ngrok http 5000
```
Then set the webhook URL in Twilio console to: `https://your-ngrok-url/webhook`

## 💬 Usage

The bot understands natural English and Hinglish conversations:

**Casual Chat:**
- "Biryani khane ka mann hai" → Bot asks if you want to order or make it
- "Chicken tikka banana hai" → Bot suggests ingredients

**Ordering:**
- "Order biryani from Zepto" → Searches for biryani
- "Yes" (after ingredient suggestion) → Searches for all ingredients
- "Add all" → Adds all items to cart
- "Checkout" → Places the order

**Commands:**
- "View cart" → Shows cart contents
- "Coupons" → Shows available coupons (Zepto only)

## 🧪 Testing

Run individual platform tests:
```bash
cd blinkit_mcp
python tests/test_zepto.py
python tests/test_blinkit.py
python tests/test_instamart.py
```

Test AI conversation:
```bash
python tests/test_ai_conversation.py
```

## 🛠️ Features

- **Multi-Platform Support**: Zepto, Blinkit, Instamart, BigBasket
- **Natural Language**: Understands English and Hinglish
- **AI-Powered**: Uses Gemini 2.0 Flash for conversation
- **Ingredient Suggestions**: Suggests ingredients for recipes
- **WhatsApp Integration**: Order through WhatsApp messages
- **Session Management**: Saves login sessions for reuse
- **Cart Management**: Add, view, and checkout items
- **Coupon Support**: Auto-applies best coupons (Zepto)

## 📝 Notes

- The bot sends multiple messages for ingredient searches to avoid WhatsApp's 1600 character limit
- Sessions are stored in `data/` folder
- WhatsApp session data is stored in `whatsapp_session/` folder
- All state files are gitignored for privacy

## 🔧 Development

To add a new platform agent:
1. Create a new file in `agents/` folder
2. Implement the required methods: `search_products`, `add_to_cart`, `view_cart`, `place_order`
3. Import it in `whatsapp_bot.py`
4. Add tests in `tests/` folder

## 📄 License

MIT
