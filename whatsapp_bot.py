"""
WhatsApp Bot for Multi-Platform Ordering

This bot integrates with WhatsApp to allow users to order from Zepto, Blinkit, and Zomato
through natural language messages.

Setup:
1. Install required packages:
   pip install flask twilio

2. Set up Twilio account and get credentials:
   - Sign up at https://www.twilio.com
   - Get your Account SID and Auth Token
   - Set up WhatsApp sandbox or get approved number

3. Set environment variables:
   export TWILIO_ACCOUNT_SID="your_account_sid"
   export TWILIO_AUTH_TOKEN="your_auth_token"
   export TWILIO_WHATSAPP_NUMBER="whatsapp:+14155238886"  # Twilio sandbox number

4. Run the bot:
   python whatsapp_bot.py

5. Expose to internet using ngrok:
   ngrok http 5000
   
6. Set webhook URL in Twilio console to: https://your-ngrok-url/webhook
"""

import os
import re
import asyncio
import threading
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize Twilio client for sending messages
twilio_client = Client(
    os.getenv('TWILIO_ACCOUNT_SID'),
    os.getenv('TWILIO_AUTH_TOKEN')
)
TWILIO_WHATSAPP_NUMBER = os.getenv('TWILIO_WHATSAPP_NUMBER')

# Import agents
from agents.zepto import ZeptoAgent
from agents.blinkit import BlinkitAgent
from agents.instamart import InstamartAgent
from agents.bigbasket import BigBasketAgent

# Zomato is optional
try:
    from agents.zomato_simple import ZomatoSimpleAgent
except Exception as e:
    print(f"⚠️ Zomato agent not available: {str(e)}")
    print("   Install with: pip install langchain-mcp-adapters langgraph langchain-google-genai langchain-core")


app = Flask(__name__)

# Store user conversation context
user_context = {}


class WhatsAppOrderBot:
    """WhatsApp bot for multi-platform ordering with AI conversation"""
    
    def __init__(self):
        self.zepto = None
        self.blinkit = None
        self.instamart = None
        self.bigbasket = None
        self.ai = None
        
    async def initialize_agents(self):
        """Initialize all platform agents and AI"""
        print("🤖 Initializing Zepto agent...")
        self.zepto = ZeptoAgent()
        print("✅ Zepto agent ready")
        
        print("🤖 Initializing Blinkit agent...")
        self.blinkit = BlinkitAgent()
        print("✅ Blinkit agent ready")
        
        print("🤖 Initializing Instamart agent...")
        self.instamart = InstamartAgent()
        print("✅ Instamart agent ready")
        
        print("🤖 Initializing BigBasket agent...")
        self.bigbasket = BigBasketAgent()
        print("✅ BigBasket agent ready")
        
        print("🤖 Initializing Conversation AI...")
        try:
            from utils.conversation_ai import ConversationAI
            self.ai = ConversationAI()
            print("✅ AI ready")
        except Exception as e:
            print(f"⚠️ AI not available: {e}")
            self.ai = None
    
    def parse_message(self, message: str, user_id: str):
        """
        Parse user message to extract intent, platform, and parameters
        
        Returns:
            dict with: platform, action, query, items
        """
        message = message.lower().strip()
        
        # Get or create user context
        if user_id not in user_context:
            user_context[user_id] = {
                "platform": None,
                "last_search": [],
                "cart_items": [],
                "suggested_items": [],
                "shopping_queue": [],
                "current_ingredient_index": 0
            }
        
        context = user_context[user_id]
        
        # Detect platform
        platform = None
        if any(word in message for word in ["zepto", "zpto"]):
            platform = "zepto"
        elif any(word in message for word in ["blinkit", "blink"]):
            platform = "blinkit"
        elif any(word in message for word in ["instamart", "swiggy", "insta"]):
            platform = "instamart"
        elif any(word in message for word in ["bigbasket", "big basket", "bb"]):
            platform = "bigbasket"
        elif context["platform"]:
            # Use last platform if not specified
            platform = context["platform"]
        
        # Detect action
        action = None
        query = None
        
        # View cart patterns (check FIRST before other patterns)
        if any(phrase in message for phrase in ["view cart", "show cart", "my cart", "see cart", "check cart"]):
            action = "view_cart"
        
        # Search patterns
        elif any(word in message for word in ["search", "find", "show", "look for"]):
            action = "search"
            # Extract search query
            for keyword in ["search for", "find", "show me", "look for"]:
                if keyword in message:
                    query = message.split(keyword)[-1].strip()
                    # Remove platform name from query
                    for platform_name in ["on zepto", "on blinkit", "on zomato", "zepto", "blinkit", "zomato"]:
                        query = query.replace(platform_name, "").strip()
                    break
            if not query:
                # Just extract the product name
                query = re.sub(r'\b(search|find|show|look)\b', '', message).strip()
                for platform_name in ["zepto", "blinkit", "zomato"]:
                    query = query.replace(platform_name, "").strip()
        
        # Add to cart patterns (check BEFORE checkout patterns)
        elif any(word in message for word in ["add", "buy"]) or re.match(r'^(order|yes|haan)\s+\d+', message):
            action = "add_to_cart"
            # Check if user is referencing search results
            if any(word in message for word in ["first", "1st", "top", "all"]) or re.search(r'\d+', message):
                query = message
            else:
                # Extract item name
                query = re.sub(r'\b(add|buy|to|the)\b', '', message).strip()
        
        # Checkout patterns (more specific to avoid matching "order 1")
        elif any(phrase in message for phrase in ["checkout", "place order", "buy now", "complete order"]) or (message == "order" or message.startswith("order now")):
            action = "checkout"
        
        # Coupon patterns
        elif any(word in message for word in ["coupon", "discount", "offer"]):
            action = "coupons"
        
        # Help patterns
        elif any(word in message for word in ["help", "how", "what can"]):
            action = "help"
        
        # Update context
        if platform:
            context["platform"] = platform
        
        return {
            "platform": platform,
            "action": action,
            "query": query,
            "raw_message": message
        }
    
    async def handle_search(self, platform: str, query: str, user_id: str):
        """Handle product search"""
        print(f"🔍 handle_search called: platform={platform}, query={query}, user_id={user_id}")
        
        # Ensure user context exists
        if user_id not in user_context:
            user_context[user_id] = {
                "platform": None,
                "last_search": [],
                "cart_items": [],
                "suggested_items": [],
                "shopping_queue": [],
                "current_ingredient_index": 0
            }
        
        if not query:
            return "Please specify what you want to search for.\nExample: 'Search for milk on Zepto'"
        
        try:
            if platform == "zepto":
                print(f"🔍 Calling zepto.search_products with query: {query}")
                products = await self.zepto.search_products(query, limit=5)
            elif platform == "blinkit":
                # Run sync Blinkit method in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                products = await loop.run_in_executor(None, lambda: self.blinkit.search_products(query, limit=5))
            elif platform == "instamart":
                # Run sync Instamart method in thread pool
                loop = asyncio.get_event_loop()
                products = await loop.run_in_executor(None, lambda: self.instamart.search_products(query, limit=5))
            elif platform == "bigbasket":
                # Run sync BigBasket method in thread pool
                loop = asyncio.get_event_loop()
                products = await loop.run_in_executor(None, lambda: self.bigbasket.search_products(query, limit=5))
            else:
                return "Please specify a platform: Zepto, Blinkit, Instamart, or BigBasket"
            
            if not products:
                return f"No products found for '{query}' on {platform.title()}"
            
            # Store search results in context
            user_context[user_id]["last_search"] = products
            
            # Format response
            response = f"🔍 Found {len(products)} products on {platform.title()}:\n\n"
            for i, p in enumerate(products, 1):
                price = f"₹{p['price']}" if p['price'] else "N/A"
                savings = f" (save ₹{p['savings']})" if p.get('savings') else ""
                response += f"{i}. {p['name']}\n"
                response += f"   {p.get('pack_size', p.get('weight', ''))} - {price}{savings}\n\n"
            
            response += "Reply with:\n"
            response += "• 'Add 1' to add first item\n"
            response += "• 'Add all' to add all items\n"
            response += "• 'Add 1,3,5' to add specific items"
            
            return response
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"❌ Error in handle_search: {error_details}")
            return f"Error searching on {platform}: {str(e)}"
    
    async def handle_add_to_cart(self, platform: str, query: str, user_id: str):
        """Handle adding items to cart"""
        # Ensure user context exists
        if user_id not in user_context:
            user_context[user_id] = {
                "platform": None,
                "last_search": [],
                "cart_items": [],
                "suggested_items": [],
                "shopping_queue": [],
                "current_ingredient_index": 0
            }
        
        context = user_context.get(user_id, {})
        last_search = context.get("last_search", [])
        
        if not last_search:
            return "Please search for products first.\nExample: 'Search for milk on Zepto'"
        
        try:
            # Parse which items to add
            indices = []
            
            # Handle None or empty query
            if not query:
                query = ""
            
            if "all" in query.lower():
                indices = list(range(len(last_search)))
            elif any(char.isdigit() for char in query):
                # Extract numbers
                numbers = re.findall(r'\d+', query)
                indices = [int(n) - 1 for n in numbers if 0 < int(n) <= len(last_search)]
            else:
                # Default to first item
                indices = [0]
            
            if not indices:
                return "Please specify which items to add.\nExample: 'Add 1' or 'Add 1,2,3'"
            
            # Get product URLs
            product_urls = [last_search[i]['url'] for i in indices if i < len(last_search)]
            
            if not product_urls:
                return "Invalid item numbers. Please try again."
            
            # Add to cart
            if platform == "zepto":
                result = await self.zepto.add_to_cart(product_urls)
            elif platform == "blinkit":
                # Run sync Blinkit method in thread pool
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, lambda: self.blinkit.add_to_cart(product_urls))
            elif platform == "instamart":
                # Run sync Instamart method in thread pool
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, lambda: self.instamart.add_to_cart(product_urls))
            elif platform == "bigbasket":
                # Run sync BigBasket method in thread pool
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, lambda: self.bigbasket.add_to_cart(product_urls))
            else:
                return f"Add to cart not supported for {platform}"
            
            if result['success']:
                response = f"✅ Added {result['successful']}/{result['total_products']} items to cart!\n\n"
                response += "What's next?\n"
                response += "• 'View cart' to see your cart\n"
                response += "• 'Checkout' to place order\n"
                response += "• Search for more items"
                return response
            else:
                return f"Failed to add items to cart. Please try again."
                
        except Exception as e:
            return f"Error adding to cart: {str(e)}"
    
    async def handle_view_cart(self, platform: str, user_id: str):
        """Handle viewing cart"""
        # Ensure user context exists
        if user_id not in user_context:
            user_context[user_id] = {
                "platform": None,
                "last_search": [],
                "cart_items": [],
                "suggested_items": [],
                "shopping_queue": [],
                "current_ingredient_index": 0
            }
        
        try:
            if platform == "zepto":
                cart = await self.zepto.view_cart()
            elif platform == "blinkit":
                # Run sync Blinkit method in thread pool
                loop = asyncio.get_event_loop()
                cart = await loop.run_in_executor(None, self.blinkit.view_cart)
            elif platform == "instamart":
                # Run sync Instamart method in thread pool
                loop = asyncio.get_event_loop()
                cart = await loop.run_in_executor(None, self.instamart.view_cart)
            elif platform == "bigbasket":
                # Run sync BigBasket method in thread pool
                loop = asyncio.get_event_loop()
                cart = await loop.run_in_executor(None, self.bigbasket.view_cart)
            else:
                return f"View cart not supported for {platform}"
            
            if cart['cart_empty']:
                return "🛒 Your cart is empty.\n\nSearch for products to get started!"
            
            response = f"🛒 Your {platform.title()} Cart:\n\n"
            for item in cart['cart_items']:
                response += f"• {item['name']}\n"
                response += f"  {item.get('pack_size', item.get('weight', ''))} x{item['quantity']} = ₹{item['total_price']}\n\n"
            
            response += f"Total Items: {cart['total_items']}\n"
            response += f"Subtotal: ₹{cart['subtotal']}\n\n"
            response += "Reply with:\n"
            response += "• 'Checkout' to place order\n"
            response += "• 'Coupons' to check offers"
            
            return response
            
        except Exception as e:
            return f"Error viewing cart: {str(e)}"
    
    async def handle_coupons(self, platform: str, user_id: str):
        """Handle checking coupons"""
        try:
            if platform == "zepto":
                coupons = await self.zepto.check_coupons(auto_apply=True)
            else:
                return f"Coupons not yet supported for {platform}"
            
            if not coupons:
                return "No coupons available right now."
            
            response = f"🎟️ Available Coupons on {platform.title()}:\n\n"
            for coupon in coupons:
                status = "✅ APPLIED" if coupon['is_applicable_now'] else "🔒 LOCKED"
                response += f"{status} {coupon['coupon_code']}\n"
                response += f"{coupon['coupon_title']}\n"
                if coupon['amount_needed_to_unlock']:
                    response += f"Add ₹{coupon['amount_needed_to_unlock']} more to unlock\n"
                response += "\n"
            
            return response
            
        except Exception as e:
            return f"Error checking coupons: {str(e)}"
    
    async def handle_checkout(self, platform: str, user_id: str):
        """Handle order placement"""
        try:
            if platform == "zepto":
                result = await self.zepto.place_order()
            elif platform == "blinkit":
                # Run sync Blinkit method in thread pool
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, self.blinkit.place_order)
            elif platform == "instamart":
                # Run sync Instamart method in thread pool
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, self.instamart.place_order)
            elif platform == "bigbasket":
                # Run sync BigBasket method in thread pool
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, self.bigbasket.place_order)
            else:
                return f"Checkout not yet supported for {platform}"
            
            if result['final_status'] == 'completed':
                response = "🎉 Order Placed Successfully!\n\n"
                if result.get('order_id'):
                    response += f"Order ID: {result['order_id']}\n"
                if result.get('eta'):
                    response += f"ETA: {result['eta']}\n"
                elif result.get('delivery_time'):
                    response += f"Delivery Time: {result['delivery_time']}\n"
                response += f"Payment: {result['payment_method']}"
                return response
            else:
                return f"Checkout failed: {result.get('error', 'Unknown error')}"
                
        except Exception as e:
            return f"Error during checkout: {str(e)}"
    
    async def handle_shopping_queue(self, user_id: str, message: str):
        """Handle interactive shopping queue flow"""
        from_number = f"whatsapp:{user_id}"
        context = user_context[user_id]
        message_lower = message.lower().strip()
        
        # Check if user wants to stop
        if any(word in message_lower for word in ['stop', 'cancel', 'quit']):
            context['shopping_queue'] = []
            send_whatsapp_message(from_number, "🛑 Shopping stopped. Your cart is saved!\n\nReply 'View cart' to see what you have.")
            return "__MESSAGES_SENT__"
        
        # Check if user wants to skip
        if any(word in message_lower for word in ['skip', 'next', 'nahi']):
            # Move to next ingredient
            context['current_ingredient_index'] += 1
            
            if context['current_ingredient_index'] >= len(context['shopping_queue']):
                # Done with all ingredients
                context['shopping_queue'] = []
                send_whatsapp_message(from_number, "✅ Done shopping!\n\nReply with:\n• 'View cart' to see your items\n• 'Checkout' to place order")
                return "__MESSAGES_SENT__"
            
            # Show next ingredient
            next_item = context['shopping_queue'][context['current_ingredient_index']]
            platform = context.get('platform', 'zepto')
            search_result = await self.handle_search(platform, next_item, user_id)
            
            message = f"🛒 Next ingredient ({context['current_ingredient_index']+1}/{len(context['shopping_queue'])})\n\n"
            message += f"🔍 {next_item}:\n\n{search_result}\n\n"
            message += "Reply with:\n"
            message += "• 'Add 1' (or any number) to add that item\n"
            message += "• 'Skip' to skip this ingredient\n"
            message += "• 'Stop' to stop shopping"
            
            send_whatsapp_message(from_number, message)
            return "__MESSAGES_SENT__"
        
        # Check if user wants to add item
        if any(word in message_lower for word in ['add', 'yes', 'haan']):
            # Add the item
            platform = context.get('platform', 'zepto')
            add_result = await self.handle_add_to_cart(platform, message, user_id)
            send_whatsapp_message(from_number, add_result)
            
            # Move to next ingredient
            context['current_ingredient_index'] += 1
            
            if context['current_ingredient_index'] >= len(context['shopping_queue']):
                # Done with all ingredients
                context['shopping_queue'] = []
                send_whatsapp_message(from_number, "✅ Done shopping!\n\nReply with:\n• 'View cart' to see your items\n• 'Checkout' to place order")
                return "__MESSAGES_SENT__"
            
            # Show next ingredient
            next_item = context['shopping_queue'][context['current_ingredient_index']]
            search_result = await self.handle_search(platform, next_item, user_id)
            
            message = f"🛒 Next ingredient ({context['current_ingredient_index']+1}/{len(context['shopping_queue'])})\n\n"
            message += f"🔍 {next_item}:\n\n{search_result}\n\n"
            message += "Reply with:\n"
            message += "• 'Add 1' (or any number) to add that item\n"
            message += "• 'Skip' to skip this ingredient\n"
            message += "• 'Stop' to stop shopping"
            
            send_whatsapp_message(from_number, message)
            return "__MESSAGES_SENT__"
        
        # User said something else, ask for clarification
        send_whatsapp_message(from_number, "Please reply with:\n• 'Add 1' to add item\n• 'Skip' to skip\n• 'Stop' to stop shopping")
        return "__MESSAGES_SENT__"
    
    async def handle_ai_conversation(self, user_id: str, message: str):
        """Handle natural conversation with AI"""
        if not self.ai:
            return None
        
        # Ensure user context exists
        if user_id not in user_context:
            user_context[user_id] = {
                "platform": None,
                "last_search": [],
                "cart_items": [],
                "suggested_items": [],
                "shopping_queue": [],
                "current_ingredient_index": 0
            }
        
        # Check if user is in shopping queue flow
        if user_context[user_id].get('shopping_queue'):
            return await self.handle_shopping_queue(user_id, message)
        
        try:
            # Analyze message with AI
            print(f"🤖 AI analyzing message from user_id={user_id}: {message}")
            analysis = self.ai.analyze_message(user_id, message)
            print(f"🤖 AI analysis result: {analysis}")
            
            # Handle based on intent
            if analysis['intent'] == 'casual_chat':
                # User is just chatting, respond naturally and DON'T search
                return analysis['response']
            
            elif analysis['intent'] == 'ingredient_suggestion':
                # User wants to make something, suggest ingredients
                response = analysis['response']
                
                if analysis.get('suggested_items'):
                    response += "\n\n📝 Suggested ingredients:\n"
                    for i, item in enumerate(analysis['suggested_items'], 1):
                        response += f"{i}. {item}\n"
                    
                    response += "\n💡 Reply with:\n"
                    response += "• 'Yes' or 'Haan' to search for these items\n"
                    response += "• 'Order on Zepto/Blinkit' to choose platform"
                    
                    # Store suggested items in context
                    user_context[user_id]['suggested_items'] = analysis['suggested_items']
                
                return response
            
            elif analysis['intent'] == 'order_request':
                # User EXPLICITLY wants to order
                platform = analysis.get('platform') or user_context[user_id].get('platform') or 'zepto'
                
                # Check if user is confirming ingredient suggestions
                if user_context[user_id].get('suggested_items'):
                    # Get user's WhatsApp number for sending incremental messages
                    from_number = f"whatsapp:{user_id}"
                    
                    # Start interactive ingredient shopping flow
                    # Store the items in a shopping queue
                    user_context[user_id]['shopping_queue'] = user_context[user_id]['suggested_items'].copy()
                    user_context[user_id]['current_ingredient_index'] = 0
                    user_context[user_id]['platform'] = platform
                    
                    # Clear suggested items
                    user_context[user_id]['suggested_items'] = []
                    
                    # Search and show first ingredient
                    first_item = user_context[user_id]['shopping_queue'][0]
                    search_result = await self.handle_search(platform, first_item, user_id)
                    
                    message = f"🛒 Let's shop for ingredients! (1/{len(user_context[user_id]['shopping_queue'])})\n\n"
                    message += f"🔍 {first_item}:\n\n{search_result}\n\n"
                    message += "Reply with:\n"
                    message += "• 'Add 1' (or any number) to add that item\n"
                    message += "• 'Skip' to skip this ingredient\n"
                    message += "• 'Stop' to stop shopping"
                    
                    send_whatsapp_message(from_number, message)
                    
                    # Return special marker to indicate messages were sent
                    return "__MESSAGES_SENT__"
                
                # Regular order request with search query
                elif analysis.get('action') == 'search' and analysis.get('query'):
                    print(f"🤖 AI calling handle_search: platform={platform}, query={analysis['query']}, user_id={user_id}")
                    return await self.handle_search(platform, analysis['query'], user_id)
                else:
                    return analysis['response']
            
            elif analysis['intent'] == 'direct_command':
                # Direct command - execute the action
                platform = analysis.get('platform') or user_context[user_id].get('platform') or 'zepto'
                
                if analysis.get('action') == 'search':
                    # User wants to search for items
                    query = analysis.get('query')
                    
                    # Check if user is confirming ingredient suggestions (prioritize this!)
                    if user_context[user_id].get('suggested_items'):
                        # Get user's WhatsApp number for sending incremental messages
                        from_number = f"whatsapp:{user_id}"
                        
                        # Start interactive ingredient shopping flow
                        # Store the items in a shopping queue
                        user_context[user_id]['shopping_queue'] = user_context[user_id]['suggested_items'].copy()
                        user_context[user_id]['current_ingredient_index'] = 0
                        user_context[user_id]['platform'] = platform
                        
                        # Clear suggested items
                        user_context[user_id]['suggested_items'] = []
                        
                        # Search and show first ingredient
                        first_item = user_context[user_id]['shopping_queue'][0]
                        search_result = await self.handle_search(platform, first_item, user_id)
                        
                        message = f"🛒 Let's shop for ingredients! (1/{len(user_context[user_id]['shopping_queue'])})\n\n"
                        message += f"🔍 {first_item}:\n\n{search_result}\n\n"
                        message += "Reply with:\n"
                        message += "• 'Add 1' (or any number) to add that item\n"
                        message += "• 'Skip' to skip this ingredient\n"
                        message += "• 'Stop' to stop shopping"
                        
                        send_whatsapp_message(from_number, message)
                        
                        # Return special marker to indicate messages were sent
                        return "__MESSAGES_SENT__"
                    
                    elif query:
                        # Search for specific query
                        print(f"🤖 AI calling handle_search: platform={platform}, query={query}, user_id={user_id}")
                        return await self.handle_search(platform, query, user_id)
                    else:
                        return analysis['response']
                
                elif analysis.get('action') == 'add_to_cart':
                    # User wants to add items from previous search
                    query = analysis.get('query') if analysis.get('query') is not None else message
                    print(f"🛒 Adding to cart: platform={platform}, query={query}, user_id={user_id}")
                    return await self.handle_add_to_cart(platform, query, user_id)
                
                elif analysis.get('action') == 'view_cart':
                    return await self.handle_view_cart(platform, user_id)
                
                elif analysis.get('action') == 'checkout':
                    return await self.handle_checkout(platform, user_id)
                
                elif analysis.get('action') == 'coupons':
                    return await self.handle_coupons(platform, user_id)
                
                else:
                    # For other direct commands, return None to use regular parsing
                    return None
            
            else:
                # Unknown intent, return None to use regular parsing
                return None
                
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"❌ AI conversation error: {error_details}")
            return None
    
    def get_help_message(self):
        """Return help message"""
        return """🤖 Smart Shopping Assistant

I understand English and Hinglish! Just chat naturally:

💬 Natural Chat:
• "Aaj chai peene ka mann hai"
• "Mujhe pasta banana hai"
• "I want to make biryani"

📱 Direct Commands:
• "Search for milk on Zepto"
• "Add 1" or "Add all"
• "View cart"
• "Checkout"

🛒 Platforms:
• Zepto (10 min delivery)
• Blinkit (quick groceries)
• Instamart (Swiggy)
• BigBasket (wide selection)

Just message me naturally and I'll help! 🚀"""


# Initialize bot
bot = WhatsAppOrderBot()


def send_whatsapp_message(to_number: str, message: str):
    """Send a WhatsApp message via Twilio"""
    try:
        twilio_client.messages.create(
            from_=TWILIO_WHATSAPP_NUMBER,
            body=message,
            to=to_number
        )
        print(f"✅ Message sent to {to_number}")
    except Exception as e:
        print(f"❌ Failed to send message: {e}")


def process_message_async(from_number: str, incoming_msg: str):
    """Process message in background and send response"""
    user_id = from_number.replace('whatsapp:', '')
    
    try:
        # Try AI conversation first
        ai_response = asyncio.run(bot.handle_ai_conversation(user_id, incoming_msg))
        
        if ai_response == "__MESSAGES_SENT__":
            # AI already sent messages, don't send another
            print("✅ AI sent messages directly")
            return
        elif ai_response:
            # AI handled the conversation
            print(f"🤖 AI Response: {ai_response[:100]}...")
            response_text = ai_response
        else:
            # Fall back to regular command parsing
            intent = bot.parse_message(incoming_msg, user_id)
            print(f"🎯 Intent: {intent}")
            
            # Handle action
            if intent['action'] == 'help' or not intent['action']:
                response_text = bot.get_help_message()
            elif intent['action'] == 'search':
                response_text = asyncio.run(bot.handle_search(
                    intent['platform'], intent['query'], user_id
                ))
            elif intent['action'] == 'add_to_cart':
                response_text = asyncio.run(bot.handle_add_to_cart(
                    intent['platform'], intent['query'], user_id
                ))
            elif intent['action'] == 'view_cart':
                response_text = asyncio.run(bot.handle_view_cart(
                    intent['platform'], user_id
                ))
            elif intent['action'] == 'coupons':
                response_text = asyncio.run(bot.handle_coupons(
                    intent['platform'], user_id
                ))
            elif intent['action'] == 'checkout':
                response_text = asyncio.run(bot.handle_checkout(
                    intent['platform'], user_id
                ))
            else:
                response_text = "I didn't understand that. Reply 'help' for commands."
                
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        response_text = f"Sorry, something went wrong: {str(e)}\n\nReply 'help' for assistance."
    
    # Send response back to user
    print(f"📤 Sending response: {response_text[:100]}...")
    send_whatsapp_message(from_number, response_text)


@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming WhatsApp messages - responds immediately and processes in background"""
    incoming_msg = request.values.get('Body', '').strip()
    from_number = request.values.get('From', '')
    
    print(f"\n📨 Received message from {from_number}: {incoming_msg}")
    
    # Start background processing
    thread = threading.Thread(
        target=process_message_async,
        args=(from_number, incoming_msg)
    )
    thread.daemon = True
    thread.start()
    
    # Return empty response immediately (within Twilio's timeout)
    return '', 200


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return {'status': 'ok', 'message': 'WhatsApp bot is running'}


if __name__ == '__main__':
    print("🤖 Starting WhatsApp Ordering Bot...")
    print("="*60)
    print("\n📱 Bot is ready to receive messages!")
    print("\nSetup Instructions:")
    print("1. Run: ngrok http 5000")
    print("2. Copy the ngrok URL")
    print("3. Set webhook in Twilio: https://your-ngrok-url/webhook")
    print("4. Send a WhatsApp message to your Twilio number")
    print("\n" + "="*60)
    
    # Initialize agents
    asyncio.run(bot.initialize_agents())
    
    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)
