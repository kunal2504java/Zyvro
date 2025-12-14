"""
Conversational AI layer using Gemini 2.5 Flash

Handles natural language conversations in English and Hinglish,
understands user intent, and suggests shopping lists intelligently.
"""

import os
import json
from typing import Dict, List, Optional
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


class ConversationAI:
    """AI-powered conversation handler for the ordering bot"""
    
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        self.conversation_history = {}
        
    def get_user_context(self, user_id: str) -> Dict:
        """Get or create conversation context for a user"""
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = {
                "messages": [],
                "suggested_items": [],
                "current_intent": None,
                "platform": None
            }
        return self.conversation_history[user_id]
    
    def analyze_message(self, user_id: str, message: str) -> Dict:
        """
        Analyze user message and determine intent
        
        Returns:
            {
                "intent": "casual_chat" | "order_request" | "ingredient_suggestion" | "direct_command",
                "response": "AI generated response",
                "suggested_items": ["item1", "item2"],
                "platform": "zepto" | "blinkit" | "instamart" | None,
                "action": "search" | "add_to_cart" | "checkout" | "suggest" | None
            }
        """
        context = self.get_user_context(user_id)
        
        # Build conversation history for context
        history_text = "\n".join([
            f"User: {msg['user']}\nBot: {msg['bot']}" 
            for msg in context["messages"][-3:]  # Last 3 exchanges
        ])
        
        prompt = f"""You are a friendly shopping assistant for Indian grocery delivery apps (Zepto, Blinkit, Instamart).
You understand both English and Hinglish (Hindi written in English).

Previous conversation:
{history_text if history_text else "No previous conversation"}

Current user message: "{message}"

Analyze this message and respond in JSON format:
{{
    "intent": "casual_chat" | "order_request" | "ingredient_suggestion" | "direct_command",
    "response": "Your friendly response in the same language style as user (English/Hinglish)",
    "suggested_items": ["list of items if user wants to make something"],
    "platform": "zepto" | "blinkit" | "instamart" | null,
    "action": "search" | "add_to_cart" | "checkout" | "suggest" | null,
    "query": "search query if action is search"
}}

Intent types:
- casual_chat: User is expressing a desire/craving but NOT explicitly asking to order (e.g., "Biryani khane ka mann hai", "Aaj chai peene ka mann ho raha hai")
- order_request: User EXPLICITLY wants to order/search for specific items NOW (e.g., "Order biryani", "I want to buy milk", "Search for chocolate")
- ingredient_suggestion: User wants to MAKE/COOK something and needs ingredients (e.g., "Mujhe pasta banana hai", "I want to make biryani")
- direct_command: Direct bot commands (search, add, checkout, view cart)

IMPORTANT RULES:
1. If user just expresses a craving/desire WITHOUT explicitly asking to order, use "casual_chat" - have a conversation first!
2. Only use "order_request" with action "search" if user EXPLICITLY says to order/search/buy
3. For "casual_chat", respond warmly and ask if they want to order or make it themselves
4. For "ingredient_suggestion", ALWAYS populate the "suggested_items" array with individual ingredient names (e.g., ["Chicken", "Dahi", "Ginger-Garlic Paste", "Tikka Masala"])
5. Keep ingredient names simple and searchable (e.g., "Chicken" not "Chicken pieces", "Dahi" not "Fresh dahi")

Examples:
1. "Biryani khane ka mann hai" → casual_chat (just expressing desire, not ordering yet)
2. "Order biryani from Zepto" → order_request, action: search, query: "biryani"
3. "Search for milk on Zepto" → direct_command, action: search, query: "milk"
4. "Mujhe pasta banana hai" → ingredient_suggestion, suggested_items: ["Pasta", "Tomato", "Garlic", "Olive Oil", "Cheese"]
5. "Chicken tikka banana hai" → ingredient_suggestion, suggested_items: ["Chicken", "Dahi", "Ginger-Garlic Paste", "Tikka Masala", "Lemon"]
6. "Add 1" → direct_command, action: add_to_cart
7. "View cart" → direct_command, action: view_cart
8. "Checkout" → direct_command, action: checkout
9. "Aaj chai peene ka mann hai" → casual_chat (expressing craving, not ordering)
10. "I want to buy chocolate" → order_request, action: search, query: "chocolate"
11. "Yes" (after ingredient suggestion) → order_request, action: search (will search for suggested items)
12. "Order on Zepto" (after ingredient suggestion) → direct_command, action: search, platform: zepto (will search for suggested items)

Be warm, friendly, and conversational. Use emojis appropriately. Match the user's language style.
NEVER jump straight to searching unless user explicitly asks to order/search/buy!
"""
        
        try:
            response = self.model.generate_content(prompt)
            result = json.loads(response.text.strip().replace('```json', '').replace('```', ''))
            
            # Store in conversation history
            context["messages"].append({
                "user": message,
                "bot": result.get("response", "")
            })
            
            if result.get("suggested_items"):
                context["suggested_items"] = result["suggested_items"]
            
            if result.get("platform"):
                context["platform"] = result["platform"]
            
            context["current_intent"] = result.get("intent")
            
            return result
            
        except Exception as e:
            print(f"Error in AI analysis: {e}")
            # Fallback to simple response
            return {
                "intent": "direct_command",
                "response": "I'm here to help you order groceries! What would you like?",
                "suggested_items": [],
                "platform": None,
                "action": None
            }
    
    def format_ingredient_list(self, items: List[str], context: str = "") -> str:
        """Format ingredient list in a friendly way"""
        if not items:
            return ""
        
        response = f"\n\n📝 Ingredients for {context}:\n"
        for i, item in enumerate(items, 1):
            response += f"{i}. {item}\n"
        
        response += "\nReply with:\n"
        response += "• 'Yes' to search for these items\n"
        response += "• 'Edit' to modify the list\n"
        response += "• Or tell me what to add/remove"
        
        return response
    
    def clear_context(self, user_id: str):
        """Clear conversation context for a user"""
        if user_id in self.conversation_history:
            del self.conversation_history[user_id]


# Example usage
if __name__ == "__main__":
    ai = ConversationAI()
    
    # Test messages
    test_messages = [
        "Aaj chai peene ka mann ho raha hai",
        "Haan, order karna hai",
        "Search for milk on Zepto"
    ]
    
    for msg in test_messages:
        print(f"\nUser: {msg}")
        result = ai.analyze_message("test_user", msg)
        print(f"Intent: {result['intent']}")
        print(f"Response: {result['response']}")
        if result.get('suggested_items'):
            print(f"Suggested: {result['suggested_items']}")
