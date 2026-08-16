import os
import sys
import time
import random
import subprocess

EXPRESSVPN_EXE = r"C:\Program Files (x86)\ExpressVPN\services\ExpressVPN.CLI.exe"

# Curated pool of high-reputation, Noon/Akamai-friendly server locations
VPN_LOCATIONS = [
    "264",     # United Arab Emirates
    "356",     # Saudi Arabia
    "5",       # UK - London
    "7",       # Germany - Frankfurt - 1
    "8",       # France - Paris - 2
    "4",       # Netherlands - Amsterdam
    "11",      # Switzerland
    "21",      # Austria
    "22",      # Spain - Madrid
    "29",      # Italy - Naples
    "75",      # USA - New York
    "25",      # USA - Washington DC
    "54",      # USA - Miami
    "84",      # Egypt
    "smart"    # Smart Location
]

_current_loc_idx = random.randint(0, len(VPN_LOCATIONS) - 1)

def is_vpn_cli_installed() -> bool:
    return os.path.isfile(EXPRESSVPN_EXE)

def run_vpn_cmd(args: list) -> str:
    if not is_vpn_cli_installed():
        return "[ERROR] ExpressVPN CLI executable not found."
    try:
        res = subprocess.run(
            [EXPRESSVPN_EXE] + args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30
        )
        return (res.stdout or res.stderr or "").strip()
    except Exception as e:
        return f"[ERROR] Failed to run ExpressVPN CLI: {e}"

def get_vpn_status() -> str:
    return run_vpn_cmd(["status"])

def is_vpn_connected() -> bool:
    status = get_vpn_status().lower()
    return "connected" in status and "not connected" not in status and "connecting" not in status

def disconnect_vpn():
    return run_vpn_cmd(["disconnect"])

def flush_dns():
    try:
        subprocess.run("ipconfig /flushdns", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

def rotate_vpn(target_location: str = None) -> bool:
    """
    Rotates ExpressVPN to a new country / server and waits for connection & IP stabilization.
    """
    global _current_loc_idx
    if not is_vpn_cli_installed():
        print("❌ ExpressVPN CLI not found at default location.")
        return False

    if target_location:
        loc = target_location
    else:
        loc = VPN_LOCATIONS[_current_loc_idx % len(VPN_LOCATIONS)]
        _current_loc_idx += 1

    print(f"\n🔄 [ExpressVPN] Disconnecting current VPN session...")
    disconnect_vpn()
    time.sleep(2)
    flush_dns()

    print(f"🌍 [ExpressVPN] Connecting to location: [{loc}] ...")
    connect_out = run_vpn_cmd(["connect", loc])
    print(f"    Result: {connect_out}")

    # Wait for status to report connected (up to 25 seconds)
    print("⏳ [ExpressVPN] Waiting for connection & IP stabilization...")
    start_t = time.time()
    while time.time() - start_t < 25:
        if is_vpn_connected():
            print(f"✅ [ExpressVPN] Successfully CONNECTED! ({get_vpn_status()})")
            time.sleep(5)  # IP and routing table stabilization pause
            flush_dns()
            return True
        time.sleep(1.5)

    print("⚠️ [ExpressVPN] Connection took longer than expected. Proceeding...")
    return False

if __name__ == "__main__":
    print("Testing ExpressVPN Module...")
    print("Status:", get_vpn_status())
    print("Rotating...")
    rotate_vpn()
    print("New Status:", get_vpn_status())
