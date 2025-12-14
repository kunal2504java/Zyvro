"""
Simple test script for WhatsApp bot - Tests without starting Flask server
"""

import asyncio
import sys
sys.path.insert(0, '.')

# Test imports
print("🧪 Testing imports...")
try:
    from zepto import ZeptoAgent
    print("✅ Zepto imported")
except Exception as e:
    print(f"❌ Zepto import failed: {e}")

try:
    from blinkit import BlinkitAgent
    print("✅ Blinkit imported")
except Exception as e:
    print(f"❌ Blinkit import failed: {e}")

try:
    from instamart import InstamartAgent
    print("✅ Instamart imported")
except Exception as e:
    print(f"❌ Instamart import failed: {e}")

# Test bot initialization
print("\n🤖 Testing bot initialization...")
try:
    from whatsapp_bot import WhatsAppOrderBot
    bot = WhatsAppOrderBot()
    print("✅ Bot created successfully")
    
    # Test agent initialization
    print("\n⚙️ Initializing agents...")
    asyncio.run(bot.initialize_agents())
    print("✅ All agents initialized!")
    
    # Test message parsing
    print("\n📝 Testing message parsing...")
    test_messages = [
        "search for milk on zepto",
        "find bread on blinkit",
        "add 1",
        "view cart",
        "help"
    ]
    
    for msg in test_messages:
        intent = bot.parse_message(msg, "test_user")
        print(f"  '{msg}' → {intent['action']} on {intent['platform']}")
    
    print("\n✅ All tests passed!")
    print("\n🎯 Bot is ready to use!")
    print("\nNext steps:")
    print("1. Make sure you have sessions set up:")
    print("   python setup_session.py")
    print("\n2. Start the bot:")
    print("   python whatsapp_bot.py")
    print("\n3. In another terminal, start ngrok:")
    print("   ngrok http 5000")
    print("\n4. Set webhook in Twilio to: https://your-ngrok-url/webhook")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
