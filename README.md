# Noon SMS & ExpressVPN Automation Bot

Automated account creation, MSI SMS portal integration, human simulation, and ExpressVPN auto-rotation for Noon.

## Features
- **Automated Phone Fetching & OTP**: Connects directly to MSI SMS system, pulls available Mali (`+223`) numbers, and monitors incoming OTP codes.
- **ExpressVPN Auto-Rotation**: Automatically switches country/IP whenever rate-limited or blocked by Akamai, preserving the current number and retrying seamlessly.
- **Human Simulation**: Bezier curve human mouse movements and realistic keystroke intervals to pass anti-bot protections.
- **Full Session Wipe**: Automatically clears cookies, cache, storage, and profiles between runs for complete isolation.
- **One-Click Execution**: Double-click `START.bat` or `RUN_BOT.bat` with automatic administrator elevation.
- **Built-in Auto-Updater**: Checks GitHub on launch and auto-downloads the latest updates.

## Quick Start
1. Clone or download the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```
3. Run the bot:
   - Double-click `START.bat` or `RUN_BOT.bat`
   - Or run:
     ```bash
     python noon_signup_hybrid.py
     ```
