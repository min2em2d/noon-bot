import json

with open("noon_signup_hybrid.py", "r", encoding="utf-8") as f:
    code = f.read()

# 1. Step 594 edit
old_594 = """        # UI Navigation to force the reCAPTCHA Enterprise script to load
        print("[2.5] Opening Signup Modal in UI...")
        login_signup_selectors = [
            'text="Login/Signup"',
            'text="LOGIN/SIGNUP"',
            'button:has-text("Login")',
            'span:has-text("Login")',
        ]
        safe_click(page, login_signup_selectors, timeout=5000)
        time.sleep(1)

        signup_link_selectors = [
            '[data-qa="sign-up"]',
            'text="Sign up"',
            'text="Sign Up"',
        ]
        safe_click(page, signup_link_selectors, timeout=3000)
        time.sleep(1)"""

new_594 = """        # UI Navigation to force the reCAPTCHA Enterprise script to load
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
            '[data-qa="اشترك-الآن"]',
            'button:has-text("Sign up")',
            'span:has-text("Sign up")',
        ]
        if safe_click(page, signup_link_selectors, timeout=3000):
            print("    Successfully switched to Sign Up tab.")
        else:
            print("    Warning: Failed to click Sign Up tab.")
        time.sleep(1)"""

if old_594 in code:
    code = code.replace(old_594, new_594)
    print("Step 594 edit applied.")

# 2. Step 636 edit
old_636 = """def get_recaptcha_token(page, action):
    \"\"\"Wait for reCAPTCHA Enterprise script to load and generate a token for an action\"\"\"
    try:
        # Wait up to 15 seconds for Google reCAPTCHA Enterprise to load
        page.wait_for_function(
            "typeof grecaptcha !== 'undefined' && typeof grecaptcha.enterprise !== 'undefined'",
            timeout=15000
        )
        # Execute reCAPTCHA Enterprise in the browser context
        token = page.evaluate(
            f"grecaptcha.enterprise.execute('{RECAPTCHA_KEY}', {{action: '{action}'}})"
        )
        return token
    except Exception as e:
        print(f"[RECAPTCHA ERROR] Failed to generate token: {e}")
        return None"""

new_636 = """def get_recaptcha_token(page, action):
    \"\"\"Wait for reCAPTCHA script to load and generate a token for an action\"\"\"
    try:
        # Wait up to 15 seconds for Google reCAPTCHA to load
        page.wait_for_function(
            "typeof grecaptcha !== 'undefined' && typeof grecaptcha.execute !== 'undefined'",
            timeout=15000
        )
        # Execute reCAPTCHA in the browser context directly using grecaptcha.execute
        token = page.evaluate(
            f"grecaptcha.execute('{RECAPTCHA_KEY}', {{action: '{action}'}})"
        )
        return token
    except Exception as e:
        print(f"[RECAPTCHA ERROR] Failed to generate token: {e}")
        return None"""

if old_636 in code:
    code = code.replace(old_636, new_636)
    print("Step 636 edit applied.")

with open("noon_signup_hybrid.py", "w", encoding="utf-8") as out:
    out.write(code)

print("Saved clean reconstructed code!")
