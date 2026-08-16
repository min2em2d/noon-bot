import time
from playwright.sync_api import sync_playwright

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        user_data_dir="./test_profile",
        executable_path=CHROME_PATH,
        headless=False
    )
    page = context.pages[0]
    
    print("[1] Opening Noon Profile Page...")
    page.goto("https://account.noon.com/egypt-en/profile/")
    time.sleep(2)
    
    print("[2] Opening Signup Modal...")
    login_signup_selectors = [
        'text="Login/Signup"',
        'text="LOGIN/SIGNUP"',
        'div.layout-module-scss-module__-MERqq__mainLayout span',
        'xpath=//html/body/div[2]/div/main/div/div/div[2]/button/span',
    ]
    for sel in login_signup_selectors:
        try:
            page.locator(sel).first.click(timeout=3000)
            print(f"    Clicked: {sel}")
            break
        except Exception:
            continue
            
    time.sleep(2)
    
    print("[3] Switching to Sign Up tab...")
    signup_link_selectors = [
        '[data-qa="sign-up"]',
        'text="Sign up"',
        'text="Sign Up"',
    ]
    for sel in signup_link_selectors:
        try:
            page.locator(sel).first.click(timeout=3000)
            print(f"    Clicked: {sel}")
            break
        except Exception:
            continue
            
    time.sleep(3)
    
    # Check what recaptcha objects exist
    has_grecaptcha = page.evaluate("typeof grecaptcha !== 'undefined'")
    print(f"Is window.grecaptcha defined? {has_grecaptcha}")
    
    if has_grecaptcha:
        keys = page.evaluate("Object.keys(grecaptcha)")
        print(f"grecaptcha properties: {keys}")
        
        has_enterprise = page.evaluate("typeof grecaptcha.enterprise !== 'undefined'")
        print(f"Is window.grecaptcha.enterprise defined? {has_enterprise}")
        if has_enterprise:
            ent_keys = page.evaluate("Object.keys(grecaptcha.enterprise)")
            print(f"grecaptcha.enterprise properties: {ent_keys}")
            
    context.close()
