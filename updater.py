import os
import sys
import subprocess
import requests
import json

# GitHub repository name for automatic updates
GITHUB_REPO = "min2em2d/noon-bot"
BRANCH = "main"

TRACKED_FILES = [
    "noon_signup_hybrid.py",
    "msi_api.py",
    "expressvpn_manager.py",
    "requirements.txt",
    "START.bat",
    "RUN_BOT.bat",
    "README.md"
]

def check_for_updates():
    """
    Checks GitHub for the latest version of the code and updates modified files automatically.
    Works with both Git (git pull) and standalone direct file download (without requiring Git).
    """
    if "YOUR_USERNAME" in GITHUB_REPO:
        return

    print("\n🔍 [*] Checking GitHub for latest updates...")

    # Method 1: If repository is cloned with git
    if os.path.exists(os.path.join(os.path.dirname(__file__), ".git")):
        try:
            res = subprocess.run(
                ["git", "pull", "origin", BRANCH],
                cwd=os.path.dirname(__file__),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10
            )
            output = (res.stdout or res.stderr).strip()
            if "Already up to date" in output:
                print("✅ Code is up to date with GitHub.")
            else:
                print(f"🚀 [UPDATED] Downloaded latest updates:\n    {output}")
            return
        except Exception:
            pass

    # Method 2: Pure Python downloader from GitHub raw (No Git required on client machine)
    base_raw_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{BRANCH}"
    updated_any = False
    
    for filename in TRACKED_FILES:
        target_path = os.path.join(os.path.dirname(__file__), filename)
        file_url = f"{base_raw_url}/{filename}"
        
        try:
            resp = requests.get(file_url, timeout=5)
            if resp.status_code == 200:
                remote_content = resp.content
                local_content = b""
                if os.path.exists(target_path):
                    with open(target_path, "rb") as f:
                        local_content = f.read()
                        
                if local_content != remote_content:
                    with open(target_path, "wb") as f:
                        f.write(remote_content)
                    print(f"📥 [UPDATED FILE]: {filename}")
                    updated_any = True
        except Exception:
            pass

    if updated_any:
        print("✅ Successfully updated all files to the latest GitHub version!\n")
    else:
        print("✅ You are running the latest version from GitHub.\n")

if __name__ == "__main__":
    check_for_updates()
