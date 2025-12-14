"""
Setup script to create initial session files for Zepto, Blinkit, and Instamart.

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


async def setup_instamart_session():
    """Open Instamart in browser for manual login and save session"""
    print("\n" + "="*60)
    print("Setting up Instamart Session")
    print("="*60)
    print("\n⚠️  IMPORTANT: Swiggy has bot detection!")
    print("\n📱 Alternative setup methods:")
    print("   1. Use Swiggy mobile app (recommended)")
    print("   2. Login via Chrome with your regular profile")
    print("\n🔧 Manual Setup Steps:")
    print("   1. Open Chrome browser normally")
    print("   2. Go to https://www.swiggy.com/instamart")
    print("   3. Login with your phone number")
    print("   4. Keep the browser open")
    print("\n   Then use the Instamart agent with your Chrome profile")
    print("="*60)
    
    choice = input("\nTry automated setup anyway? (y/n): ").lower().strip()
    
    if choice != 'y':
        print("\n💡 Tip: For now, skip Instamart or use Zepto/Blinkit instead")
        print("   We'll add mobile app integration in the future!")
        return
    
    async with async_playwright() as p:
        # Try with more realistic browser settings
        browser = await p.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage'
            ]
        )
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        
        # Hide automation indicators
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        page = await context.new_page()
        
        await page.goto("https://www.swiggy.com/instamart")
        
        print("\n⚠️  If login fails with 403 error:")
        print("   1. Close this browser")
        print("   2. Login manually in your regular Chrome")
        print("   3. Use that session instead")
        
        # Wait for user to log in
        input("\nPress Enter after you've logged in (or Ctrl+C to cancel)...")
        
        # Save the session
        await context.storage_state(path="instamart_state.json")
        print("✅ Instamart session saved to instamart_state.json")
        
        await browser.close()


async def main():
    """Setup sessions for all platforms"""
    print("\n🔧 Session Setup Wizard")
    print("="*60)
    print("\nThis script will help you set up sessions for:")
    print("  1. Zepto")
    print("  2. Blinkit")
    print("  3. Instamart (Swiggy)")
    print("\nYou'll need to log in to each platform manually.")
    print("="*60)
    
    # Ask which platforms to set up
    setup_zepto = input("\nSetup Zepto session? (y/n): ").lower().strip() == 'y'
    setup_blinkit = input("Setup Blinkit session? (y/n): ").lower().strip() == 'y'
    setup_instamart = input("Setup Instamart session? (y/n): ").lower().strip() == 'y'
    
    if setup_zepto:
        await setup_zepto_session()
    
    if setup_blinkit:
        await setup_blinkit_session()
    
    if setup_instamart:
        await setup_instamart_session()
    
    print("\n" + "="*60)
    print("✅ Setup Complete!")
    print("="*60)
    print("\nYou can now run the agent scripts:")
    if setup_zepto:
        print("  python zepto.py")
    if setup_blinkit:
        print("  python blinkit.py")
    if setup_instamart:
        print("  python instamart.py")
    print("\n")


if __name__ == "__main__":
    asyncio.run(main())
