import re

def compare():
    with open("noon_signup_hybrid.py", "r", encoding="utf-8") as f:
        hybrid = f.read()
        
    with open("noon_app_gui.py", "r", encoding="utf-8") as f:
        gui = f.read()
        
    print("=== Comparing Core Methods ===")
    
    # 1. Compare sync_cookies_to_playwright
    print("\n[1] sync_cookies_to_playwright in Hybrid:")
    m1 = re.search(r"def sync_cookies_to_playwright.*?\n\n", hybrid, re.DOTALL)
    if m1:
        print(m1.group(0))
        
    print("[1] sync_cookies_to_playwright in GUI:")
    m2 = re.search(r"def sync_cookies_to_playwright.*?\n\n", gui, re.DOTALL)
    if m2:
        print(m2.group(0))
        
    # 2. Compare generate_strong_password
    print("\n[2] generate_strong_password in Hybrid:")
    m3 = re.search(r"def generate_strong_password.*?\n\n", hybrid, re.DOTALL)
    if m3:
        print(m3.group(0))
        
    print("[2] generate_strong_password in GUI:")
    m4 = re.search(r"def generate_strong_password.*?\n\n", gui, re.DOTALL)
    if m4:
        print(m4.group(0))

if __name__ == "__main__":
    compare()
