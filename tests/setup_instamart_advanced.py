"""
Advanced Instamart Session Setup with Stealth Mode

This script uses advanced techniques to bypass Swiggy's bot detection:
- Stealth browser configuration
- Realistic user behavior simulation
- Custom headers and fingerprinting
- Manual intervention for OTP/verification
"""

import asyncio
from playwright.async_api import async_playwright
import random


async def setup_instamart_stealth():
    """Setup Instamart session with advanced stealth techniques"""
    print("\n" + "="*70)
    print("🕵️  Advanced Instamart Session Setup (Stealth Mode)")
    print("="*70)
    print("\n📋 This setup uses advanced techniques to bypass bot detection:")
    print("   ✓ Stealth browser configuration")
    print("   ✓ Realistic user behavior simulation")
    print("   ✓ Custom headers and fingerprinting")
    print("   ✓ Manual OTP verification support")
    print("\n" + "="*70)
    
    async with async_playwright() as p:
        print("\n🚀 Launching stealth browser...")
        
        # Launch with maximum stealth
        browser = await p.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-infobars',
                '--window-position=0,0',
                '--ignore-certifcate-errors',
                '--ignore-certifcate-errors-spki-list',
                '--disable-blink-features',
                '--disable-automation',
                '--disable-extensions',
                '--profile-directory=Default',
                '--disable-plugins-discovery',
                '--start-maximized',
                '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ],
            chromium_sandbox=False
        )
        
        # Create context with realistic settings
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-IN',
            timezone_id='Asia/Kolkata',
            permissions=['geolocation'],
            geolocation={'latitude': 12.9716, 'longitude': 77.5946},  # Bangalore
            extra_http_headers={
                'Accept-Language': 'en-IN,en;q=0.9,hi;q=0.8',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"'
            }
        )
        
        # Add comprehensive stealth scripts
        await context.add_init_script("""
            // Remove webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            // Mock plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => {
                    return [
                        {
                            0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format", enabledPlugin: Plugin},
                            description: "Portable Document Format",
                            filename: "internal-pdf-viewer",
                            length: 1,
                            name: "Chrome PDF Plugin"
                        },
                        {
                            0: {type: "application/pdf", suffixes: "pdf", description: "", enabledPlugin: Plugin},
                            description: "",
                            filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                            length: 1,
                            name: "Chrome PDF Viewer"
                        },
                        {
                            0: {type: "application/x-nacl", suffixes: "", description: "Native Client Executable", enabledPlugin: Plugin},
                            1: {type: "application/x-pnacl", suffixes: "", description: "Portable Native Client Executable", enabledPlugin: Plugin},
                            description: "",
                            filename: "internal-nacl-plugin",
                            length: 2,
                            name: "Native Client"
                        }
                    ];
                },
            });
            
            // Mock languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-IN', 'en', 'hi'],
            });
            
            // Mock permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            // Add chrome object
            window.chrome = {
                runtime: {},
                loadTimes: function() {},
                csi: function() {},
                app: {}
            };
            
            // Mock battery
            Object.defineProperty(navigator, 'getBattery', {
                value: () => Promise.resolve({
                    charging: true,
                    chargingTime: 0,
                    dischargingTime: Infinity,
                    level: 1
                })
            });
            
            // Mock connection
            Object.defineProperty(navigator, 'connection', {
                value: {
                    effectiveType: '4g',
                    rtt: 50,
                    downlink: 10,
                    saveData: false
                }
            });
            
            // Mock hardware concurrency
            Object.defineProperty(navigator, 'hardwareConcurrency', {
                get: () => 8
            });
            
            // Mock device memory
            Object.defineProperty(navigator, 'deviceMemory', {
                get: () => 8
            });
            
            // Override toString
            window.navigator.toString = () => '[object Navigator]';
        """)
        
        page = await context.new_page()
        
        print("✅ Stealth browser configured")
        print("\n📱 Opening Swiggy Instamart...")
        print("   URL: https://www.swiggy.com/instamart")
        
        # Navigate with realistic timing
        await asyncio.sleep(random.uniform(1, 2))
        await page.goto("https://www.swiggy.com/instamart", wait_until="networkidle", timeout=60000)
        await asyncio.sleep(random.uniform(2, 3))
        
        # Simulate human behavior
        print("\n🖱️  Simulating human behavior...")
        await page.mouse.move(random.randint(100, 500), random.randint(100, 500))
        await asyncio.sleep(random.uniform(0.5, 1.5))
        await page.evaluate("window.scrollBy(0, 100)")
        await asyncio.sleep(random.uniform(1, 2))
        
        print("\n" + "="*70)
        print("📋 MANUAL LOGIN INSTRUCTIONS:")
        print("="*70)
        print("\n1. The browser window should now be open")
        print("2. Click on 'Login' or 'Sign In'")
        print("3. Enter your phone number")
        print("4. Complete OTP verification")
        print("5. Make sure you're logged in successfully")
        print("6. You should see your location/address")
        print("\n⚠️  IMPORTANT:")
        print("   - Take your time with the login")
        print("   - Complete any CAPTCHA if shown")
        print("   - Verify your phone number")
        print("   - Don't close the browser!")
        print("\n" + "="*70)
        
        input("\n✋ Press Enter AFTER you've successfully logged in...")
        
        # Verify login
        print("\n🔍 Verifying login status...")
        await asyncio.sleep(2)
        
        # Check if logged in by looking for user indicators
        try:
            # Look for common logged-in indicators
            await page.wait_for_selector('[class*="user"], [class*="profile"], [class*="account"]', timeout=5000)
            print("✅ Login verified!")
        except:
            print("⚠️  Could not verify login automatically")
            confirm = input("Are you sure you're logged in? (y/n): ")
            if confirm.lower() != 'y':
                print("❌ Setup cancelled. Please try again.")
                await browser.close()
                return
        
        # Save the session
        print("\n💾 Saving session...")
        await context.storage_state(path="sessions/instamart_session/state.json")
        print("✅ Session saved to: sessions/instamart_session/state.json")
        
        print("\n" + "="*70)
        print("🎉 Setup Complete!")
        print("="*70)
        print("\n✅ Your Instamart session is now saved")
        print("✅ The bot can now use this session for automation")
        print("\nYou can now:")
        print("  1. Close this browser")
        print("  2. Run: python blinkit_mcp/whatsapp_bot.py")
        print("  3. Test with: 'Search for milk on Instamart'")
        print("\n" + "="*70)
        
        input("\nPress Enter to close the browser...")
        await browser.close()


if __name__ == "__main__":
    print("\n🕵️  Instamart Advanced Setup")
    print("This will help you bypass Swiggy's bot detection\n")
    
    try:
        asyncio.run(setup_instamart_stealth())
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user")
    except Exception as e:
        print(f"\n\n❌ Error during setup: {e}")
        print("\nTroubleshooting:")
        print("  1. Make sure Playwright is installed: pip install playwright")
        print("  2. Install browsers: playwright install chromium")
        print("  3. Check your internet connection")
        print("  4. Try again with a different network")
