# Project Structure

## Directory Layout

```
blinkit_mcp/
├── agents/                 # Platform-specific ordering agents
│   ├── __init__.py        # Package initialization
│   ├── zepto.py           # Zepto ordering agent
│   ├── blinkit.py         # Blinkit ordering agent
│   ├── instamart.py       # Instamart ordering agent
│   └── zomato_simple.py   # Zomato ordering agent (optional)
│
├── utils/                  # Utility modules
│   ├── __init__.py        # Package initialization
│   └── conversation_ai.py # AI conversation handler using Gemini 2.0 Flash
│
├── tests/                  # Test and setup scripts
│   ├── __init__.py        # Package initialization
│   ├── setup_session.py   # Setup login sessions for platforms
│   ├── test_zepto.py      # Test Zepto agent
│   ├── test_blinkit.py    # Test Blinkit agent
│   ├── test_instamart.py  # Test Instamart agent
│   └── test_ai_conversation.py # Test AI conversation
│
├── data/                   # Data files (gitignored)
│   ├── __init__.py        # Package initialization
│   ├── zepto_state.json   # Zepto session state
│   ├── blinkit_state.json # Blinkit session state
│   ├── instamart_state.json # Instamart session state
│   └── blinkit_selectors.json # Blinkit CSS selectors
│
├── whatsapp_session/       # WhatsApp Web session data (gitignored)
│   └── [Chrome profile data]
│
├── whatsapp_bot.py         # Main WhatsApp bot application
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (gitignored)
├── .gitignore             # Git ignore rules
├── README.md              # Main documentation
└── STRUCTURE.md           # This file
```

## Key Files

### Main Application
- **whatsapp_bot.py**: Flask app that handles WhatsApp webhooks and orchestrates the ordering flow

### Agents
Each agent implements the same interface:
- `search_products(query, limit)`: Search for products
- `add_to_cart(product_urls)`: Add products to cart
- `view_cart()`: View cart contents
- `place_order()`: Complete checkout and place order

### Utils
- **conversation_ai.py**: Handles natural language understanding using Google's Gemini AI
  - Analyzes user intent (casual_chat, order_request, ingredient_suggestion, direct_command)
  - Maintains conversation context
  - Suggests ingredients for recipes

### Data Files
- **State files**: Store browser session cookies for persistent login
- **Selectors**: CSS selectors for web scraping (Blinkit)

## Flow

1. User sends WhatsApp message → Twilio webhook → Flask app
2. AI analyzes message intent and extracts information
3. Bot executes appropriate action (search, add to cart, checkout)
4. Results sent back to user via WhatsApp

## Environment Variables

Required in `.env`:
```
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
GOOGLE_API_KEY=your_gemini_key
```

## Dependencies

See `requirements.txt` for full list. Key dependencies:
- `playwright`: Browser automation
- `flask`: Web server for webhooks
- `twilio`: WhatsApp messaging
- `google-generativeai`: AI conversation
- `python-dotenv`: Environment variables
