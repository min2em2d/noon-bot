import os
import sys
import time
import json
import uuid
import random
from curl_cffi import requests
from playwright.sync_api import sync_playwright

# reCAPTCHA Enterprise Site Key for Noon
RECAPTCHA_KEY = "6Lc3F28qAAAAALqhS6u6ULhid0FfhAQxz0uwVQjC"

def generate_strong_password():
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
    return "01223456" + "".join(random.choice(chars) for _ in range(4)) + "@"

def generate_custom_gmail():
    prefix = "nabil"
    mid = random.choice(["c", "d", "e", "f", "k"])
    num1 = random.randint(1, 9)
    name = random.choice(["omar", "salem", "ibrahim", "ali"])
    num2 = random.randint(1000, 9999)
    return f"{prefix}{mid}{num1}{name}{num2}@gmail.com"

def safe_click(page, selectors, timeout=3000, force=False):
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            loc.wait_for(state="visible", timeout=timeout)
            loc.click(force=force)
            return True
        except Exception:
            continue
    return False

def get_recaptcha_token(page, action):
    """Wait for reCAPTCHA script to load and generate a token for an action"""
    try:
        page.wait_for_function(
            "typeof grecaptcha !== 'undefined' && typeof grecaptcha.execute !== 'undefined'",
            timeout=15000
        )
        token = page.evaluate(
            f"grecaptcha.execute('{RECAPTCHA_KEY}', {{action: '{action}'}})"
        )
        return token
    except Exception as e:
        print(f"[RECAPTCHA ERROR] Failed to generate token: {e}")
        return None

def sync_cookies_to_curl(context, session):
    """Sync Playwright browser cookies to curl_cffi session"""
    cookies = context.cookies()
    for cookie in cookies:
        session.cookies.set(
            name=cookie['name'],
            value=cookie['value'],
            domain=cookie['domain'],
            path=cookie['path']
        )

def sync_cookies_to_playwright(session, context):
    """Sync curl_cffi session cookies back to Playwright browser context"""
    cookies_to_add = []
    for cookie in session.cookies.jar:
        name = cookie.name
        value = cookie.value
        domain = cookie.domain
        path = cookie.path
        
        if name.lower() == "_grecaptcha" or name.startswith("_grecaptcha"):
            continue
            
        if not domain:
            domain = ".noon.com"
        elif "noon.com" not in domain.lower():
            continue
            
        cookies_to_add.append({
            "name": name,
            "value": value,
            "domain": domain,
            "path": path if path else "/"
        })
    try:
        context.add_cookies(cookies_to_add)
    except Exception as e:
        print(f"Cookie sync back error: {e}")

def human_click(page, selectors, timeout=5000):
    if isinstance(selectors, str):
        selectors = [selectors]
    for selector in selectors:
        try:
            loc = page.locator(selector).first
            loc.wait_for(state="visible", timeout=timeout)
            box = loc.bounding_box()
            if box:
                x = box['x'] + box['width']/2 + random.uniform(-2, 2)
                y = box['y'] + box['height']/2 + random.uniform(-2, 2)
                # Simulate human mouse movement
                page.mouse.move(x, y, steps=random.randint(15, 25))
                time.sleep(random.uniform(0.1, 0.3))
                page.mouse.click(x, y)
                return True
        except Exception:
            continue
    # Fallback to direct page click if bounding box fails
    for selector in selectors:
        try:
            page.click(selector, timeout=timeout, force=True)
            return True
        except Exception:
            continue
    return False

def human_type(page, selectors, text, timeout=5000):
    if isinstance(selectors, str):
        selectors = [selectors]
    # Focus input first
    if not human_click(page, selectors, timeout):
        return False
    time.sleep(random.uniform(0.2, 0.4))
    
    # Get active locator to fill and type
    loc = None
    for selector in selectors:
        try:
            l = page.locator(selector).first
            if l.is_visible():
                loc = l
                break
        except Exception:
            continue
    if not loc:
        return False
        
    try:
        loc.fill("")
        time.sleep(random.uniform(0.1, 0.2))
        for char in text:
            page.keyboard.type(char)
            time.sleep(random.uniform(0.08, 0.22))
        return True
    except Exception as e:
        print(f"    [WARNING] Human type failed: {e}")
        return False

def main():
    print("=" * 60)
    print("        NOON EGYPT HYBRID MANUAL-BROWSER AUTOMATION")
    print("=" * 60)
    
    email = generate_custom_gmail()
    password = generate_strong_password()
    visitor_id = str(uuid.uuid4())
    
    print(f"Generated Email:  {email}")
    print(f"Password:          {password}")
    print("=" * 60)

    print("[0] Terminating background Chrome processes to unlock files...")
    try:
        import subprocess
        subprocess.run("taskkill /f /im chrome.exe", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1)
    except Exception:
        pass

    CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    profile_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hybrid_profile")
    
    if os.path.exists(profile_dir):
        import shutil
        try:
            shutil.rmtree(profile_dir)
            print("    Successfully cleared old Chrome session profile.")
        except Exception as e:
            print(f"    [WARNING] Could not clear profile folder: {e}. Session may carry over.")
    else:
        print("    No previous session folder found. Starting fresh.")
            
    os.makedirs(profile_dir, exist_ok=True)

    chrome_process = None
    playwright_instance = None
    try:
        import subprocess
        playwright_instance = sync_playwright().start()
        chrome_port = 9222
        print(f"[1] Starting native Google Chrome on port {chrome_port}...")
        
        # Remove lock file if it exists from previous crashed runs
        lock_file = os.path.join(profile_dir, "SingletonLock")
        if os.path.exists(lock_file):
            try:
                os.remove(lock_file)
            except Exception:
                pass
                
        cmd = [
            CHROME_PATH,
            f"--remote-debugging-port={chrome_port}",
            f"--user-data-dir={profile_dir}",
            "--no-first-run",
            "--no-default-browser-check",
            "--lang=en-US",
            "--accept-lang=en-US,en"
        ]
        chrome_process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(3)  # Wait for Chrome to fully bind
        
        print("[1.5] Connecting Playwright over CDP...")
        browser = playwright_instance.chromium.connect_over_cdp(f"http://localhost:{chrome_port}")
        context = browser.contexts[0]
        page = context.pages[0]
        
        try:
            page.set_viewport_size({'width': 1200, 'height': 800})
        except Exception:
            pass

        print("[2] Loading Noon Portal...")
        page.goto("https://account.noon.com/egypt-en/profile/", wait_until="domcontentloaded")
        time.sleep(1)

        print("[2.5] Opening Signup Modal in UI...")
        login_signup_selectors = [
            'text="Login/Signup"',
            'text="LOGIN/SIGNUP"',
            'div.layout-module-scss-module__-MERqq__mainLayout span',
            'xpath=//html/body/div[2]/div/main/div/div/div[2]/button/span',
            'button:has-text("Login")',
            'span:has-text("Login")',
            'div[title="Log in"]',
            'button[data-qa="btn_header_signInOrUp-header-desktop"]',
        ]
        if safe_click(page, login_signup_selectors, timeout=5000):
            print("    Successfully opened Login/Signup modal.")
        else:
            print("    Warning: Failed to click Login/Signup button.")
        time.sleep(1)

        signup_link_selectors = [
            '[data-qa="sign-up"]',
            'aria/Sign up',
            'text="Sign up"',
            'text="Sign Up"',
            '[data-qa="Register-now"]',
            'button:has-text("Sign up")',
            'span:has-text("Sign up")',
        ]
        if safe_click(page, signup_link_selectors, timeout=3000):
            print("    Successfully switched to Sign Up tab.")
        else:
            print("    Warning: Failed to click Sign Up tab.")
        time.sleep(1)

        session = requests.Session(impersonate="chrome124")
        sync_cookies_to_curl(context, session)

        print("[3] Generating reCAPTCHA token for check-in...")
        token_signin = get_recaptcha_token(page, "login")
        if not token_signin:
            print("[ERROR] Could not generate reCAPTCHA token. Exiting.")
            context.close()
            return

        print("[4] Sending /auth/sign-in request via API...")
        headers = {
            "content-type": "application/json",
            "x-locale": "en-eg",
            "x-platform": "web",
            "x-visitor-id": visitor_id
        }
        
        payload_signin = {
            "emailOrPhone": email,
            "recaptcha": {
                "token": token_signin,
                "action": "login",
                "key": RECAPTCHA_KEY
            }
        }

        resp_signin = session.post(
            "https://account.noon.com/_vs/st/mp-identity-api/auth/sign-in",
            json=payload_signin,
            headers=headers
        )
        print(f"    Response Status: {resp_signin.status_code}")

        print("[5] Generating reCAPTCHA token for signup...")
        token_signup = get_recaptcha_token(page, "login")
        
        payload_signup = {
            "email": email,
            "password": password,
            "recaptcha": {
                "token": token_signup,
                "action": "login",
                "key": RECAPTCHA_KEY
            },
            "deviceName": "Windows / Chrome"
        }

        print("[6] Registering account via /auth/sign-in-with-password API...")
        resp_signup = session.post(
            "https://account.noon.com/_vs/st/mp-identity-api/auth/sign-in-with-password",
            json=payload_signup,
            headers=headers
        )
        print(f"    Response Status: {resp_signup.status_code}")
        
        if resp_signup.status_code != 200:
            print("[ERROR] Registration failed. Response:")
            print(resp_signup.text)
            context.close()
            return
            
        print("[SUCCESS] Account created successfully via API!")
        sync_cookies_to_playwright(session, context)

        print("[7] Loading profile page in browser...")
        page.goto("https://account.noon.com/egypt-en/profile/", wait_until="domcontentloaded")
        time.sleep(2)

        print("[7.5] Opening Add Phone Modal in UI (human simulation)...")
        add_phone_selectors = [
            'text="Add"',
            'button:has-text("Add")',
            'span:has-text("Add")',
        ]
        human_click(page, add_phone_selectors, timeout=5000)
        time.sleep(1.5)

        print("\n" + "=" * 60)
        print(">>> SELECT COUNTRY:")
        print(">>> 1. Egypt (+20)")
        print(">>> 2. Mali (+223)")
        print("=" * 60)
        
        while True:
            choice = input("Select choice (1 or 2): ").strip()
            if choice in ["1", "2"]:
                break
            print("Invalid choice. Please enter 1 or 2.")
            
        phone_number = input("\nEnter phone number: ").strip()
        
        if choice == "2":
            print("    Selecting Mali (+223) in browser UI (human simulation)...")
            try:
                # Click dropdown using human click
                trigger_selectors = [
                    "button.CountryCodeSelect-module-scss-module__wwAlcW__trigger",
                    "button[class*='CountryCodeSelect-module-scss-module__wwAlcW__trigger']"
                ]
                human_click(page, trigger_selectors, timeout=5000)
                time.sleep(1.5)
                
                # Type 'mali' in search box using human typing
                search_selectors = [
                    "#overlay-portal input[id*='react-select']",
                    "input[id*='react-select']"
                ]
                human_type(page, search_selectors, "mali", timeout=3000)
                time.sleep(1.5)
                
                # Select Mali from option list using human click
                mali_option_selectors = [
                    "#overlay-portal div[role='option']:has-text('Mali')",
                    "#overlay-portal div[class*='option']:has-text('Mali')",
                    "div[role='option']:has-text('Mali')"
                ]
                human_click(page, mali_option_selectors, timeout=5000)
                time.sleep(1.5)
                print("    Successfully selected Mali.")
            except Exception as e:
                print(f"    [WARNING] Failed to select Mali in UI: {e}")
        else:
            print("    Keeping Egypt (+20) as default.")
            
        print(f"    Typing phone number '{phone_number}' in browser UI (human simulation)...")
        try:
            phone_input_selectors = [
                "input[name='primaryPhone']",
                "input.PhoneInput-module-scss-module__gXMrQq__input"
            ]
            human_type(page, phone_input_selectors, phone_number, timeout=5000)
            time.sleep(1.5)
        except Exception as e:
            print(f"    [WARNING] Failed to type phone number in UI: {e}")

        print("\n[8] Submitting phone number in browser UI (human simulation)...")
        submit_btn_selectors = [
            'button:has-text("ADD PHONE NUMBER")',
            'button:has-text("Add Phone Number")',
            'button[type="submit"]'
        ]
        human_click(page, submit_btn_selectors, timeout=5000)
        time.sleep(2)

        print("[9] Waiting for verification modal & clicking SMS 1 button...")
        try:
            # Match only VISIBLE button or clickable elements with text SMS
            sms_btn = page.locator('button:has-text("SMS"):visible, [role="button"]:has-text("SMS"):visible').first
            sms_btn.wait_for(state="visible", timeout=15000)
            
            # Wait for SMS 1 button to become enabled
            print("    Waiting for SMS 1 button to become enabled (cooldown)...")
            start_time = time.time()
            is_enabled = False
            last_print = 0
            while time.time() - start_time < 35:
                disabled_prop = sms_btn.is_disabled()
                aria_disabled = sms_btn.get_attribute("aria-disabled")
                
                if not disabled_prop and aria_disabled != "true":
                    is_enabled = True
                    break
                    
                if time.time() - last_print > 3:
                    print(f"      [Status] disabled={disabled_prop}, aria-disabled={aria_disabled}")
                    last_print = time.time()
                    
                time.sleep(0.5)
                
            if is_enabled:
                print(f"    SMS 1 button became enabled after {int(time.time() - start_time)} seconds.")
            else:
                print("    [WARNING] SMS 1 button did not report 'enabled' state. Attempting click anyway...")
                
            sms_btn.click(timeout=5000)
            print("[SUCCESS] Clicked SMS 1 button in browser UI!")
            
            # Wait for SMS 2 button to become enabled
            print("[10] Waiting for SMS 2 button to become enabled (cooldown)...")
            start_time = time.time()
            is_enabled = False
            last_print = 0
            while time.time() - start_time < 35:
                disabled_prop = sms_btn.is_disabled()
                aria_disabled = sms_btn.get_attribute("aria-disabled")
                
                if not disabled_prop and aria_disabled != "true":
                    is_enabled = True
                    break
                    
                if time.time() - last_print > 3:
                    print(f"      [Status] disabled={disabled_prop}, aria-disabled={aria_disabled}")
                    last_print = time.time()
                    
                time.sleep(0.5)
                
            if is_enabled:
                print(f"    SMS 2 button became enabled after {int(time.time() - start_time)} seconds.")
            else:
                print("    [WARNING] SMS 2 button did not report 'enabled' state. Attempting click anyway...")
                
            sms_btn.click(timeout=5000)
            print("[SUCCESS] Clicked SMS 2 button in browser UI! [COMPLETED]")
            
        except Exception as err:
            print(f"[WARNING] Modal or SMS click issue: {err}")

        print("\n>>> Verification flow completed! Press ENTER to exit.")
        input()
        try:
            context.close()
        except Exception:
            pass
    finally:
        if chrome_process:
            print("Terminating Chrome process...")
            try:
                chrome_process.terminate()
            except Exception:
                pass
        if playwright_instance:
            try:
                playwright_instance.stop()
            except Exception:
                pass

if __name__ == "__main__":
    main()
