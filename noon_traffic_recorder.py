import json
import os
import time
import sys
import atexit
from datetime import datetime
from playwright.sync_api import sync_playwright

LOG_FILE = "captured_noon_flow.json"
captured_data = []

def save_log():
    if captured_data:
        try:
            with open(LOG_FILE, "w", encoding="utf-8") as f:
                json.dump(captured_data, f, indent=2, ensure_ascii=False)
            print(f"\n[RECORDER] Successfully saved {len(captured_data)} traffic entries to '{LOG_FILE}'")
        except Exception as e:
            print(f"\n[RECORDER] Error saving log file: {e}")

atexit.register(save_log)

def main():
    print("=" * 60)
    print("        NOON API TRAFFIC RECORDER")
    print("=" * 60)
    print("This script will open Brave Browser and record all HTTP API requests")
    print("and responses going to noon.com to build a requests-based script.")
    print("\nInstructions:")
    print("1. A Brave browser window will open.")
    print("2. Perform the entire registration process manually in that browser:")
    print("   - Enter email and password.")
    print("   - Click Continue.")
    print("   - Wait for the profile page.")
    print("   - Click 'Add' next to Phone number.")
    print("   - Enter your phone number and click Save/Send.")
    print("   - Choose 'SMS' in the verification modal.")
    print("3. Once the OTP is sent to your phone, close the browser window or")
    print("   press Enter in this terminal to stop recording and save the file.")
    print("=" * 60)

    BRAVE_PATH = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
    
    # Use a persistent profile directory local to the workspace
    profile_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "recorder_profile")
    if os.path.exists(profile_dir):
        # We can start fresh to make sure we capture the signup flow from the beginning
        import shutil
        try:
            shutil.rmtree(profile_dir, ignore_errors=True)
            print("[RECORDER] Cleaned previous recorder profile to start fresh.")
        except Exception:
            pass

    os.makedirs(profile_dir, exist_ok=True)

    with sync_playwright() as p:
        browser_args = [
            "--no-sandbox",
            "--disable-web-security",
            "--disable-features=IsolateOrigins,site-per-process",
        ]
        
        print("[RECORDER] Launching Brave browser...")
        context = p.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            executable_path=BRAVE_PATH,
            headless=False,
            args=browser_args,
            viewport={'width': 1200, 'height': 800}
        )

        page = context.pages[0]

        def handle_request(request):
            url = request.url
            # Filter for Noon API endpoints
            if "noon.com" in url:
                post_data = ""
                if request.post_data:
                    try:
                        post_data = request.post_data_text
                    except Exception:
                        pass
                
                entry = {
                    "timestamp": datetime.now().isoformat(),
                    "type": "request",
                    "method": request.method,
                    "url": url,
                    "headers": dict(request.headers),
                    "post_data": post_data
                }
                captured_data.append(entry)
                # Save continuously in case of abrupt termination
                save_log()

        def handle_response(response):
            url = response.url
            if "noon.com" in url:
                body = ""
                # Avoid downloading huge images/binary files response body
                content_type = response.headers.get("content-type", "").lower()
                if "json" in content_type or "text" in content_type or "javascript" in content_type:
                    try:
                        body = response.text()
                    except Exception:
                        body = "[unreadable text body]"
                else:
                    body = f"[binary/ignored content-type: {content_type}]"
                
                entry = {
                    "timestamp": datetime.now().isoformat(),
                    "type": "response",
                    "status": response.status,
                    "url": url,
                    "headers": dict(response.headers),
                    "body": body
                }
                captured_data.append(entry)
                save_log()

        # Listen to network events
        page.on("request", handle_request)
        page.on("response", handle_response)

        print("[RECORDER] Navigating to Noon Account Profile Page...")
        page.goto("https://account.noon.com/egypt-en/profile/")

        print("\n>>> Browser is open. Please proceed with the registration flow now.")
        print(">>> PRESS ENTER HERE IN THE TERMINAL TO SAVE AND EXIT WHEN DONE.")
        
        try:
            input()
        except KeyboardInterrupt:
            pass

        print("[RECORDER] Closing browser and saving final logs...")
        context.close()

if __name__ == "__main__":
    main()
