import os
import random
import string
import sys
import time
import threading
import shutil
import tempfile

# ─────────────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────────────
NAMES_LIST = [
    "ahmed", "mohamed", "mahmoud", "mostafa", "kareem",
    "tarek", "hassan", "hossam", "omar", "sayed",
    "ali", "ibrahim", "salem", "amr", "sherif", "khaled",
    "youssef", "samir", "ramy", "tamer", "hany", "nabil"
]

def generate_custom_gmail():
    name1     = random.choice(NAMES_LIST)
    name2     = random.choice(NAMES_LIST)
    mid_char  = random.choice(string.ascii_lowercase)
    mid_digit = str(random.randint(0, 9))
    suffix    = "".join(random.choices(string.digits, k=4))
    return f"{name1}{mid_char}{mid_digit}{name2}{suffix}@gmail.com"

def generate_strong_password():
    return "01223456menA@"

def console_input(prompt):
    """Print to original terminal stdout and read from original stdin"""
    import sys
    sys.__stdout__.write(prompt)
    sys.__stdout__.flush()
    return sys.__stdin__.readline()


def human_wait(min_ms=1800, max_ms=2400):
    time.sleep(random.uniform(min_ms, max_ms) / 1000)

def slow_type(ele, text, delay=0.04):
    """Type text character by character to mimic human speed"""
    ele.clear()
    for ch in text:
        ele.input(ch, clear=False)
        time.sleep(delay + random.uniform(0, 0.03))

def dp_click(page, selectors, timeout=8, desc="element"):
    """Try each CSS selector, click the first visible one."""
    for sel in selectors:
        try:
            ele = page.ele(f"css:{sel}", timeout=timeout)
            if ele:
                ele.click()
                print(f"  [OK] Clicked: {desc}")
                return True
        except Exception:
            continue
    print(f"  [FAIL] Not found: {desc}")
    return False

def dp_fill(page, selectors, value, timeout=8, desc="field"):
    """Try each CSS selector, fill the first visible one."""
    for sel in selectors:
        try:
            ele = page.ele(f"css:{sel}", timeout=timeout)
            if ele:
                slow_type(ele, value)
                print(f"  [OK] Filled: {desc}")
                return True
        except Exception:
            continue
    print(f"  [FAIL] Not found: {desc}")
    return False

# -----------------------------------------------------------------
#  MAIN SIGNUP PROCESS
# -----------------------------------------------------------------
def run_signup_process(port, phone_number=""):
    from DrissionPage import ChromiumPage, ChromiumOptions

    email    = generate_custom_gmail()
    password = generate_strong_password()

    print("\n" + "="*60)
    print(f"  Email:    {email}")
    print(f"  Password: {password}")
    print("="*60 + "\n")

    # ── Browser options ──────────────────────────────────────────
    co = ChromiumOptions()
    co.set_local_port(port)
    co.set_argument("--lang=en-US")
    co.set_argument("--disable-features=Translate,TranslateUI,BraveTranslate")
    co.set_argument("--accept-lang=en-US,en")

    # Use Google Chrome explicitly
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    if os.path.exists(chrome_path):
        co.set_browser_path(chrome_path)

    # Use a persistent profile directory local to the workspace to build trust/cookies
    profile_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"noon_profile_dp_{port}")
    os.makedirs(profile_dir, exist_ok=True)
    co.set_user_data_path(profile_dir)

    page = ChromiumPage(co)

    try:
        # ── 1. Signup page ────────────────────────────────────────
        print("1. Opening signup page...")
        page.get("https://account.noon.com/egypt-en/profile/")
        console_input("\n>>> Page opened. Press ENTER to continue...\n")

        # ── 2. Email field ────────────────────────────────────────
        print("2. Filling email...")
        dp_fill(page, [
            'input[name="email"]',
            'input[type="email"]',
            '#email',
            'input[placeholder*="mail" i]',
        ], email, desc="email")
        human_wait(800, 1200)

        # ── 3. Password field ─────────────────────────────────────
        print("3. Filling password...")
        dp_fill(page, [
            'input[name="password"]',
            'input[type="password"]',
            '#password',
        ], password, desc="password")
        human_wait(800, 1200)

        # ── 4. Confirm Password ───────────────────────────────────
        print("4. Filling confirm password...")
        dp_fill(page, [
            'input[name="confirmPassword"]',
            'input[name="confirm_password"]',
            'input[placeholder*="confirm" i]',
        ], password, desc="confirm password")
        human_wait(800, 1200)

        # ── 5. Continue / Submit ──────────────────────────────────
        print("5. Clicking Continue...")
        dp_click(page, [
            'button[type="submit"]',
            'button:has(.ArrowRightIcon)',
            '#register-btn',
        ], desc="Continue button")
        human_wait()
        human_wait()

        # ── 6. Handle OTP screen if it appears ───────────────────
        print("6. Checking for OTP / verification screen...")
        time.sleep(2)
        try:
            otp_box = page.ele('css:input[name*="otp" i]', timeout=3)
            if not otp_box:
                otp_box = page.ele('css:input[maxlength="1"]', timeout=3)
            if otp_box:
                print("  OTP screen detected. Waiting for user to complete it...")
                console_input("\n>>> Complete email OTP in browser, then press ENTER here to continue...\n")
        except Exception:
            pass
        human_wait()

        # ── 7. Navigate to profile page ───────────────────────────
        print("7. Navigating to profile page...")
        page.get("https://account.noon.com/egypt-en/profile/")
        human_wait()
        human_wait()

        # ── 8. Wait for profile page to load ─────────────────────
        print("8. Waiting for profile page...")
        time.sleep(3)

        # ── 9. Close any popup/modal that may appear ──────────────
        print("9. Checking for popups...")
        try:
            close_btn = page.ele('css:button[aria-label*="close" i]', timeout=2)
            if close_btn:
                close_btn.click()
                human_wait(400, 700)
        except Exception:
            pass

        # ── 10. Click Add phone button ────────────────────────────
        print("10. Clicking Add phone button...")
        added = dp_click(page, [
            'div[class*="hasAddAction"]',
            'div[class*="hasAddAction"] span',
            'div[class*="editPhoneInputCtr"] span',
            'img[alt="plus-blue"] + span',
            'img[alt="plus-blue"]',
            'span:contains("Add")',
        ], desc="Add phone button")

        if added:
            human_wait(800, 1200)

            # ── 11. Focus phone input ──────────────────────────────
            print("11. Looking for phone input field...")
            phone_ele = None
            for sel in [
                'div[class*="PhoneInput"] input',
                '#overlay-portal input[type="tel"]',
                '#overlay-portal input[type="text"]',
                '#overlay-portal input',
                'input[placeholder*="phone" i]',
            ]:
                try:
                    phone_ele = page.ele(f"css:{sel}", timeout=4)
                    if phone_ele:
                        phone_ele.click()
                        print("  [OK] Phone input focused.")
                        break
                except Exception:
                    continue

            if phone_ele:
                console_input("\n>>> Type phone number in browser, then press ENTER here to submit...\n")
                human_wait(300, 500)

                # ── 12. Click Save/Send ────────────────────────────
                print("12. Clicking Save/Send to trigger SMS...")
                
                target_button = None
                text_keywords = ["save", "send", "verification", "حفظ", "إرسال", "تأكيد"]
                
                # 1. Search all button elements on the page first (highly robust)
                try:
                    buttons = page.eles('css:button')
                    for btn in buttons:
                        btn_text = btn.text.lower() if btn.text else ""
                        if any(kw in btn_text for kw in text_keywords):
                            target_button = btn
                            print(f"  Found button by text across page: '{btn.text}'")
                            break
                except Exception:
                    pass

                # 2. Try direct text lookup if not found (supports divs/spans styled as buttons)
                if not target_button:
                    for kw in text_keywords:
                        try:
                            btn = page.ele(f"text:{kw}", timeout=1)
                            if btn:
                                tag = btn.tag.lower()
                                if tag in ['button', 'div', 'span', 'a', 'p']:
                                    target_button = btn
                                    print(f"  Found clickable element by text '{kw}': <{tag}>")
                                    break
                        except Exception:
                            continue

                # 3. Fallback to searching within overlay portal if still not found
                if not target_button:
                    overlay = None
                    try:
                        overlay = page.ele('css:#overlay-portal', timeout=2)
                    except Exception:
                        pass
                    
                    if overlay:
                        try:
                            # Look for submit button inside overlay
                            buttons = overlay.eles('css:button')
                            for btn in buttons:
                                if btn.attr('type') == 'submit':
                                    target_button = btn
                                    print("  Found button by type='submit' in overlay")
                                    break
                            
                            if not target_button:
                                target_button = overlay.ele('css:form button')
                                if target_button:
                                    print("  Found form button fallback in overlay")
                        except Exception:
                            pass
                
                # 4. Final generic selector lookup
                if not target_button:
                    try:
                        target_button = page.ele('css:#overlay-portal button[type="submit"]', timeout=2)
                    except Exception:
                        pass

                saved = False
                if target_button:
                    # Wait for the button to become enabled (check disabled, aria-disabled, and class)
                    print("  Waiting for button to be enabled...")
                    is_enabled = False
                    for _ in range(20):  # wait up to 10 seconds
                        attrs = target_button.attr('disabled')
                        cls = target_button.attr('class') or ""
                        aria = target_button.attr('aria-disabled')
                        
                        disabled_attr = attrs is not None
                        disabled_class = 'disabled' in cls.lower()
                        disabled_aria = aria is not None and aria.lower() == 'true'
                        
                        if not disabled_attr and not disabled_class and not disabled_aria:
                            is_enabled = True
                            break
                        time.sleep(0.5)
                    
                    if not is_enabled:
                        print("  WARNING: Button still disabled after timeout, attempting to click anyway.")
                    
                    try:
                        target_button.click()
                        print("  [OK] Clicked Save/Send button!")
                        saved = True
                    except Exception as click_err:
                        print(f"  [FAIL] Click failed: {click_err}")
                
                if not saved:
                    try:
                        from DrissionPage.common import Keys
                        phone_ele.key_press(Keys.ENTER)
                        print("  INFO: Pressed Enter on phone field as fallback.")
                        saved = True
                    except Exception as enter_err:
                        print(f"  [FAIL] Enter fallback failed: {enter_err}")

                # ── 13. Select SMS option in verification modal ────
                if saved:
                    print("13. Checking for verification modal...")
                    modal_found = False
                    for _ in range(20):  # wait up to 10 seconds
                        html = page.html or ""
                        if "Verify your account" in html or "Didn't get the" in html:
                            modal_found = True
                            break
                        time.sleep(0.5)

                    if modal_found:
                        print("  INFO: Verification modal detected.")
                        sms_btn = None
                        try:
                            # Find all elements containing text "SMS"
                            buttons = page.eles('text:SMS')
                            for btn in buttons:
                                tag = btn.tag.lower()
                                if tag in ['button', 'div', 'span', 'p']:
                                    btn_text = btn.text.strip()
                                    if btn_text == "SMS":
                                        sms_btn = btn
                                        print(f"  Found SMS button element: <{tag}>")
                                        break
                            
                            # Fallback: search for elements with tag button containing "SMS"
                            if not sms_btn:
                                for btn in page.eles('css:button'):
                                    if "sms" in btn.text.lower():
                                        sms_btn = btn
                                        print(f"  Found SMS button by tag: '{btn.text}'")
                                        break
                        except Exception as find_err:
                            print(f"  WARNING: Error finding SMS button: {find_err}")

                        if sms_btn:
                            try:
                                sms_btn.click(force=True)
                                print("  [OK] Clicked SMS button in modal!")
                            except Exception as click_err:
                                print(f"  [FAIL] Failed to click SMS button: {click_err}")
                        else:
                            print("  WARNING: SMS button not found in modal.")
                    else:
                        print("  INFO: Verification modal not detected within timeout.")
            else:
                print("  WARNING: Phone input not found in modal.")
        else:
            print("  INFO: Add button not found — may need manual steps.")

        print("\n[SUCCESS] All steps completed!")
        print(f"   Email:    {email}")
        print(f"   Password: {password}\n")

    except Exception as e:
        print(f"\n[ERROR] Error: {e}")

    return page, profile_dir


# -----------------------------------------------------------------
#  THREAD WORKER
# ─────────────────────────────────────────────────────────────────
_print_lock = threading.Lock()
BASE_PORT   = 9222  # each thread gets BASE_PORT + thread_id

def tprint(tid, msg):
    with _print_lock:
        print(f"[T{tid}] {msg}", flush=True)

def run_in_thread(tid, results):
    port     = BASE_PORT + tid
    log_path = f"thread_{tid}.log"
    tprint(tid, f"Starting on port {port}  (log -> {log_path})")

    old_stdout = sys.stdout
    log_file   = open(log_path, "w", encoding="utf-8", buffering=1)

    try:
        sys.stdout = log_file
        page, profile_dir = run_signup_process(port)
        sys.stdout = old_stdout

        # Pull credentials from log and display them
        lines = open(log_path, encoding="utf-8").readlines()
        for ln in lines:
            if "Email:" in ln or "Password:" in ln:
                tprint(tid, ln.strip())

        results[tid] = "done"
        tprint(tid, "Done! Press ENTER to close this browser.")
        input()
        page.close()

        # Clean up profile (disabled to persist profile)
        # shutil.rmtree(profile_dir, ignore_errors=True)
        tprint(tid, "Browser closed.")
    except Exception as e:
        sys.stdout = old_stdout
        tprint(tid, f"ERROR: {e}")
        results[tid] = f"error: {e}"
    finally:
        log_file.close()


# ─────────────────────────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────────────────────────
def main():
    print("=" * 56)
    print("   Noon Egypt Signup — DrissionPage (Undetectable)")
    print("=" * 56)

    while True:
        try:
            n = int(input("\nHow many parallel browsers to open? (1-5): ").strip())
            n = max(1, min(n, 5))
        except ValueError:
            n = 1

        results = {}
        threads = []

        for i in range(1, n + 1):
            t = threading.Thread(target=run_in_thread, args=(i, results), daemon=True)
            threads.append(t)
            t.start()
            time.sleep(3)  # stagger starts

        for t in threads:
            t.join()

        print("\nAll browsers closed.")
        ans = input("Start another batch? (Enter = yes / 'exit' = quit): ").strip().lower()
        if ans in ("exit", "x", "quit", "q"):
            print("Done. Have a great day!")
            break


if __name__ == "__main__":
    main()
