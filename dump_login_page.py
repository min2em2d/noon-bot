import os
import time
from playwright.sync_api import sync_playwright

def run():
    CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    with sync_playwright() as p:
        context = p.chromium.launch(
            executable_path=CHROME_PATH,
            headless=False
        )
        page = context.new_page()
        page.goto("https://account.noon.com/egypt-en/profile/", wait_until="networkidle")
        time.sleep(3)
        
        # Dump HTML
        html = page.content()
        with open("login_page_dump.html", "w", encoding="utf-8") as out:
            out.write(html)
        print("Logged out page HTML dumped.")
        
        # Take screenshot
        page.screenshot(path="login_page_screenshot.png")
        print("Screenshot saved to login_page_screenshot.png")
        
        context.close()

if __name__ == "__main__":
    run()
