"""
Outlier Bet Phone Login Automation Script
Automates:
1. Navigating to https://app.outlier.bet/login
2. Clicking "Use phone instead"
3. Selecting Country (United Kingdom +44 or custom)
4. Focusing and filling phone number field
"""
import random
import string
import time
from playwright.sync_api import sync_playwright

def human_type(locator, text, min_delay=15, max_delay=40):
    """Fill text into field instantly or character-by-character if required"""
    try:
        locator.click()
        locator.fill("")
        locator.fill(text)
    except Exception:
        try:
            locator.fill(text)
        except Exception:
            pass

def human_wait(min_ms=300, max_ms=800):
    """Fast natural hesitation between actions"""
    time.sleep(random.uniform(min_ms, max_ms) / 1000)

def safe_click(page, selectors, timeout=5000, force=False):
    """Try selectors sequentially and click as soon as visible"""
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            loc.wait_for(state="visible", timeout=timeout)
            loc.click(force=force)
            return True
        except Exception:
            continue
    return False

def run_outlier_login(playwright, country_name="United Kingdom", phone_number=""):
    print("\n" + "="*60)
    print("  Starting Outlier Bet Login Automation Session  ")
    print(f"  Target Country: {country_name}")
    print("="*60 + "\n")

    BRAVE_PATH = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
    browser = playwright.chromium.launch(
        executable_path=BRAVE_PATH,
        headless=False,
        ignore_default_args=['--enable-automation'],
        args=[
            '--incognito',
            '--disable-cache',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-extensions',
            '--disable-blink-features=AutomationControlled',
            '--lang=en-US',
        ]
    )

    context = browser.new_context(
        viewport={'width': 1280, 'height': 800},
        locale='en-US',
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    )

    context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        delete Object.getPrototypeOf(navigator).webdriver;
        window.chrome = { runtime: {} };
    """)

    page = context.new_page()

    try:
        # 1. Navigate to Outlier login page
        print("1. Navigating to https://app.outlier.bet/login ...")
        page.goto("https://app.outlier.bet/login", wait_until="domcontentloaded", timeout=60000)
        human_wait(500, 1000)

        # 2. Click "Use phone instead"
        print("2. Clicking 'Use phone instead' button...")
        use_phone_selectors = [
            'aria/Use phone instead',
            'text="Use phone instead"',
            'button:has-text("Use phone instead")',
            'div.px-16px > div:nth-of-type(2) > button',
            'xpath=//*[@id="root"]/div[1]/div/div[1]/div[2]/button'
        ]
        if safe_click(page, use_phone_selectors, timeout=8000):
            print("SUCCESS: Clicked 'Use phone instead'.")
        else:
            print("INFO: 'Use phone instead' button not found or already on phone view.")

        human_wait(300, 600)

        # 3. Click Country Selector Dropdown
        print(f"3. Opening Country selector dropdown...")
        country_dropdown_selectors = [
            'form > div.flex svg',
            'button[role="combobox"]',
            'xpath=//*[@id="root"]/div[1]/div/div[1]/div[2]/form/div[1]/div/div/button',
            'form div.flex button'
        ]
        safe_click(page, country_dropdown_selectors, timeout=5000)
        human_wait(200, 400)

        # 4. Search and Select Country
        print("4. Searching for country: typing 'un' ...")
        search_input_selectors = [
            'div[role="listbox"] input',
            'input.h-44px',
            'div[role="listbox"] input[class*="grow"]',
            'input[role="textbox"]',
        ]
        
        search_loc = None
        for sel in search_input_selectors:
            try:
                loc = page.locator(sel).first
                if loc.is_visible(timeout=2000):
                    loc.click()
                    loc.fill("")
                    loc.type("un", delay=40)
                    search_loc = loc
                    break
            except Exception:
                continue

        human_wait(300, 600)

        # Click the exact country option div from HTML
        country_item_selectors = [
            f'div[role="option"]:has-text("{country_name}")',
            'div[role="option"]:has-text("+44")',
            'div[role="option"].bg-brand-10',
            'div[role="option"].text-brand-50p',
            'div[role="listbox"] div[role="option"]',
            f'text="{country_name}"'
        ]
        
        clicked_country = safe_click(page, country_item_selectors, timeout=4000, force=True)
        
        # If click failed, press Enter on the search input
        if not clicked_country and search_loc:
            try:
                search_loc.press("Enter")
                clicked_country = True
            except Exception:
                pass

        if clicked_country:
            print(f"SUCCESS: Selected country '{country_name}'.")
        else:
            print("WARNING: Could not click country option.")

        human_wait(300, 600)


        # 5. Focus & Enter Phone Number
        print("5. Focusing Phone Number input field...")
        phone_input_selectors = [
            'input[placeholder*="phone"]',
            'aria/Enter your phone',
            'form input[type="tel"]',
            'form input[type="text"]',
            'xpath=//*[@id=":r1:"]'
        ]
        for sel in phone_input_selectors:
            try:
                loc = page.locator(sel).first
                if loc.is_visible(timeout=3000):
                    loc.click()
                    if phone_number:
                        human_type(loc, phone_number)
                        print(f"SUCCESS: Entered phone number: {phone_number}")
                    else:
                        print("SUCCESS: Phone field focused. Ready for phone input.")
                    break
            except Exception:
                continue

        human_wait(300, 600)

        # 6. Click "Continue with phone" submit button
        print("6. Clicking 'Continue with phone' submit button...")
        submit_btn_selectors = [
            'button[type="submit"]:has-text("Continue with phone")',
            'button.btn-48-brand',
            'button:has-text("Continue with phone")',
            'button[type="submit"]',
            'form button'
        ]
        if safe_click(page, submit_btn_selectors, timeout=5000, force=True):
            print("SUCCESS: Clicked 'Continue with phone' button.")
        else:
            print("INFO: Submit button not found.")

        human_wait(500, 1000)

        # 7. Wait for confirmation code screen & click 'Resend code' 4 times
        print("\n7. Waiting for confirmation code screen & 'Resend code' button...")
        resend_btn_selectors = [
            'button:has-text("Resend code")',
            'button.bg-lvl-1:has-text("Resend code")',
            'button:has-text("Resend")',
        ]

        resend_count = 0
        max_resends = 4

        for iteration in range(1, max_resends + 1):
            print(f"   Waiting for Resend button ({iteration}/{max_resends})...")
            # Wait for resend button to become visible (cooldown up to 45s)
            clicked = safe_click(page, resend_btn_selectors, timeout=45000, force=True)
            if clicked:
                resend_count += 1
                print(f"   SUCCESS [{iteration}/{max_resends}]: Clicked 'Resend code'.")
                # Check for "Code resent" text confirmation
                try:
                    page.locator('text="Code resent"').first.wait_for(state="visible", timeout=5000)
                    print(f"   Verified: 'Code resent' message appeared.")
                except Exception:
                    pass
                human_wait(1000, 2000)
            else:
                print(f"   WARNING [{iteration}/{max_resends}]: Resend button did not appear or timed out.")
                break

        print(f"\nAll Outlier login & 4x Resend code steps completed! Total resends: {resend_count}/{max_resends}")


    except Exception as e:
        print(f"Error during execution: {e}")

    return browser, context, page

import threading
_print_lock = threading.Lock()

def tprint(thread_id, msg):
    """Thread-safe terminal print with prefix"""
    with _print_lock:
        print(f"[Thread-{thread_id}] {msg}", flush=True)

def run_in_thread(thread_id, country_name, phone_number, results):
    """Run Outlier login process in its own thread with its own Playwright instance"""
    from playwright.sync_api import sync_playwright as _sync_playwright
    import sys

    log_path = f"outlier_thread_{thread_id}.log"
    tprint(thread_id, f"Starting... (log -> {log_path})")

    old_stdout = sys.stdout
    log_file = open(log_path, "w", encoding="utf-8", buffering=1)

    try:
        with _sync_playwright() as pw:
            sys.stdout = log_file
            browser, context, page = run_outlier_login(pw, country_name=country_name, phone_number=phone_number)
            sys.stdout = old_stdout

            results[thread_id] = "done"
            tprint(thread_id, "Completed steps! Press Enter in terminal to close this browser.")
            input()
            page.close()
            context.close()
            browser.close()
            tprint(thread_id, "Browser closed.")
    except Exception as e:
        sys.stdout = old_stdout
        tprint(thread_id, f"ERROR: {e}")
        results[thread_id] = f"error: {e}"
    finally:
        log_file.close()

def main():
    print("==================================================")
    print("       Outlier Bet Phone Login Automation         ")
    print("==================================================")

    while True:
        try:
            n = int(input("\nHow many parallel browsers/threads to open? (1-5): ").strip())
            n = max(1, min(n, 5))
        except ValueError:
            n = 1

        phone_inputs = []
        for i in range(1, n + 1):
            p = input(f"Enter phone number for Thread-{i} (or press Enter to leave empty): ").strip()
            if p.startswith('&') or 'python' in p.lower() or 'outlier' in p.lower():
                p = ""
            phone_inputs.append(p)

        print(f"\nLaunching {n} parallel threads...\n")
        results = {}
        threads = []

        for i in range(1, n + 1):
            t = threading.Thread(target=run_in_thread, args=(i, "United Kingdom", phone_inputs[i-1], results), daemon=True)
            threads.append(t)
            t.start()
            time.sleep(2)  # stagger starts by 2 seconds

        for t in threads:
            t.join()

        print("\nAll thread browsers finished.")
        ans = input("Start another batch? (Enter = yes, 'exit' = quit): ").strip().lower()
        if ans in ['exit', 'x', 'quit', 'q']:
            print("Exiting Outlier Bet Automation. Goodbye!")
            break

if __name__ == "__main__":
    main()


