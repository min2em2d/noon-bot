import os
import sys
import re
import time
import datetime
import requests

class MSIApiClient:
    """
    Pure Python Interactive API client for MSI SMS System.
    Handles dynamic math captcha login, fetching numbers, dashboard statistics,
    retrieving SMS/OTP codes, and live monitoring.
    """

    BASE_URL = "http://145.239.130.45/ints"

    def __init__(self, username="R_minaemad", password="R_minaemad"):
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
        })
        self.is_logged_in = False

    def solve_math_captcha(self, html_content: str) -> int:
        """Parses math captcha expression from login HTML (e.g. 'What is 8 + 7 = ?')."""
        match = re.search(r"What\s+is\s+(\d+)\s*([\+\-\*])\s*(\d+)\s*=", html_content, re.IGNORECASE)
        if match:
            num1 = int(match.group(1))
            op = match.group(2)
            num2 = int(match.group(3))
            
            if op == '+':
                result = num1 + num2
            elif op == '-':
                result = num1 - num2
            elif op == '*':
                result = num1 * num2
            else:
                result = num1 + num2
                
            return result
            
        raise ValueError("Could not extract math captcha from login page.")

    def login(self) -> bool:
        """Fetches login page, solves math captcha, and submits signin POST request."""
        login_page_url = f"{self.BASE_URL}/login"
        
        try:
            resp = self.session.get(login_page_url, timeout=15)
            if resp.status_code != 200:
                print(f"❌ Failed to load login page. Status: {resp.status_code}")
                return False

            captcha_ans = self.solve_math_captcha(resp.text)

            signin_url = f"{self.BASE_URL}/signin"
            payload = {
                "username": self.username,
                "password": self.password,
                "capt": str(captcha_ans)
            }
            
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Referer": login_page_url,
                "Origin": "http://145.239.130.45"
            }

            login_resp = self.session.post(signin_url, data=payload, headers=headers, allow_redirects=True, timeout=15)
            
            if "SMSDashboard" in login_resp.url or login_resp.status_code == 200:
                self.is_logged_in = True
                return True
            else:
                print(f"❌ Login failed. Status: {login_resp.status_code}, URL: {login_resp.url}")
                return False
        except Exception as e:
            print(f"❌ Login Error: {e}")
            return False

    def get_my_numbers(self, limit: int = 500) -> list:
        """
        Fetches all assigned SMS numbers for the account.
        Returns a list of dicts: [{'range': ..., 'prefix': ..., 'number': ..., 'payterm': ..., 'payout': ..., 'limits': ...}]
        """
        if not self.is_logged_in and not self.login():
            return []

        url = f"{self.BASE_URL}/client/res/data_smsnumbers.php?sEcho=1&iDisplayStart=0&iDisplayLength={limit}"
        headers = {
            "Referer": f"{self.BASE_URL}/client/MySMSNumbers",
            "X-Requested-With": "XMLHttpRequest"
        }

        try:
            resp = self.session.get(url, headers=headers, timeout=15)
            data = resp.json()
            numbers_list = []
            for row in data.get("aaData", []):
                if len(row) >= 6:
                    numbers_list.append({
                        "range": row[0],
                        "prefix": row[1],
                        "number": row[2],
                        "payterm": row[3],
                        "payout": row[4],
                        "limits": re.sub(r'<[^>]+>', '', row[5]).strip()
                    })
            return numbers_list
        except Exception as e:
            print(f"❌ Error fetching numbers: {e}")
            return []

    def get_next_number(self, country: str = "mali", used_file="used_numbers.txt") -> tuple:
        """
        Returns (full_number, local_number) for the next available number of the chosen country.
        Supports 'mali' (+223) and 'egypt' (+20).
        Automatically checks used_numbers.txt to avoid duplicates.
        """
        used_numbers = set()
        if os.path.exists(used_file):
            try:
                with open(used_file, "r", encoding="utf-8") as f:
                    used_numbers = set(line.strip() for line in f if line.strip())
            except Exception:
                pass

        all_numbers = self.get_my_numbers(limit=500)
        if not all_numbers:
            return None, None

        target_country = country.lower().strip()

        for item in all_numbers:
            num = str(item.get("number", "")).strip()
            range_name = str(item.get("range", "")).lower()
            prefix = str(item.get("prefix", "")).strip()

            clean_full = num.replace("+", "").strip()

            if clean_full in used_numbers or num in used_numbers:
                continue

            if target_country in ["mali", "223"]:
                is_match = "mali" in range_name or prefix == "223" or clean_full.startswith("223")
                if is_match:
                    local_num = clean_full
                    if local_num.startswith("223"):
                        local_num = local_num[3:]
                    return clean_full, local_num

            elif target_country in ["egypt", "20", "eg"]:
                is_match = "egypt" in range_name or prefix == "20" or clean_full.startswith("20")
                if is_match:
                    local_num = clean_full
                    if local_num.startswith("20"):
                        local_num = local_num[2:]
                    return clean_full, local_num

        return None, None

    def get_next_mali_number(self, used_file="used_numbers.txt") -> tuple:
        return self.get_next_number(country="mali", used_file=used_file)

    def mark_number_as_used(self, number: str, used_file="used_numbers.txt"):
        """Saves number to used_numbers.txt so it won't be reused."""
        try:
            with open(used_file, "a", encoding="utf-8") as f:
                f.write(f"{number}\n")
        except Exception as e:
            print(f"[WARNING] Could not save used number: {e}")

    def get_sms_logs(self, date_from: str = None, date_to: str = None, phone_number: str = "", limit: int = 100) -> list:
        """Fetches received SMS logs from MSI."""
        if not self.is_logged_in and not self.login():
            return []

        now = datetime.datetime.now()
        if not date_to:
            date_to = now.strftime("%Y-%m-%d 23:59:59")
        if not date_from:
            date_from = (now - datetime.timedelta(days=7)).strftime("%Y-%m-%d 00:00:00")

        url = (
            f"{self.BASE_URL}/client/res/data_smscdr.php"
            f"?sEcho=1&iDisplayStart=0&iDisplayLength={limit}"
            f"&fdate1={requests.utils.quote(date_from)}&fdate2={requests.utils.quote(date_to)}"
            f"&fnum={phone_number}"
        )
        headers = {
            "Referer": f"{self.BASE_URL}/client/SMSCDRStats",
            "X-Requested-With": "XMLHttpRequest"
        }

        try:
            resp = self.session.get(url, headers=headers, timeout=15)
            data = resp.json()
            sms_list = []
            for row in data.get("aaData", []):
                if len(row) >= 5 and isinstance(row[0], str):
                    sms_text = str(row[4]) if row[4] else ""
                    # Extract 4-6 digit OTP code
                    otp_match = re.search(r'\b\d{4,6}\b', sms_text)
                    otp_code = otp_match.group(0) if otp_match else None

                    sms_list.append({
                        "date": row[0],
                        "range": row[1],
                        "number": row[2],
                        "sender": row[3],
                        "sms_text": sms_text,
                        "otp_code": otp_code,
                    })
            return sms_list
        except Exception as e:
            print(f"❌ Error fetching SMS logs: {e}")
            return []

    def get_latest_otp(self, phone_number: str, timeout_seconds: int = 60, poll_interval: int = 3) -> str:
        """
        Polls for the latest OTP code received for a specific phone number.
        Returns the OTP string if found, otherwise None.
        """
        clean_num = str(phone_number).replace("+", "").strip()
        print(f"⏳ [MSI] Waiting for OTP code on number: {clean_num} (Timeout: {timeout_seconds}s)...")
        
        start_time = time.time()
        while time.time() - start_time < timeout_seconds:
            logs = self.get_sms_logs(phone_number=clean_num, limit=10)
            for item in logs:
                num_in_log = str(item.get("number", "")).replace("+", "").strip()
                if clean_num in num_in_log or num_in_log in clean_num:
                    if item.get("otp_code"):
                        print(f"\n🎯 [MSI OTP RECEIVED]: [{item['otp_code']}] | Message: {item['sms_text']}")
                        return item["otp_code"]
            
            time.sleep(poll_interval)

        print(f"⚠️ [MSI Timeout] No OTP received within {timeout_seconds} seconds.")
        return None
