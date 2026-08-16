import os
import sys
import subprocess

def install_and_import_dependencies():
    required_packages = {
        "playwright": "playwright>=1.40.0",
        "curl_cffi": "curl_cffi>=0.6.0"
    }
    
    missing_packages = []
    
    # Check curl_cffi
    try:
        import curl_cffi
    except ImportError:
        missing_packages.append(required_packages["curl_cffi"])
        
    # Check playwright
    try:
        import playwright
    except ImportError:
        missing_packages.append(required_packages["playwright"])
        
    if missing_packages:
        print("[*] Missing required packages detected. Installing automatically...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
            print("[*] Packages installed successfully.")
        except Exception as e:
            print(f"[ERROR] Failed to install packages automatically: {e}")
            print("[*] Please run: pip install playwright curl_cffi")
            sys.exit(1)
            
        if "playwright" in "".join(missing_packages).lower():
            print("[*] Initializing Playwright browser binaries...")
            try:
                subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
                print("[*] Playwright initialized successfully.")
            except Exception as e:
                print(f"[ERROR] Failed to install Playwright browser binaries: {e}")
                print("[*] Please run: playwright install chromium")
                sys.exit(1)

# Run dependency check before importing other libraries
install_and_import_dependencies()

try:
    from updater import check_for_updates
    check_for_updates()
except Exception:
    pass

import time
import json
import uuid
import random
from curl_cffi import requests
from playwright.sync_api import sync_playwright
from msi_api import MSIApiClient
from expressvpn_manager import rotate_vpn, is_vpn_connected, get_vpn_status

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

def cleanup_chrome_and_profile(profile_dir):
    """Kills any active Chrome processes and completely wipes the session profile folder."""
    try:
        import subprocess
        subprocess.run("taskkill /f /im chrome.exe", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1.5)
    except Exception:
        pass
        
    if os.path.exists(profile_dir):
        import shutil
        for _ in range(3):
            try:
                shutil.rmtree(profile_dir)
                break
            except Exception:
                time.sleep(1)
        if os.path.exists(profile_dir):
            print("    [WARNING] Could not fully remove profile folder. Some files may be locked.")
        else:
            print("    ✅ Complete Wipe: Deleted old Chrome session, cookies, cache & local storage.")

def save_account_record(email, password, phone, filename="created_accounts.txt"):
    """Saves created account credentials to text file."""
    try:
        now_str = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(filename, "a", encoding="utf-8") as f:
            f.write(f"{email}:{password}:{phone}:{now_str}\n")
        print(f"📁 [SAVED] Account record appended to {filename}")
    except Exception as e:
        print(f"[WARNING] Could not save account record: {e}")

def run_single_signup_session(mode_choice="1", target_country="mali", msi_client=None, session_num=1, assigned_phone=None):
    print("\n" + "=" * 65)
    print(f"      🚀 STARTING FRESH NOON SIGNUP SESSION #{session_num}")
    print("=" * 65)
    
    # 0. Determine Phone Number
    full_phone = ""
    phone_number = ""
    country_prefix = "+223" if target_country == "mali" else "+20"
    
    if assigned_phone:
        full_phone, phone_number = assigned_phone
        print(f"🔄 [RETRYING EXISTING NUMBER] Keeping: {country_prefix} {phone_number} (Full: {full_phone})")
    elif mode_choice == "1":
        if not msi_client:
            msi_client = MSIApiClient()
            msi_client.login()
            
        c_label = "Mali (+223)" if target_country == "mali" else "Egypt (+20)"
        print(f"[MSI] Fetching next available {c_label} number...")
        full_num, local_num = msi_client.get_next_number(country=target_country)
        if full_num and local_num:
            full_phone = full_num
            phone_number = local_num
            print(f"✅ [MSI] Assigned New {c_label} Number: {country_prefix} {phone_number} (Full: {full_phone})")
        else:
            print(f"❌ [MSI] No unused {c_label} numbers found in account.")
            return ("EXHAUSTED", None, None)
    elif mode_choice == "2":
        phone_number = input(f"\nEnter {target_country.title()} phone number: ").strip()
        code = "223" if target_country == "mali" else "20"
        full_phone = code + phone_number.replace("+", "").lstrip("0")

    email = generate_custom_gmail()
    password = generate_strong_password()
    visitor_id = str(uuid.uuid4())
    
    print(f"Generated Email:  {email}")
    print(f"Password:          {password}")
    print("=" * 65)

    profile_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hybrid_profile")
    
    # 1. Complete cleanup before starting this session
    print("[0] Performing complete browser wipe & clearing all old cookies/cache...")
    cleanup_chrome_and_profile(profile_dir)
    os.makedirs(profile_dir, exist_ok=True)

    CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    chrome_process = None
    playwright_instance = None
    
    try:
        import subprocess
        playwright_instance = sync_playwright().start()
        chrome_port = 9222
        print(f"[1] Starting clean Google Chrome instance on port {chrome_port}...")
        
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
        
        print("[1.5] Connecting Playwright over CDP...")
        browser = None
        for attempt in range(1, 8):
            try:
                browser = playwright_instance.chromium.connect_over_cdp(f"http://localhost:{chrome_port}", timeout=4000)
                if browser:
                    break
            except Exception:
                time.sleep(1)

        if not browser or not browser.contexts:
            print(f"[ERROR] Could not connect to Chrome on port {chrome_port} after retries. Retrying session...")
            return ("RETRY_SAME_NUMBER", full_phone, phone_number)
            
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else context.new_page()
        
        try:
            page.set_viewport_size({'width': 1200, 'height': 800})
        except Exception:
            pass

        print("[2] Loading Noon Portal (Fresh Session)...")
        page.goto("https://account.noon.com/egypt-en/profile/", wait_until="domcontentloaded")
        time.sleep(1)

        # Immediate check for Akamai Access Denied on this VPN IP
        try:
            page_html = page.content().lower()
            if "access denied" in page_html or "edgesuite.net" in page_html or "permission to access" in page_html:
                print("⚠️ [ACCESS DENIED ON VPN IP] Akamai blocked this VPN server IP. Rotating ExpressVPN & retrying...")
                rotate_vpn()
                return ("RETRY_SAME_NUMBER", full_phone, phone_number)
        except Exception:
            pass

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
            print("[ERROR] Could not generate reCAPTCHA token. Rotating VPN & retrying...")
            rotate_vpn()
            return ("RETRY_SAME_NUMBER", full_phone, phone_number)

        print("[4] Sending /auth/sign-in request via API...")
        headers = {
            "content-type": "application/json",
            "x-locale": "en-eg",
            "x-platform": "web",
            "x-visitor-id": visitor_id,
            "origin": "https://account.noon.com",
            "referer": "https://account.noon.com/egypt-en/profile/"
        }
        
        payload_signin = {
            "emailOrPhone": email,
            "recaptcha": {
                "token": token_signin,
                "action": "login",
                "key": RECAPTCHA_KEY
            }
        }

        try:
            resp_signin = session.post(
                "https://account.noon.com/_vs/st/mp-identity-api/auth/sign-in",
                json=payload_signin,
                headers=headers,
                timeout=15
            )
            print(f"    Response Status: {resp_signin.status_code}")
        except Exception as e:
            print(f"[ERROR] Connection to Noon /sign-in failed: {e}. Rotating VPN...")
            rotate_vpn()
            return ("RETRY_SAME_NUMBER", full_phone, phone_number)

        if resp_signin.status_code != 200:
            print(f"⚠️ [RATE LIMIT / BLOCKED DETECTED] Check-in responded with: {resp_signin.text}")
            rotate_vpn()
            return ("RETRY_SAME_NUMBER", full_phone, phone_number)

        print("[5] Generating reCAPTCHA token for signup...")
        token_signup = get_recaptcha_token(page, "login")
        if not token_signup:
            print("[ERROR] Could not generate reCAPTCHA token for registration. Rotating VPN...")
            rotate_vpn()
            return ("RETRY_SAME_NUMBER", full_phone, phone_number)
            
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

        sync_cookies_to_curl(context, session)

        print("[6] Registering account via /auth/sign-in-with-password API...")
        try:
            resp_signup = session.post(
                "https://account.noon.com/_vs/st/mp-identity-api/auth/sign-in-with-password",
                json=payload_signup,
                headers=headers,
                timeout=15
            )
            print(f"    Response Status: {resp_signup.status_code}")
        except Exception as e:
            print(f"[ERROR] Connection to Noon /sign-in-with-password failed: {e}. Rotating VPN...")
            rotate_vpn()
            return ("RETRY_SAME_NUMBER", full_phone, phone_number)
        
        if resp_signup.status_code != 200:
            print(f"⚠️ [RATE LIMIT / BLOCKED DETECTED] Registration failed: {resp_signup.text}")
            rotate_vpn()
            return ("RETRY_SAME_NUMBER", full_phone, phone_number)
            
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

        if target_country == "mali":
            print("    Selecting Mali (+223) in browser UI (human simulation)...")
            try:
                trigger_selectors = [
                    "button.CountryCodeSelect-module-scss-module__wwAlcW__trigger",
                    "button[class*='CountryCodeSelect-module-scss-module__wwAlcW__trigger']"
                ]
                human_click(page, trigger_selectors, timeout=5000)
                time.sleep(1.5)
                
                search_selectors = [
                    "#overlay-portal input[id*='react-select']",
                    "input[id*='react-select']"
                ]
                human_type(page, search_selectors, "mali", timeout=3000)
                time.sleep(1.5)
                
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
            print("    Using Egypt (+20) as country code.")
            
        sms_btn = None
        # Inner loop to try phone numbers within the SAME already-logged-in session
        while True:
            print(f"\n[8] Typing phone number '{phone_number}' in browser UI (human simulation)...")
            try:
                phone_input_selectors = [
                    "input[name='primaryPhone']",
                    "input.PhoneInput-module-scss-module__gXMrQq__input"
                ]
                human_type(page, phone_input_selectors, phone_number, timeout=5000)
                time.sleep(1)
            except Exception as e:
                print(f"    [WARNING] Failed to type phone number in UI: {e}")

            print("    Submitting phone number in browser UI...")
            submit_btn_selectors = [
                'button:has-text("ADD PHONE NUMBER")',
                'button:has-text("Add Phone Number")',
                'button[type="submit"]'
            ]
            human_click(page, submit_btn_selectors, timeout=5000)
            time.sleep(2)

            # Check if Noon returned "Invalid phone number" or error toast
            is_number_invalid = False
            try:
                page_html = page.content().lower()
                if "invalid phone number" in page_html or "invalid_phone_number" in page_html or "phone number is invalid" in page_html or "already registered" in page_html or "already in use" in page_html:
                    is_number_invalid = True
            except Exception:
                pass

            if is_number_invalid:
                print(f"⚠️ [INVALID NUMBER] Noon rejected number: {full_phone} ('Invalid phone number').")
                if msi_client and full_phone:
                    msi_client.mark_number_as_used(full_phone)
                
                # Fetch next number from MSI and retry immediately in the same modal
                if mode_choice == "1" and msi_client:
                    c_label = "Mali (+223)" if target_country == "mali" else "Egypt (+20)"
                    print(f"🔄 Fetching next available {c_label} number from MSI...")
                    next_full, next_local = msi_client.get_next_number(country=target_country)
                    if next_full and next_local:
                        full_phone = next_full
                        phone_number = next_local
                        print(f"➡️ [MSI] Switched to next number: {country_prefix} {phone_number} (Full: {full_phone})")
                        time.sleep(1)
                        continue
                    else:
                        print(f"🏁 [MSI] No more {c_label} numbers available.")
                        return ("EXHAUSTED", None, None)
                else:
                    phone_number = input("\nPhone number invalid. Enter a new number: ").strip()
                    continue

            # Check if SMS button appeared
            sms_btn = page.locator('button:has-text("SMS"):visible, [role="button"]:has-text("SMS"):visible').first
            try:
                sms_btn.wait_for(state="visible", timeout=6000)
                # Success, SMS modal loaded!
                break
            except Exception:
                # If SMS button didn't appear, check if there was an error toast
                page_html = page.content().lower()
                if "invalid" in page_html or "error" in page_html or "phone" in page_html:
                    print(f"⚠️ [REJECTED NUMBER] Noon did not accept number: {full_phone}.")
                    if msi_client and full_phone:
                        msi_client.mark_number_as_used(full_phone)
                    if mode_choice == "1" and msi_client:
                        next_full, next_local = msi_client.get_next_number(country=target_country)
                        if next_full and next_local:
                            full_phone = next_full
                            phone_number = next_local
                            print(f"➡️ [MSI] Trying next number: {country_prefix} {phone_number}...")
                            time.sleep(1)
                            continue
                        else:
                            return ("EXHAUSTED", None, None)
                
                # If it's a rate limit or general block
                print("⚠️ [MODAL BLOCKED / TIMEOUT] Rotating ExpressVPN & retrying...")
                rotate_vpn()
                return ("RETRY_SAME_NUMBER", full_phone, phone_number)

        print("\n[9] Waiting for verification modal & clicking SMS 1 button...")
        try:
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
                sms_btn.click(timeout=5000)
                print("📩 [SUCCESS] Clicked SMS 1 button (SMS 1 Dispatched)!")
            else:
                print(f"⚠️ [SMS DISABLED ON NUMBER] SMS button never enabled for {full_phone} (WhatsApp only / unsupported carrier).")
                if msi_client and full_phone:
                    msi_client.mark_number_as_used(full_phone)
                return ("SKIP_BAD_NUMBER", full_phone, phone_number)
            
            # Wait for SMS 2 cooldown
            print("\n[10] Waiting for SMS 2 button to become enabled (cooldown)...")
            time.sleep(2)  # Initial pause to allow button state to register
            start_time = time.time()
            is_enabled_2 = False
            last_print = 0
            while time.time() - start_time < 45:
                disabled_prop = sms_btn.is_disabled()
                aria_disabled = sms_btn.get_attribute("aria-disabled")
                
                if not disabled_prop and aria_disabled != "true":
                    is_enabled_2 = True
                    break
                    
                if time.time() - last_print > 3:
                    print(f"      [Status] disabled={disabled_prop}, aria-disabled={aria_disabled}")
                    last_print = time.time()
                    
                time.sleep(0.5)
                
            if is_enabled_2:
                print(f"    SMS 2 button became enabled after {int(time.time() - start_time)} seconds.")
                sms_btn.click(timeout=5000)
                print("📩 [SUCCESS] Clicked SMS 2 button (SMS 2 Dispatched)! [COMPLETED 2/2 SMS]")
            else:
                print(f"⚠️ [SMS 2 BUTTON TIMEOUT] SMS 2 button never enabled for {full_phone}.")
                if msi_client and full_phone:
                    msi_client.mark_number_as_used(full_phone)
                return ("SKIP_BAD_NUMBER", full_phone, phone_number)
            
            # Mark number as used only after both SMS succeed
            if msi_client and full_phone:
                msi_client.mark_number_as_used(full_phone)
            save_account_record(email, password, full_phone)
            
            time.sleep(1.5)
            return ("SUCCESS", full_phone, phone_number)
            
        except Exception as err:
            print(f"[WARNING] Modal or SMS click issue: {err}. Rotating VPN and retrying same number...")
            rotate_vpn()
            return ("RETRY_SAME_NUMBER", full_phone, phone_number)

    finally:
        try:
            if context:
                context.close()
        except Exception:
            pass
        if chrome_process:
            try:
                chrome_process.terminate()
            except Exception:
                pass
        if playwright_instance:
            try:
                playwright_instance.stop()
            except Exception:
                pass
                
        # Final full cleanup after session finishes
        cleanup_chrome_and_profile(profile_dir)

def main():
    print("=" * 65)
    print("        NOON EGYPT HYBRID AUTOMATION (EXPRESSVPN + MSI)")
    print("=" * 65)
    
    print(">>> SELECT PHONE NUMBER SOURCE:")
    print(">>> 1. 🤖 Automatic from MSI Portal [Default]")
    print(">>> 2. ✍️  Manual Number Entry")
    print("=" * 65)
    
    mode_choice = input("Select mode (1 or 2, default 1): ").strip() or "1"
    
    print("\n" + "=" * 65)
    print(">>> SELECT TARGET COUNTRY:")
    print(">>> 1. 🇲🇱 Mali (+223) [Default]")
    print(">>> 2. 🇪🇬 Egypt (+20)")
    print("=" * 65)
    
    country_choice = input("Select country (1 or 2, default 1): ").strip() or "1"
    target_country = "mali" if country_choice == "1" else "egypt"
    country_display = "Mali (+223)" if target_country == "mali" else "Egypt (+20)"
    
    msi_client = None
    if mode_choice == "1":
        print("\n[MSI] Connecting to MSI SMS API client...")
        msi_client = MSIApiClient()
        if msi_client.login():
            all_numbers = msi_client.get_my_numbers(limit=500)
            if target_country == "mali":
                filtered_nums = [n for n in all_numbers if "mali" in str(n.get("range", "")).lower() or str(n.get("prefix", "")) == "223" or str(n.get("number", "")).startswith("223")]
            else:
                filtered_nums = [n for n in all_numbers if "egypt" in str(n.get("range", "")).lower() or str(n.get("prefix", "")) == "20" or str(n.get("number", "")).startswith("20")]
            
            used = set()
            if os.path.exists("used_numbers.txt"):
                try:
                    with open("used_numbers.txt", "r", encoding="utf-8") as f:
                        used = set(l.strip() for l in f if l.strip())
                except Exception:
                    pass
                    
            unused_count = sum(1 for n in filtered_nums if str(n.get("number", "")).replace("+", "").strip() not in used)
            print(f"📊 [MSI] Total {country_display} Numbers in Account: {len(filtered_nums)} | Remaining Unused: {unused_count}")
        else:
            print("[WARNING] MSI login failed. Will fall back to manual mode.")
            mode_choice = "2"
            
    print("\n" + "=" * 65)
    total_accounts_input = input("How many accounts to create? (Enter number, or press ENTER to process ALL remaining numbers): ").strip()
    print("=" * 65)
    
    if not total_accounts_input:
        target_count = 999999  # Process all remaining numbers until exhausted
        print(f"🚀 Mode: Processing ALL remaining unused {country_display} numbers until exhaustion...")
    else:
        try:
            target_count = int(total_accounts_input)
        except ValueError:
            target_count = 999999
    
    created = 0
    session_idx = 1
    current_phone = None  # Holds (full_num, local_num) to retry if rate limit occurs
    
    while session_idx <= target_count:
        status, full_p, local_p = run_single_signup_session(
            mode_choice=mode_choice,
            target_country=target_country,
            msi_client=msi_client,
            session_num=session_idx,
            assigned_phone=current_phone
        )
        
        if status == "SUCCESS":
            created += 1
            print(f"\n✅ Successfully completed 2 SMS for account #{session_idx} on number {full_p}. (Total completed: {created})")
            current_phone = None  # Reset to fetch next number
            session_idx += 1
        elif status == "SKIP_BAD_NUMBER":
            print(f"\n⏭️ [SKIPPED BAD NUMBER] Skipped number {full_p} (SMS disabled/unsupported). Proceeding to next number from MSI...")
            current_phone = None  # Reset to fetch next fresh number from MSI!
        elif status == "RETRY_SAME_NUMBER":
            print(f"\n🔁 [RETRY] Re-attempting session for the SAME number {full_p} on a fresh VPN IP...")
            current_phone = (full_p, local_p)
            # Do not increment session_idx so it retries the same account target
        elif status == "EXHAUSTED":
            print(f"\n🏁 [MSI] All available {country_display} numbers have been processed and exhausted!")
            break
        else:
            print(f"\n⚠️ Session #{session_idx} ended with error. Moving to next number...")
            current_phone = None
            session_idx += 1
            
        if session_idx <= target_count and status != "EXHAUSTED":
            print("\n⏳ Cooldown: Waiting 4 seconds before starting next session...")
            time.sleep(4)
            
    print(f"\n🎉 All operations completed! Total numbers successfully processed: {created}")

if __name__ == "__main__":
    main()



