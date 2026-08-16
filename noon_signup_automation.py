import os
import random
import string
import sys
import time
from playwright.sync_api import sync_playwright


# List of common names to generate realistic emails
NAMES_LIST = [
    "ahmed", "mohamed", "mahmoud", "mostafa", "kareem", 
    "tarek", "hassan", "hossam", "omar", "sayed", 
    "ali", "ibrahim", "salem", "amr", "sherif", "khaled",
    "youssef", "samir", "ramy", "tamer", "hany", "nabil"
]

def generate_custom_gmail():
    """
    Generate Gmail according to specified pattern:
    Name1 + random_char + random_digit + Name2 + 4_random_digits + @gmail.com
    Example: amri3mohamed7147@gmail.com
    """
    name1 = random.choice(NAMES_LIST)
    name2 = random.choice(NAMES_LIST)
    mid_char = random.choice(string.ascii_lowercase)
    mid_digit = str(random.randint(0, 9))
    four_digits = "".join(random.choices(string.digits, k=4))
    
    email = f"{name1}{mid_char}{mid_digit}{name2}{four_digits}@gmail.com"
    return email

def generate_strong_password():
    """Password compliant with Noon security requirements"""
    return "01223456menA@"

def fill_instant(locator, text):
    """Fill text into field all at once instantly"""
    try:
        locator.click()
        locator.fill("")
        locator.fill(text)
    except Exception:
        try:
            locator.fill(text)
        except Exception:
            pass


def human_wait(min_ms=2000, max_ms=2000):
    """Fixed 2 second wait between actions"""
    time.sleep(random.uniform(min_ms, max_ms) / 1000)


def console_input(prompt):
    """Print to original terminal stdout and read from original stdin"""
    import sys
    sys.__stdout__.write(prompt)
    sys.__stdout__.flush()
    return sys.__stdin__.readline()


def safe_click(page, selectors, timeout=3000, force=False):
    """Try each selector with 3s timeout, click as soon as one is visible"""
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            loc.wait_for(state="visible", timeout=timeout)
            loc.click(force=force)
            return True
        except Exception:
            continue
    return False

def safe_fill(page, selectors, value, timeout=3000):
    """Try each selector with 3s timeout, fill as soon as one is visible"""
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            loc.wait_for(state="visible", timeout=timeout)
            fill_instant(loc, value)
            return True
        except Exception:
            continue
    return False


def run_signup_process(playwright, target_url="https://account.noon.com/egypt-en/profile/", phone_number="", thread_id=1):
    email = generate_custom_gmail()
    password = generate_strong_password()
    
    print("\n" + "="*60)
    print("Starting new clean session for Noon account creation...")
    print(f"Generated Email: {email}")
    print(f"Password:        {password}")
    print("="*60 + "\n")

    # Use a persistent profile directory local to the workspace to build trust/cookies
    import os
    profile_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"noon_profile_pw_{thread_id}")
    os.makedirs(profile_dir, exist_ok=True)

    CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

    # Use launch_persistent_context for a real fresh browser profile (not incognito)
    context = playwright.chromium.launch_persistent_context(
        user_data_dir=profile_dir,
        executable_path=CHROME_PATH,
        headless=False,
        ignore_default_args=['--enable-automation', '--no-sandbox'],
        args=[
            '--disable-cache',
            '--disk-cache-size=0',
            '--disable-extensions',
            '--disable-translate',
            '--disable-features=Translate,TranslateUI,BraveTranslate',
            '--lang=en-US',
            '--accept-lang=en-US,en'
        ],
        viewport={'width': 1100, 'height': 750},
        locale='en-US',
        timezone_id='Africa/Cairo',
        extra_http_headers={'Accept-Language': 'en-US,en;q=0.9'},
    )
    browser = None  # persistent context has no separate browser object

    
    # Anti-bot detection stealth bypass overrides
    context.add_init_script("""
        // Hide navigator.webdriver
        Object.defineProperty(navigator, 'webdriver', { get: () => false });
        
        // Mock Chrome runtime & plugins
        window.chrome = {
            runtime: {},
            loadTimes: function() {},
            csi: function() {},
            app: {}
        };
        Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
        Object.defineProperty(navigator, 'language', { get: () => 'en-US' });
        Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
        
        // Hide automation styles and translate bars
        window.addEventListener('DOMContentLoaded', () => {
            const style = document.createElement('style');
            style.innerHTML = `
                .goog-te-banner-frame, 
                #goog-gt-tt, 
                .skiptranslate, 
                #translateBar,
                iframe[id*="translate"],
                div[class*="translateBar"],
                div[id*="translateBar"] { 
                    display: none !important; 
                    visibility: hidden !important; 
                    height: 0 !important;
                } 
                body { top: 0px !important; }
            `;
            (document.head || document.documentElement).appendChild(style);
        });
    """)

    page = context.new_page()

    
    # Clear cache and cookies via CDP
    try:
        cdp = context.new_cdp_session(page)
        cdp.send('Network.clearBrowserCache')
        cdp.send('Network.clearBrowserCookies')
    except Exception:
        pass

    try:
        # 1. Navigate directly to Profile page
        print(f"1. Navigating to profile page: {target_url}")
        page.goto(target_url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(500)
        
        # 2. Click Login / Signup button on Profile page
        print("2. Clicking Login/Signup button...")
        login_signup_selectors = [
            # Exact from new Recording
            'text="Login/Signup"',
            'text="LOGIN/SIGNUP"',
            'div.layout-module-scss-module__-MERqq__mainLayout span',
            'xpath=//html/body/div[2]/div/main/div/div/div[2]/button/span',
            # Fallbacks
            'button:has-text("Login")',
            'span:has-text("Login")',
            'div[title="Log in"]',
            'button[data-qa="btn_header_signInOrUp-header-desktop"]',
        ]
        
        if safe_click(page, login_signup_selectors, timeout=5000):
            print("SUCCESS: Clicked Login/Signup button.")
        else:
            print("INFO: Login/Signup button not found or modal already open.")

        human_wait(200, 400)


        
        # 3. Click Sign Up
        print("3. Waiting for and clicking Sign Up...")
        signup_link_selectors = [
            # Exact from Recording: data-qa='sign-up'
            '[data-qa="sign-up"]',
            'aria/Sign up',
            'text="Sign up"',
            'text="Sign Up"',
            # Fallbacks
            '[data-qa="Register-now"]',
            '[data-qa="اشترك-الآن"]',
            'button:has-text("Sign up")',
            'span:has-text("Sign up")',
        ]
        if safe_click(page, signup_link_selectors, timeout=2000):
            print("SUCCESS: Clicked Sign Up.")
        else:
            print("WARNING: Sign Up button not found or not visible.")
            
        human_wait(200, 400)
        
        # 4. Fill Email
        print(f"4. Waiting for email field and typing: {email}")
        email_field = None
        email_selectors = [
            # Exact ID & attributes from actual HTML
            '#emailInput',
            'input#emailInput',
            'input[aria-label="Email address"]',
            'input[placeholder*="enter email"]',
            'input[placeholder*="Email"]',
            'input[type="text"]#emailInput',
            'input[type="email"]',
            '[data-qa="lbl_value_"] input',
            'input[name="email"]',
            '#overlay-portal input',
            'div[role="dialog"] input'
        ]

        
        email_field_found = False
        for sel in email_selectors:
            try:
                loc = page.locator(sel).first
                loc.wait_for(state="visible", timeout=3000)
                fill_instant(loc, email)
                email_field = loc
                email_field_found = True
                break
            except Exception:
                continue

        if email_field_found:
            print("SUCCESS: Email entered successfully.")
        else:
            print("WARNING: Email field was not found on screen.")

        human_wait(200, 400)
        
        # 4.5. Click Continue button
        print("4.5. Waiting for and clicking Continue button...")
        continue_btn_selectors = [
            # Exact from Recording
            'div._modalContent_15ecu_45 span',
            'xpath=//*[@data-qa="btn_Continue"]/span',
            '[data-qa="btn_Continue"]',
            'text="Continue"',
            # Fallbacks
            'div.SigninV2-module-scss-module__HeoDSq__modalContent span',
            '#login-submit',
            'button#login-submit',
            'button:has-text("Continue")',
            'span:has-text("Continue")',
            'button:has-text("متابعة")',
            'text="متابعة"'
        ]
        
        clicked_continue = safe_click(page, continue_btn_selectors, timeout=3000, force=True)
        
        if email_field:
            try:
                email_field.press("Enter")
            except Exception:
                pass
        else:
            try:
                page.keyboard.press("Enter")
            except Exception:
                pass

        if clicked_continue:
            print("SUCCESS: Clicked Continue button.")
        else:
            print("INFO: Submitted email via Enter key.")

        human_wait(500, 1000)


        
        # 5. Click Register with Password
        print("5. Waiting for 'Sign up using password' button...")
        pass_mode_selectors = [
            # Exact from Recording
            'button._signinWithPasswordBtn_1dxqd_183 > p',
            'button._signinWithPasswordBtn_1dxqd_183',
            'text="Sign up using password"',
            'text="Sign in with Password"',
            'text="Register with Password"',
            'p:has-text("Sign up using")',
            'button:has-text("Password")',
            'text="سجل باستخدام كلمة المرور"',
        ]
        if safe_click(page, pass_mode_selectors, timeout=2000, force=True):
            print("SUCCESS: Selected 'Sign up using password'.")
        else:
            print("INFO: Password choice button not shown or already in password view.")

        human_wait(300, 500)

        # 6. Fill new password and password confirmation
        print("6. Waiting for password fields...")
        pass_filled = False

        # Wait for password fields to appear (simple loop)
        pass_selectors = [
            'input[type="password"]',
            'form > div:nth-of-type(2) [data-qa="lbl_value_"]',
        ]
        for sel in pass_selectors:
            try:
                loc = page.locator(sel).first
                loc.wait_for(state="visible", timeout=5000)
                # Found a password field - now count how many there are
                all_pass = page.locator('input[type="password"]')
                count = all_pass.count()
                if count >= 2:
                    fill_instant(all_pass.nth(0), password)
                    human_wait()
                    fill_instant(all_pass.nth(1), password)
                    pass_filled = True
                elif count == 1:
                    fill_instant(all_pass.nth(0), password)
                    page.keyboard.press("Tab")
                    human_wait()
                    # Second field may appear after Tab
                    try:
                        conf = page.locator('input[type="password"]').nth(1)
                        conf.wait_for(state="visible", timeout=3000)
                        fill_instant(conf, password)
                        pass_filled = True
                    except Exception:
                        pass_filled = True  # single field, try submitting
                break
            except Exception:
                continue

        if pass_filled:
            print("SUCCESS: Password and confirmation entered.")
        else:
            print("WARNING: Could not find password fields - skipping submit.")

        human_wait()

        # 7. Submit registration form (SIGN UP) - only if password was filled
        if pass_filled:
            print("7. Waiting for SIGN UP submit button...")
            submit_btn_selectors = [
                'xpath=//*[@id="overlay-portal"]/div/div[2]/div/div[2]/div/div[2]/form/button/p',
                '#overlay-portal form button[type="submit"] p',
                '#overlay-portal form button[type="submit"]',
                'aria/SIGN UP',
                'button[type="submit"]'
            ]
            if safe_click(page, submit_btn_selectors, timeout=3000, force=True):
                print("SUCCESS: Clicked SIGN UP button.")
            else:
                print("INFO: Form submitted via Enter key.")
        else:
            print("7. SKIPPED submit - password was not filled.")

        human_wait()

        # 8. Handle confirmation modal if present
        print("8. Checking for confirmation modal...")
        confirm_btn_selectors = [
            # Exact from Recording
            '#overlay-portal button:nth-of-type(2)',
            'aria/Confirm',
            'button:has-text("Confirm")',
            '#overlay-portal button:has-text("Confirm")',
            'button:has-text("تأكيد")',
        ]
        safe_click(page, confirm_btn_selectors, timeout=2000, force=True)
        human_wait(400, 700)

        # 9. Already on profile page after signup confirmation, wait for Add button directly



        # 10. Click Add button on profile page
        print("10. Waiting for Add button on Profile page...")
        add_btn_selectors = [
            'div[class*="hasAddAction"]',
            'div[class*="hasAddAction"] span',
            'div[class*="editPhoneInputCtr"] span:has-text("Add")',
            'img[alt="plus-blue"] + span',
            'img[alt="plus-blue"]',
            'span:has-text("Add")',
            'button:has-text("Add")',
            'text="Add"',
        ]
        if safe_click(page, add_btn_selectors, timeout=8000):
            print("SUCCESS: Clicked Add button on Profile page.")
            human_wait(800, 1200)

            # Step 11: Open phone modal and let user type manually
            print("11. Waiting for phone input modal...")
            phone_input_selectors = [
                'div.PhoneInput-module-scss-module__gXMrQq__inputContainer > input',
                '#overlay-portal input[type="tel"]',
                '#overlay-portal input[type="text"]',
                '#overlay-portal input',
                'input[placeholder*="phone"]',
                'input[placeholder*="Phone"]',
            ]

            phone_focused = False
            for sel in phone_input_selectors:
                try:
                    loc = page.locator(sel).first
                    if loc.is_visible(timeout=4000):
                        loc.click()
                        phone_focused = True
                        print("SUCCESS: Phone input focused. Type your number in the browser.")
                        break
                except Exception:
                    continue

            if phone_focused:
                console_input("\n>>> Type phone number in browser, then press ENTER here to submit...")

                human_wait(300, 500)

                # Step 12: Click Save/Send button to trigger SMS
                print("12. Clicking Save/Send button to trigger SMS...")
                sms_submit_selectors = [
                    '#overlay-portal button:has-text("Save")',
                    '#overlay-portal button:has-text("Send")',
                    '#overlay-portal button:has-text("Verification")',
                    '#overlay-portal button:has-text("حفظ")',
                    '#overlay-portal button:has-text("إرسال")',
                    '#overlay-portal button[type="submit"]',
                    '#overlay-portal form button[type="submit"]',
                    '#overlay-portal form button',
                ]

                clicked_sms = False
                for sel in sms_submit_selectors:
                    try:
                        loc = page.locator(sel).first
                        loc.wait_for(state="visible", timeout=2000)
                        if loc.is_visible():
                            print(f"  Found button matching: {sel}")
                            
                            # Wait up to 10 seconds for the button to become enabled
                            is_enabled = False
                            for _ in range(20):
                                if not loc.is_disabled() and loc.get_attribute("aria-disabled") != "true":
                                    is_enabled = True
                                    break
                                time.sleep(0.5)
                                
                            if not is_enabled:
                                print("  WARNING: Button is still disabled after timeout. Attempting click anyway...")
                            
                            # Attempt normal click first
                            try:
                                loc.click(timeout=3000)
                            except Exception:
                                # Fallback to forced click
                                loc.click(force=True)
                                
                            clicked_sms = True
                            break
                    except Exception:
                        continue
                        
                saved = False
                if clicked_sms:
                    print("SUCCESS: Submitted phone number - SMS should be sent!")
                    saved = True
                else:
                    try:
                        page.keyboard.press("Enter")
                        print("INFO: Pressed Enter to submit phone number.")
                        saved = True
                    except Exception:
                        pass

                # Step 13: Select SMS option in verification modal
                if saved:
                    print("13. Checking for verification modal...")
                    try:
                        # Wait for modal text
                        page.wait_for_selector('text=Verify your account', timeout=10000)
                        print("  INFO: Verification modal detected.")
                        
                        sms_button = page.locator('button:has-text("SMS"), [role="button"]:has-text("SMS")').last
                        if sms_button.is_visible():
                            sms_button.click(force=True)
                            print("  [OK] Clicked SMS button in modal!")
                        else:
                            sms_element = page.locator('div:has-text("SMS"), span:has-text("SMS")').last
                            if sms_element.is_visible():
                                sms_element.click(force=True)
                                print("  [OK] Clicked SMS element in modal!")
                            else:
                                print("  WARNING: SMS button not visible in modal.")
                    except Exception as modal_err:
                        print(f"  INFO: Verification modal not detected or SMS click failed: {modal_err}")
            else:
                print("WARNING: Phone input field not found in modal.")
        else:
            print("INFO: Add button not found.")

        print("\nAll registration steps completed!")
        print(f"Account Credentials:\n - Email:    {email}\n - Password: {password}\n")




    except Exception as e:
        print(f"Error during execution: {e}")

    return context, page, profile_dir


import threading
_print_lock = threading.Lock()

def tprint(thread_id, msg):
    """Thread-safe terminal print with prefix"""
    with _print_lock:
        print(f"[T{thread_id}] {msg}", flush=True)

def run_in_thread(thread_id, url, phone_number, results):
    """Run signup process in its own thread with its own Playwright instance"""
    from playwright.sync_api import sync_playwright as _sync_playwright
    import io, sys

    log_path = f"thread_{thread_id}.log"
    tprint(thread_id, f"Starting... (log -> {log_path})")

    # Redirect this thread's stdout to a file
    old_stdout = sys.stdout
    log_file = open(log_path, "w", encoding="utf-8", buffering=1)

    try:
        with _sync_playwright() as pw:
            # Temporarily redirect print to log file
            sys.stdout = log_file
            context, page, profile_dir = run_signup_process(pw, url, phone_number=phone_number, thread_id=thread_id)
            sys.stdout = old_stdout

            email_line = [l for l in open(log_path, encoding='utf-8') if 'Email:' in l]
            if email_line:
                tprint(thread_id, email_line[-1].strip())

            results[thread_id] = "done"
            tprint(thread_id, "Done! Press Enter in this terminal to close this browser.")
            input()
            page.close()
            context.close()
            # Clean up temp profile directory (disabled to persist profile)
            # try:
            #     import shutil
            #     shutil.rmtree(profile_dir, ignore_errors=True)
            # except Exception:
            #     pass
            tprint(thread_id, "Browser closed.")
    except Exception as e:
        sys.stdout = old_stdout
        tprint(thread_id, f"ERROR: {e}")
        results[thread_id] = f"error: {e}"
    finally:
        log_file.close()


def main():
    print("==================================================")
    print("     Noon Egypt Account Creation Automation      ")
    print("==================================================")

    while True:
        try:
            n = int(input("\nHow many parallel browsers to open? (1-5): ").strip())
            n = max(1, min(n, 5))
        except ValueError:
            n = 1

        import threading
        url = "https://account.noon.com/egypt-en/profile/"

        results = {}
        threads = []

        for i in range(1, n + 1):
            t = threading.Thread(target=run_in_thread, args=(i, url, "", results), daemon=True)
            threads.append(t)
            t.start()
            import time as _time
            _time.sleep(3)  # stagger 3 seconds between each browser start

        # Wait for all threads to finish
        for t in threads:
            t.join()

        print("\nAll browsers closed.")
        ans = input("Start another batch? (Enter = yes, 'exit' = quit): ").strip().lower()
        if ans in ['exit', 'x', 'quit', 'q']:
            print("Automation finished. Have a great day!")
            break

if __name__ == "__main__":
    main()
