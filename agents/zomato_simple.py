"""
Simple Zomato Agent - Uses Gemini AI directly (no MCP server required)

This is a simplified version that uses Gemini to help with restaurant searches
and food ordering queries without requiring an external MCP server.
"""

import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage


class ZomatoSimpleAgent:
    """
    Simple Zomato agent using Gemini AI directly.
    
    This agent uses Gemini to provide intelligent responses about restaurants,
    food ordering, and menu queries without requiring an external MCP server.
    """
    
    def __init__(self, model: str = "gemini-2.0-flash-exp"):
        """
        Initialize Zomato agent with Gemini.
        
        Args:
            model: Gemini model to use (default: gemini-2.0-flash-exp)
        """
        self.model = model
        self.llm = None
        self.conversation_history = {}
        
   