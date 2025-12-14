"""
Test script for AI conversation features

Tests the enhanced chatting capabilities with Gemini AI.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check if API key is set
if not os.getenv("GOOGLE_API_KEY"):
    print("❌ GOOGLE_API_KEY not found in .env file")
    print("   Please add your Gemini API key to .env file")
    sys.exit(1)

try:
    from conversation_ai import ConversationAI
except ImportError as e:
    print(f"❌ Error importing ConversationAI: {e}")
    print("   Install with: pip install google-generativeai==0.8.3")
    sys.exit(1)


def test_ai_conversations():
    """Test various conversation scenarios"""
    
    print("🤖 Testing AI Conversation Features")
    print("="*60)
    
    ai = ConversationAI()
    user_id = "test_user"
    
    # Test scenarios
    test_messages = [
        "Aaj chai peene ka mann ho raha hai",
        "Haan, order karna hai",
        "Mujhe pasta banana hai",
        "I want to make biryani",
        "Search for milk on Zepto",
        "Add 1",
        "Checkout karna hai"
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n{i}. User: {message}")
        
        try:
            result = ai.analyze_message(user_id, message)
            
            print(f"   Intent: {result['intent']}")
            print(f"   Response: {result['response'][:100]}...")
            
            if result.get('suggested_items'):
                print(f"   Suggested Items: {', '.join(result['suggested_items'][:3])}...")
            
            if result.get('platform'):
                print(f"   Platform: {result['platform']}")
            
            if result.get('action'):
                print(f"   Action: {result['action']}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "="*60)
    print("✅ AI Conversation Test Complete!")
    print("\nNext steps:")
    print("  1. Start bot: python whatsapp_bot.py")
    print("  2. Expose with ngrok: ngrok http 5000")
    print("  3. Set Twilio webhook to: https://your-ngrok-url/webhook")


if __name__ == "__main__":
    test_ai_conversations()
