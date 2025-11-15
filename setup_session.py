"""
Setup script to create initial session files for Zepto and Blinkit.

Run this script first to log in to each platform and save the session.
After running this once, the main agent scripts will use the saved sessions.
"""

import asyncio
from playwright.async_api import async_playwright


async def setup_zepto_session():
    """Open Zepto in browser for manual login and save session"""
    print("\n" + "="*60)
    print("Setting up Zepto Session")
    print("="*60)
    print("\n📱 Opening Zepto in browser...")
    print("   Please log in to your Zepto account")
    print("   Once logged in, press Enter in this terminal to save the session\n")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        await page.goto("https://www.zeptonow.com")
        
        # Wait for user to log in
        input("Press Enter after you've logged in to Zepto...")
        
        # Save the session
        await context.storage_state(path="zepto_state.json")
        print("✅ Zepto session saved to zepto_state.json")
        
        await browser.close()


async def setup_blinkit_session():
    """Open Blinkit in browser for manual login and save session"""
    print("\n" + "="*60)
    print("Setting up Blinkit Session")
    print("="*60)
    print("\n📱 Opening Blinkit in browser...")
    print("   Please log in to your Blinkit account")
    print("   Once logged in, press Enter in this terminal to save the session\n")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        await page.goto("https://blinkit.com")
        
        # Wait for user to log in
        input("Press Enter after you've logged in to Blinkit...")
        
        # Save the session
        await context.storage_state(path="blinkit_state.json")
        print("✅ Blinkit session saved to blinkit_state.json")
        
        await browser.close()


async def main():
    """Setup sessions for all platforms"""
    print("\n🔧 Session Setup Wizard")
    print("="*60)
    print("\nThis script will help you set up sessions for:")
    print("  1. Zepto")
    print("  2. Blinkit")
    print("\nYou'll need to log in to each platform manually.")
    print("="*60)
    
    # Ask which platforms to set up
    setup_zepto = input("\nSetup Zepto session? (y/n): ").lower().strip() == 'y'
    setup_blinkit = input("Setup Blinkit session? (y/n): ").lower().strip() == 'y'
    
    if setup_zepto:
        await setup_zepto_session()
    
    if setup_blinkit:
        await setup_blinkit_session()
    
    print("\n" + "="*60)
    print("✅ Setup Complete!")
    print("="*60)
    print("\nYou can now run the agent scripts:")
    if setup_zepto:
        print("  python zepto.py")
    if setup_blinkit:
        print("  python blinkit.py")
    print("\n")


if __name__ == "__main__":
    asyncio.run(main())
