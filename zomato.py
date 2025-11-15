"""
Zomato Agent - Uses Zomato's MCP (Model Context Protocol) Server

Note: Zomato provides an official MCP server that handles restaurant search,
menu browsing, and order placement through their API. This is different from
the browser automation approach used for Zepto and Blinkit.

To use Zomato MCP:
1. Install required packages:
   pip install langchain-mcp-adapters langgraph langchain-openai

2. Set up your OpenAI API key in environment variables

3. Use the example below to interact with Zomato
"""

import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage


class ZomatoAgent:
    """
    Zomato ordering agent using MCP (Model Context Protocol) server.
    
    This agent connects to Zomato's official MCP server which provides
    tools for restaurant search, menu browsing, and order management.
    """
    
    def __init__(self, model: str = "gpt-4o"):
        """
        Initialize Zomato agent with MCP client.
        
        Args:
            model: OpenAI model to use (default: gpt-4o)
        """
        self.model = model
        self.client = None
        self.agent = None
        self.checkpointer = MemorySaver()
        self.config = {"configurable": {"thread_id": "1"}}
        
    async def initialize(self):
        """Initialize MCP client and agent"""
        print("🔧 Initializing Zomato MCP client...")
        
        # Configure MCP client for Zomato
        self.client = MultiServerMCPClient(
            {
                "zomato": {
                    "command": "npx",
                    "args": ["mcp-remote", "https://mcp-server.zomato.com/mcp"],
                    "transport": "stdio"
                }
            }
        )
        
        # Get available tools from Zomato MCP server
        tools = await self.client.get_tools()
        print(f"✅ Connected to Zomato MCP server with {len(tools)} tools")
        
        # Create agent with tools
        self.agent = create_react_agent(
            f"openai:{self.model}",
            tools,
            checkpointer=self.checkpointer
        )
        
        print("🎉 Zomato agent ready!")
    
    async def query(self, message: str):
        """
        Send a natural language query to Zomato agent.
        
        Args:
            message: Natural language query (e.g., "Find biryani restaurants near me")
            
        Returns:
            Agent response with restaurant information or order status
            
        Example:
            response = await agent.query("Find the best rated pizza places in Bangalore")
        """
        if not self.agent:
            await self.initialize()
        
        print(f"\n💬 Query: {message}")
        
        response = await self.agent.ainvoke(
            {"messages": [HumanMessage(content=message)]},
            self.config
        )
        
        result = response['messages'][-1].content
        print(f"\n🍽️ Response:\n{result}")
        
        return result
    
    async def search_restaurants(self, query: str, location: str = None):
        """
        Search for restaurants on Zomato.
        
        Args:
            query: Search term (e.g., "biryani", "pizza", "chinese")
            location: Location to search in (optional)
            
        Returns:
            List of restaurants matching the query
        """
        location_str = f" in {location}" if location else ""
        message = f"Find {query} restaurants{location_str}"
        return await self.query(message)
    
    async def get_menu(self, restaurant_name: str):
        """
        Get menu for a specific restaurant.
        
        Args:
            restaurant_name: Name of the restaurant
            
        Returns:
            Menu items with prices
        """
        message = f"Show me the menu for {restaurant_name}"
        return await self.query(message)
    
    async def get_order_history(self):
        """
        Get past order history from Zomato.
        
        Returns:
            List of past orders
        """
        message = "What's my past order list?"
        return await self.query(message)
    
    async def place_order(self, restaurant_name: str, items: list):
        """
        Place an order on Zomato.
        
        Args:
            restaurant_name: Name of the restaurant
            items: List of items to order
            
        Returns:
            Order confirmation details
            
        Note: This is a placeholder. Actual order placement requires
        authentication and payment handling through Zomato's MCP server.
        """
        items_str = ", ".join(items)
        message = f"Order {items_str} from {restaurant_name}"
        return await self.query(message)
    
    async def close(self):
        """Close MCP client connection"""
        if self.client:
            await self.client.close()
            print("👋 Zomato agent closed")


# Example usage
async def main():
    """Example usage of Zomato agent"""
    
    # Create agent instance
    zomato = ZomatoAgent()
    
    try:
        # Initialize connection to Zomato MCP server
        await zomato.initialize()
        
        # Example 1: Search for restaurants
        print("\n" + "="*60)
        print("Example 1: Search for restaurants")
        print("="*60)
        await zomato.search_restaurants("biryani", location="Bangalore")
        
        # Example 2: Get order history
        print("\n" + "="*60)
        print("Example 2: Get order history")
        print("="*60)
        await zomato.get_order_history()
        
        # Example 3: Custom query
        print("\n" + "="*60)
        print("Example 3: Custom query")
        print("="*60)
        await zomato.query("What are the top rated restaurants near me?")
        
    finally:
        # Clean up
        await zomato.close()


if __name__ == "__main__":
    # Note: Make sure you have OPENAI_API_KEY set in your environment
    # export OPENAI_API_KEY="your-api-key-here"
    
    asyncio.run(main())
