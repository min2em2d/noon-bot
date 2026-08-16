import os
import uuid
import time
import random
from playwright.sync_api import sync_playwright

def generate_strong_password():
    return "TestPass123!@"

def generate_custom_gmail():
    return f"testnoon_{int(time.time())}{random.randint(100, 999)}@gmail.com"

def run():
    CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    with sync_playwright() as p:
        profile_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_profile_dump")
        if os.path.exists(profile_dir):
            import shutil
            shutil.rmtree(profile_dir, ignore_errors=True)
            
        context = p.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            executable_path=CHROME_PATH,
            headless=False,
            viewport={'width': 1200, 'height': 800}
        )
        page = context.pages[0]
        
        # Navigate to profile (redirects to home/login)
        print("Navigating to profile page...")
        page.goto("https://account.noon.com/egypt-en/profile/", wait_until="domcontentloaded")
        time.sleep(2)
        
        # Click LOGIN/SIGNUP
        print("Opening login modal...")
        page.click('text="LOGIN/SIGNUP"')
        time.sleep(1)
        
        # Click Sign up tab
        print("Switching to Sign up tab...")
        page.click('text="Sign up"')
        time.sleep(1)
        
        # Fill email and password
        email = generate_custom_gmail()
        password = generate_strong_password()
        print(f"Signing up with {email} / {password}...")
        page.locator('input[name="email"]').fill(email)
        page.locator('input[name="password"]').fill(password)
        
        # Click Sign Up button
        page.click('button:has-text("SIGN UP"), button:has-text("Sign up"), button:has-text("Sign Up")')
        
        # Wait to register and redirect to profile page
        print("Waiting for registration redirect...")
        time.sleep(6)
        
        # Verify if we are on the profile page
        if "profile" in page.url:
            print("Successfully registered and navigated to profile!")
            
            # Click "Add" phone number
            print("Opening Add phone number modal...")
            page.locator('text="Add", button:has-text("Add"), span:has-text("Add")').first.click()
            time.sleep(2)
            
            # Dump HTML
            html = page.content()
            with open("modal_dump.html", "w", encoding="utf-8") as out:
                out.write(html)
            print("SUCCESS: Modal HTML successfully dumped to modal_dump.html")
        else:
            print(f"Failed to register. Current URL: {page.url}")
            # Take screenshot to see what's wrong
            page.screenshot(path="failed_registration.png")
            print("Screenshot saved to failed_registration.png")
            
        context.close()

if __name__ == "__main__":
    run()
