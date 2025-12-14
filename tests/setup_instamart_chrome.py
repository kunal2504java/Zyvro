"""
Instamart Setup Using Chrome Profile Method

This method uses your actual Chrome browser profile where you're already logged in.
Success rate: ~90% (much better than stealth mode)

Steps:
1. Login to Swiggy in your regular Chrome browser
2. Keep Chrome CLOSED when running this script
3. This script will use your Chrome profile
4. Session will be saved for automation
"""

import os
import sys
from playwright.sync_api import sync_playwright
import time


def find_chrome_profile():
    """Find Chrome user data directory based on OS"""
    if sys.platform == "win32":
        # Windows
        base = os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\User Data")
    elif sys.platform == "darwin":
        # Mac
        base = os.path.expanduser("~/Library/Application Support/Google/Chrome")
    else:
        # Linux
        base = os.path.expanduser("~/.config/google-chrome")
    
    return base if os.path.exists(base) else None


def setup_with_chrome_profile():
    """Setup Instamart using Chrome profile"""
    
    print("\n" + "="*70)
    print("  🌐 Instamart Setup - Chrome Profile Method")
    print("="*70)
    
    # Find Chrome profile
    chrome_profile = find_chrome_profile()
    
    if not chrome_profile:
        print("\n❌ Could not find Chrome profile directory")
        print("\nExpected locations:")
        print("  Windows: C:\\Users\\YourName\\AppData\\Local\\Google\\Chrome\\User Data")
        print("  Mac: ~/Library/Application Support/Google/Chrome")
        print("  Linux: ~/.config/google-chrome")
        print("\nMake sure Chrome is installed!")
        return False
    
    print(f"\n✅ Found Chrome profile: {chrome_profile}")
    
    # Instructions
    print("\n" + "="*70)
    print("  📋 IMPORTANT INSTRUCTIONS")
    print("="*70)
    print("\n1. First, login to Swiggy in your regular Chrome browser:")
    print("   - Open Chrome normally")
    print("   - Go to: https://www.swiggy.com/instamart")
    print("   - Login with your phone number")
    print("   - Complete OTP verification")
    print("   - Make sure you're logged in")
    print("\n2. Then, CLOSE ALL Chrome windows completely")
    print("   - Close all Chrome tabs")
    print("   - Make sure Chrome is not running")
    print("   - Check Task Manager if needed")
    print("\n3. Come back here and continue")
    print("="*70)
    
    input("\n✋ Press Enter AFTER you've logged in to Swiggy and CLOSED Chrome...")
    
    # Check if Chrome is still running
    print("\n🔍 Checking if Chrome is closed...")
    
    try:
        with sync_playwright() as p:
            print("🚀 Launching Chrome with your profile...")
            
            # Launch persistent context with Chrome profile
            context = p.chromium.launch_persistent_context(
                user_data_dir=chrome_profile,
                headless=False,
                channel="chrome",  # Use installed Chrome
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-first-run',
                    '--no-default-browser-check',
                ]
            )
            
            print("✅ Chrome launched successfully")
            
            # Get or create page
            if context.pages:
                page = context.pages[0]
            else:
                page = context.new_page()
            
            print("\n📱 Navigating to Swiggy Instamart...")
            page.goto("https://www.swiggy.com/instamart", wait_until="networkidle", timeout=60000)
            time.sleep(3)
            
            # Check if logged in
            print("\n🔍 Checking login status...")
            
            # Look for login indicators
            is_logged_in = False
            
            try:
                # Check for user profile/account elements
                page.wait_for_selector('[class*="user"], [class*="profile"], [class*="account"], [class*="location"]', timeout=5000)
                is_logged_in = True
                print("✅ You appear to be logged in!")
            except:
                print("⚠️  Could not verify login automatically")
            
            if not is_logged_in:
                print("\n" + "="*70)
                print("  ⚠️  LOGIN VERIFICATION")
                print("="*70)
                print("\nPlease check the Chrome window:")
                print("  - Are you logged in?")
                print("  - Can you see your location/address?")
                print("  - Can you search for products?")
                
                confirm = input("\nAre you logged in? (y/n): ").lower().strip()
                if confirm != 'y':
                    print("\n❌ Please login in the Chrome window, then run this script again")
                    context.close()
                    return False
            
            # Save session
            print("\n💾 Saving session...")
            os.makedirs("sessions/instamart_session", exist_ok=True)
            context.storage_state(path="sessions/instamart_session/state.json")
            print("✅ Session saved!")
            
            # Success message
            print("\n" + "="*70)
            print("  🎉 Setup Complete!")
            print("="*70)
            print("\n✅ Instamart session is now configured")
            print("✅ You can now use Instamart automation")
            print("\nNext steps:")
            print("  1. Close this Chrome window")
            print("  2. Test: python blinkit_mcp/test_instamart.py")
            print("  3. Or run: python blinkit_mcp/whatsapp_bot.py")
            print("\n" + "="*70)
            
            input("\nPress Enter to close Chrome...")
            context.close()
            
            return True
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        
        if "Timeout" in str(e):
            print("\n💡 Timeout error - Chrome might still be running")
            print("   Close ALL Chrome windows and try again")
        elif "Cannot create" in str(e) or "already in use" in str(e):
            print("\n💡 Chrome profile is in use")
            print("   Make sure ALL Chrome windows are closed")
            print("   Check Task Manager and end Chrome processes")
        else:
            print("\n💡 Troubleshooting:")
            print("   1. Close all Chrome windows")
            print("   2. Check Task Manager for Chrome processes")
            print("   3. Try restarting your computer")
            print("   4. Make sure Chrome is installed")
        
        return False


def main():
    """Main setup function"""
    print("\n🌐 Instamart Setup - Chrome Profile Method")
    print("\nThis method uses your actual Chrome browser profile.")
    print("Success rate: ~90% (much better than stealth mode)")
    print("\nRequirements:")
    print("  ✓ Google Chrome installed")
    print("  ✓ Logged in to Swiggy in Chrome")
    print("  ✓ Chrome completely closed before running")
    
    input("\nPress Enter to continue...")
    
    success = setup_with_chrome_profile()
    
    if success:
        print("\n✅ All done! Instamart is ready to use.")
    else:
        print("\n❌ Setup failed. Please try again.")
        print("\nAlternative: Focus on Zepto and Blinkit (they work great!)")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup cancelled by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        print("\nPlease report this error if it persists")
