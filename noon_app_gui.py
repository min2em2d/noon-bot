import os
import sys
import time
import json
import uuid
import random
import csv
import threading
import queue
from datetime import datetime
from curl_cffi import requests
from playwright.sync_api import sync_playwright
import customtkinter as ctk
from tkinter import filedialog, messagebox

# Appearance settings
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Site-key for Noon reCAPTCHA Enterprise
RECAPTCHA_KEY = "6Lc3F28qAAAAALqhS6u6ULhid0FfhAQxz0uwVQjC"

def generate_strong_password():
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
    return "01223456" + "".join(random.choice(chars) for _ in range(4)) + "@"

def generate_custom_gmail():
    prefix = "nabil"
    mid = random.choice(["c", "d", "e", "f", "k"])
    num1 = random.randint(1, 9)
    name = random.choice(["omar", "salem", "ibrahim", "ali"])
    num2 = random.randint(1000, 9999)
    return f"{prefix}{mid}{num1}{name}{num2}@gmail.com"

def sync_cookies_to_curl(context, session):
    """Sync Playwright browser cookies to curl_cffi session"""
    cookies = context.cookies()
    for cookie in cookies:
        session.cookies.set(
            name=cookie['name'],
            value=cookie['value'],
            domain=cookie['domain'],
            path=cookie['path']
        )

def sync_cookies_to_playwright(session, context):
    """Sync curl_cffi session cookies back to Playwright browser context"""
    cookies_to_add = []
    for cookie in session.cookies.jar:
        name = cookie.name
        value = cookie.value
        domain = cookie.domain
        path = cookie.path
        
        if name.lower() == "_grecaptcha" or name.startswith("_grecaptcha"):
            continue
            
        if not domain:
            domain = ".noon.com"
        elif "noon.com" not in domain.lower():
            continue
            
        cookies_to_add.append({
            "name": name,
            "value": value,
            "domain": domain,
            "path": path if path else "/"
        })
    try:
        context.add_cookies(cookies_to_add)
    except Exception as e:
        print(f"Cookie sync back error: {e}")

def safe_click(page, selectors, timeout=3000, force=False):
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            loc.wait_for(state="visible", timeout=timeout)
            loc.click(force=force)
            return True
        except Exception:
            continue
    return False

class NoonAutomationApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("NOON ACCOUNT CREATION & OTP AUTOMATOR")
        self.geometry("1100x680")
        
        # Application State variables
        self.market_var = ctk.StringVar(value="Egypt (EG)")
        self.country_code_var = ctk.StringVar(value="223") # Default to Mali (223) based on user's CSV
        self.thread_count_var = ctk.IntVar(value=1)
        self.numbers_queue = queue.Queue()
        self.is_running = False
        self.threads = []
        self.imported_numbers = []
        
        # Load previously used numbers database
        self.used_numbers_file = "used_numbers.txt"
        self.used_numbers = set()
        if os.path.exists(self.used_numbers_file):
            try:
                with open(self.used_numbers_file, "r") as f:
                    for line in f:
                        num = line.strip()
                        if num:
                            self.used_numbers.add(num)
            except Exception as e:
                print(f"Error loading used numbers file: {e}")
        
        # Stats variables
        self.stat_total = 0
        self.stat_success = 0
        self.stat_whatsapp = 0
        self.stat_sms = 0
        self.stat_fail = 0
        
        self.setup_gui()
        
    def setup_gui(self):
        # Configure Grid Layout
        self.grid_columnconfigure(0, weight=1)  # Left controls & stats
        self.grid_columnconfigure(1, weight=3)  # Right logs & numbers list
        self.grid_rowconfigure(0, weight=1)
        
        # ==================== LEFT SIDEBAR (Controls & Stats) ====================
        sidebar = ctk.CTkFrame(self, width=280, corner_radius=15)
        sidebar.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")
        sidebar.grid_columnconfigure(0, weight=1)
        
        # Brand Header
        lbl_title = ctk.CTkLabel(sidebar, text="NOON AUTOMATOR", font=ctk.CTkFont(size=20, weight="bold", family="Outfit"))
        lbl_title.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        lbl_subtitle = ctk.CTkLabel(sidebar, text="Multi-threaded Hybrid Bot", text_color="gray", font=ctk.CTkFont(size=12))
        lbl_subtitle.grid(row=1, column=0, padx=20, pady=(0, 20))
        
        # Market Config
        lbl_market = ctk.CTkLabel(sidebar, text="Noon Storefront Region:", font=ctk.CTkFont(size=13, weight="bold"))
        lbl_market.grid(row=2, column=0, padx=20, pady=(10, 5), sticky="w")
        
        cb_market = ctk.CTkOptionMenu(sidebar, values=["Egypt (EG)", "Saudi Arabia (SA)", "UAE (AE)"], variable=self.market_var)
        cb_market.grid(row=3, column=0, padx=20, pady=(0, 15), sticky="ew")
        
        # Phone Country Code Config
        lbl_cc = ctk.CTkLabel(sidebar, text="Phone Country Code:", font=ctk.CTkFont(size=13, weight="bold"))
        lbl_cc.grid(row=4, column=0, padx=20, pady=(10, 5), sticky="w")
        
        self.country_dict = {
            "Mali (+223)": "223",
            "Egypt (+20)": "20",
            "Saudi Arabia (+966)": "966",
            "UAE (+971)": "971",
            "Algeria (+213)": "213",
            "Bahrain (+973)": "973",
            "Bangladesh (+880)": "880",
            "India (+91)": "91",
            "Jordan (+962)": "962",
            "Kuwait (+965)": "965",
            "Lebanon (+961)": "961",
            "Libya (+218)": "218",
            "Morocco (+212)": "212",
            "Oman (+968)": "968",
            "Pakistan (+92)": "92",
            "Qatar (+974)": "974",
            "Sudan (+249)": "249",
            "Syria (+963)": "963",
            "Tunisia (+216)": "216",
            "Yemen (+967)": "967",
            "Afghanistan (+93)": "93",
            "Albania (+355)": "355",
            "Andorra (+376)": "376",
            "Angola (+244)": "244",
            "Argentina (+54)": "54",
            "Armenia (+374)": "374",
            "Australia (+61)": "61",
            "Austria (+43)": "43",
            "Azerbaijan (+994)": "994",
            "Belarus (+375)": "375",
            "Belgium (+32)": "32",
            "Bolivia (+591)": "591",
            "Bosnia and Herzegovina (+387)": "387",
            "Brazil (+55)": "55",
            "Bulgaria (+359)": "359",
            "Cameroon (+237)": "237",
            "Canada (+1)": "1",
            "Chile (+56)": "56",
            "China (+86)": "86",
            "Colombia (+57)": "57",
            "Costa Rica (+506)": "506",
            "Croatia (+385)": "385",
            "Cyprus (+357)": "357",
            "Czech Republic (+420)": "420",
            "Denmark (+45)": "45",
            "Ecuador (+593)": "593",
            "Estonia (+372)": "372",
            "Ethiopia (+251)": "251",
            "Finland (+358)": "358",
            "France (+33)": "33",
            "Georgia (+995)": "995",
            "Germany (+49)": "49",
            "Ghana (+233)": "233",
            "Greece (+30)": "30",
            "Hong Kong (+852)": "852",
            "Hungary (+36)": "36",
            "Iceland (+354)": "354",
            "Indonesia (+62)": "62",
            "Iran (+98)": "98",
            "Iraq (+964)": "964",
            "Ireland (+353)": "353",
            "Italy (+39)": "39",
            "Japan (+81)": "81",
            "Kazakhstan (+7)": "7",
            "Kenya (+254)": "254",
            "Latvia (+371)": "371",
            "Lithuania (+370)": "370",
            "Luxembourg (+352)": "352",
            "Malaysia (+60)": "60",
            "Malta (+356)": "356",
            "Mexico (+52)": "52",
            "Moldova (+373)": "373",
            "Monaco (+377)": "377",
            "Nepal (+977)": "977",
            "Netherlands (+31)": "31",
            "New Zealand (+64)": "64",
            "Nigeria (+234)": "234",
            "Norway (+47)": "47",
            "Palestine (+970)": "970",
            "Panama (+507)": "507",
            "Paraguay (+595)": "595",
            "Peru (+51)": "51",
            "Philippines (+63)": "63",
            "Poland (+48)": "48",
            "Portugal (+351)": "351",
            "Romania (+40)": "40",
            "Russia (+7)": "7",
            "Senegal (+221)": "221",
            "Serbia (+381)": "381",
            "Singapore (+65)": "65",
            "Slovakia (+421)": "421",
            "Slovenia (+386)": "386",
            "South Africa (+27)": "27",
            "South Korea (+82)": "82",
            "Spain (+34)": "34",
            "Sri Lanka (+94)": "94",
            "Sweden (+46)": "46",
            "Switzerland (+41)": "41",
            "Taiwan (+886)": "886",
            "Thailand (+66)": "66",
            "Turkey (+90)": "90",
            "Ukraine (+380)": "380",
            "United Kingdom (+44)": "44",
            "United States (+1)": "1",
            "Uruguay (+598)": "598",
            "Uzbekistan (+998)": "998",
            "Venezuela (+58)": "58",
            "Vietnam (+84)": "84",
            "Zimbabwe (+263)": "263"
        }
        
        self.country_options = sorted(list(self.country_dict.keys()))
        self.cb_cc = ctk.CTkOptionMenu(sidebar, values=self.country_options, command=self.on_country_select)
        self.cb_cc.set("Mali (+223)")
        self.cb_cc.grid(row=5, column=0, padx=20, pady=(0, 5), sticky="ew")
        
        self.ent_cc = ctk.CTkEntry(sidebar, textvariable=self.country_code_var, placeholder_text="Code")
        self.ent_cc.grid(row=6, column=0, padx=20, pady=(0, 15), sticky="ew")
        
        # Thread Count Config
        lbl_threads = ctk.CTkLabel(sidebar, text="Concurrent Threads (Default 1):", font=ctk.CTkFont(size=13, weight="bold"))
        lbl_threads.grid(row=7, column=0, padx=20, pady=(10, 5), sticky="w")
        
        self.sp_threads = ctk.CTkSegmentedButton(sidebar, values=["1", "2", "3", "4", "5", "8", "10"], command=self.set_threads_val)
        self.sp_threads.set("1")
        self.sp_threads.grid(row=8, column=0, padx=20, pady=(0, 15), sticky="ew")
        
        # Statistics Panel Frame
        stats_frame = ctk.CTkFrame(sidebar, fg_color="transparent", border_width=1, border_color="#333333", corner_radius=10)
        stats_frame.grid(row=9, column=0, padx=20, pady=15, sticky="ew")
        stats_frame.grid_columnconfigure((0, 1), weight=1)
        
        self.lbl_stat_total = ctk.CTkLabel(stats_frame, text="Total: 0", font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_stat_total.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        self.lbl_stat_success = ctk.CTkLabel(stats_frame, text="Accounts: 0", text_color="#2ecc71", font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_stat_success.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        
        self.lbl_stat_wa = ctk.CTkLabel(stats_frame, text="WhatsApp: 0", text_color="#3498db", font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_stat_wa.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        
        self.lbl_stat_sms = ctk.CTkLabel(stats_frame, text="SMS OTP: 0", text_color="#e67e22", font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_stat_sms.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        
        self.lbl_stat_fail = ctk.CTkLabel(stats_frame, text="Failed: 0", text_color="#e74c3c", font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_stat_fail.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="w")

        # Action Buttons
        self.btn_start = ctk.CTkButton(sidebar, text="START RUN", fg_color="#2ecc71", hover_color="#27ae60", font=ctk.CTkFont(weight="bold"), command=self.start_automation)
        self.btn_start.grid(row=10, column=0, padx=20, pady=(20, 10), sticky="ew")
        
        self.btn_stop = ctk.CTkButton(sidebar, text="STOP / PAUSE", fg_color="#e74c3c", hover_color="#c0392b", font=ctk.CTkFont(weight="bold"), command=self.stop_automation)
        self.btn_stop.grid(row=11, column=0, padx=20, pady=(0, 10), sticky="ew")
        
        self.btn_clear_db = ctk.CTkButton(sidebar, text="Clear Used Numbers DB", fg_color="#34495e", hover_color="#2c3e50", font=ctk.CTkFont(weight="bold"), command=self.clear_used_db)
        self.btn_clear_db.grid(row=12, column=0, padx=20, pady=(0, 15), sticky="ew")# ==================== RIGHT CONTENT AREA ====================
        main_content = ctk.CTkFrame(self, corner_radius=15)
        main_content.grid(row=0, column=1, padx=(0, 15), pady=15, sticky="nsew")
        main_content.grid_columnconfigure(0, weight=1)
        main_content.grid_rowconfigure(2, weight=1) # Logs gets most space
        
        # Top panel: File Import
        import_frame = ctk.CTkFrame(main_content, fg_color="transparent")
        import_frame.grid(row=0, column=0, padx=20, pady=(15, 10), sticky="ew")
        import_frame.grid_columnconfigure(0, weight=1)
        
        self.lbl_file_status = ctk.CTkLabel(import_frame, text="No CSV file imported.", font=ctk.CTkFont(size=13, slant="italic"))
        self.lbl_file_status.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        btn_import = ctk.CTkButton(import_frame, text="Import CSV File", width=140, command=self.import_csv)
        btn_import.grid(row=0, column=1, padx=10, pady=5, sticky="e")
        
        # Manual Input Field
        lbl_manual = ctk.CTkLabel(main_content, text="Or Paste Numbers (one per line, with or without country code):", font=ctk.CTkFont(size=12, weight="bold"))
        lbl_manual.grid(row=1, column=0, padx=20, pady=(5, 5), sticky="w")
        
        self.txt_manual = ctk.CTkTextbox(main_content, height=80, corner_radius=10)
        self.txt_manual.grid(row=2, column=0, padx=20, pady=(0, 15), sticky="ew")
        
        # Live Logs area
        lbl_logs = ctk.CTkLabel(main_content, text="Live Operation Logs:", font=ctk.CTkFont(size=12, weight="bold"))
        lbl_logs.grid(row=3, column=0, padx=20, pady=(5, 5), sticky="w")
        
        self.txt_logs = ctk.CTkTextbox(main_content, corner_radius=10, font=ctk.CTkFont(family="Consolas", size=12))
        self.txt_logs.grid(row=4, column=0, padx=20, pady=(0, 20), sticky="nsew")
        main_content.grid_rowconfigure(4, weight=3) # Allow logs box to scale dynamically

    def set_threads_val(self, val):
        self.thread_count_var.set(int(val))
        
    def on_country_select(self, val):
        code = self.country_dict.get(val, "")
        self.country_code_var.set(code)
        
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {message}\n"
        self.txt_logs.insert("end", formatted)
        self.txt_logs.see("end")
        print(formatted.strip())
        sys.stdout.flush()
        
    def update_stats_ui(self):
        self.lbl_stat_total.configure(text=f"Total: {self.stat_total}")
        self.lbl_stat_success.configure(text=f"Accounts: {self.stat_success}")
        self.lbl_stat_wa.configure(text=f"WhatsApp: {self.stat_whatsapp}")
        self.lbl_stat_sms.configure(text=f"SMS OTP: {self.stat_sms}")
        self.lbl_stat_fail.configure(text=f"Failed: {self.stat_fail}")

    def import_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv"), ("Text Files", "*.txt")])
        if not file_path:
            return
            
        try:
            numbers = []
            with open(file_path, "r", encoding="utf-8") as f:
                # Detect format (comma, semicolon, or tab)
                sample = f.read(1024)
                f.seek(0)
                dialect = csv.Sniffer().sniff(sample) if ',' in sample or ';' in sample else None
                
                if dialect:
                    reader = csv.reader(f, dialect)
                else:
                    reader = csv.reader(f)
                    
                for row in reader:
                    if not row:
                        continue
                    # Clean out non-numeric chars from row items to locate phone number
                    for item in row:
                        cleaned_item = item.strip()
                        # Handle scientific notation e.g. 2.235E+10
                        if "e" in cleaned_item.lower() and "." in cleaned_item:
                            try:
                                cleaned_item = str(int(float(cleaned_item)))
                            except Exception:
                                pass
                        
                        digits = "".join(c for c in cleaned_item if c.isdigit())
                        # Standard length check to identify phone number components (e.g. 7 to 15 digits)
                        if 7 <= len(digits) <= 15:
                            numbers.append(digits)
                            break
                            
            if numbers:
                self.imported_numbers = numbers
                self.lbl_file_status.configure(text=f"Imported {len(numbers)} numbers successfully from CSV.")
                self.log(f"Imported {len(numbers)} numbers from CSV file.")
            else:
                self.log("Warning: No valid phone numbers found in CSV file columns.")
                messagebox.showwarning("File Import", "No valid phone numbers found in the imported file.")
        except Exception as e:
            self.log(f"Error parsing CSV file: {e}")
            messagebox.showerror("File Error", f"Failed to parse CSV file: {e}")

    def clean_number(self, num, cc):
        # Remove country code if it exists at the start of the number
        digits = "".join(c for c in str(num) if c.isdigit())
        if digits.startswith(cc):
            digits = digits[len(cc):]
        return digits

    def get_noon_url_prefix(self):
        market = self.market_var.get()
        if "Saudi" in market:
            return "saudi-en", "en-sa"
        elif "UAE" in market:
            return "uae-en", "en-ae"
        else:
            return "egypt-en", "en-eg"

    def start_automation(self):
        if self.is_running:
            messagebox.showwarning("Running", "Automation is already running!")
            return
            
        # Collect numbers to process
        numbers_list = []
        
        # 1. Parse manual input
        manual_text = self.txt_manual.get("1.0", "end").strip()
        if manual_text:
            for line in manual_text.splitlines():
                digits = "".join(c for c in line.strip() if c.isdigit())
                if digits:
                    numbers_list.append(digits)
                    
        # 2. Add imported numbers if manual list is empty
        if not numbers_list and self.imported_numbers:
            numbers_list = list(self.imported_numbers)
            
        if not numbers_list:
            messagebox.showerror("Input Error", "Please import a CSV file or paste phone numbers to process!")
            return
            
        cc = self.country_code_var.get().strip()
        if not cc:
            messagebox.showerror("Config Error", "Please specify the Phone Country Code!")
            return
            
        # Populate Queue and filter duplicates
        while not self.numbers_queue.empty():
            self.numbers_queue.get()
            
        skipped_count = 0
        active_numbers = []
        for num in numbers_list:
            cleaned = self.clean_number(num, cc)
            full_num_digits = f"{cc}{cleaned}"
            if full_num_digits in self.used_numbers:
                skipped_count += 1
                continue
            active_numbers.append(num)
            self.numbers_queue.put(num)
            
        # Reset Stats
        self.stat_total = len(active_numbers)
        self.stat_success = 0
        self.stat_whatsapp = 0
        self.stat_sms = 0
        self.stat_fail = 0
        self.update_stats_ui()
        
        self.is_running = True
        self.btn_start.configure(state="disabled")
        if skipped_count > 0:
            self.log(f"[INFO] Skipped {skipped_count} numbers already processed in previous runs.")
        self.log(f"Starting execution queue: {len(active_numbers)} numbers on {self.thread_count_var.get()} threads.")
        
        # Spawn Workers
        num_threads = self.thread_count_var.get()
        self.threads = []
        for i in range(num_threads):
            t = threading.Thread(target=self.worker_thread, args=(i+1, cc), daemon=True)
            self.threads.append(t)
            t.start()

    def stop_automation(self):
        if not self.is_running:
            return
        self.is_running = False
        self.log("Stopping execution threads... (Workers will finish current tasks and terminate)")
        self.btn_start.configure(state="normal")

    def clear_used_db(self):
        if messagebox.askyesno("Confirm Clear", "Are you sure you want to clear the used numbers database? All history will be deleted."):
            self.used_numbers.clear()
            try:
                with open(self.used_numbers_file, "w") as f:
                    f.write("")
                self.log("[INFO] Used numbers database cleared successfully.")
            except Exception as e:
                self.log(f"[ERROR] Failed to clear used numbers file: {e}")

    def get_recaptcha_token_sync(self, page, action, thread_id):
        """Wait for reCAPTCHA script to load and generate a token inside the page context"""
        try:
            page.wait_for_function(
                "typeof grecaptcha !== 'undefined' && typeof grecaptcha.execute !== 'undefined'",
                timeout=15000
            )
            token = page.evaluate(
                f"grecaptcha.execute('{RECAPTCHA_KEY}', {{action: '{action}'}})"
            )
            return token
        except Exception as e:
            self.log(f"[Thread {thread_id}] reCAPTCHA load timeout/error: {e}")
            return None
    def worker_thread(self, thread_id, cc):
        CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        url_suffix, locale = self.get_noon_url_prefix()
        
        profile_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"worker_profile_{thread_id}")
        if os.path.exists(profile_dir):
            import shutil
            try:
                shutil.rmtree(profile_dir)
            except Exception:
                pass
        os.makedirs(profile_dir, exist_ok=True)
        
        with sync_playwright() as p:
            try:
                self.log(f"[Thread {thread_id}] Initializing Google Chrome instance...")
                context = p.chromium.launch_persistent_context(
                    user_data_dir=profile_dir,
                    executable_path=CHROME_PATH,
                    headless=False,
                    ignore_default_args=['--enable-automation', '--no-sandbox'],
                    args=[
                        '--lang=en-US',
                        '--accept-lang=en-US,en'
                    ],
                    viewport={'width': 1000, 'height': 700}
                )
                page = context.pages[0]
                context.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => false });")
                
                # Navigate to initialize Akamai cookies
                page.goto(f"https://account.noon.com/{url_suffix}/profile/", wait_until="domcontentloaded")
                time.sleep(1)
            except Exception as e:
                self.log(f"[Thread {thread_id}] Failed to start browser: {e}")
                self.stat_fail += 1
                self.update_stats_ui()
                return

            while self.is_running and not self.numbers_queue.empty():
                try:
                    raw_num = self.numbers_queue.get_nowait()
                except queue.Empty:
                    break
                    
                cleaned_num = self.clean_number(raw_num, cc)
                
                # Correct Phone Formatting matching the original working hybrid script:
                if cc == "20" and len(cleaned_num) >= 10:
                    # Egypt format: +20-XX-XXXXXXXX
                    carrier_part = cleaned_num[:2]
                    number_part = cleaned_num[2:]
                    formatted_phone = f"+20-{carrier_part}-{number_part}"
                else:
                    # Other countries (like Mali): +[cc]-[number] (one dash after country code!)
                    formatted_phone = f"+{cc}-{cleaned_num}"
                    
                self.log(f"[Thread {thread_id}] Processing number: {formatted_phone}")
                
                # Clear cookies to ensure fresh session
                try:
                    context.clear_cookies()
                except Exception as clear_err:
                    self.log(f"[Thread {thread_id}] Cookie clear error: {clear_err}")
                
                # Create credentials
                email = generate_custom_gmail()
                password = generate_strong_password()
                visitor_id = str(uuid.uuid4())
                
                # Create isolated curl session
                session = requests.Session(impersonate="chrome124")
                sync_cookies_to_curl(context, session)
                
                success = False
                try:
                    # 1. UI Navigation to active reCAPTCHA script context
                    page.goto(f"https://account.noon.com/{url_suffix}/profile/", wait_until="domcontentloaded")
                    time.sleep(0.5)
                    
                    login_selectors = ['text="Login/Signup"', 'text="LOGIN/SIGNUP"', 'button:has-text("Login")']
                    safe_click(page, login_selectors, timeout=4000)
                    time.sleep(0.5)
                    
                    signup_selectors = ['[data-qa="sign-up"]', 'text="Sign up"', 'text="Sign Up"']
                    safe_click(page, signup_selectors, timeout=3000)
                    time.sleep(0.5)
                    
                    # 2. Call Check-in (sign-in status check) via API requests (bypasses email OTP)
                    token_check = self.get_recaptcha_token_sync(page, "login", thread_id)
                    if not token_check:
                        self.log(f"[Thread {thread_id}] Skipped registration due to reCAPTCHA error.")
                        self.stat_fail += 1
                        self.update_stats_ui()
                        continue
                        
                    headers = {
                        "content-type": "application/json",
                        "x-locale": locale,
                        "x-platform": "web",
                        "x-visitor-id": visitor_id
                    }
                    
                    sync_cookies_to_curl(context, session)
                    resp_check = session.post(
                        "https://account.noon.com/_vs/st/mp-identity-api/auth/sign-in",
                        json={
                            "emailOrPhone": email,
                            "recaptcha": {"token": token_check, "action": "login", "key": RECAPTCHA_KEY}
                        },
                        headers=headers
                    )
                    
                    if resp_check.status_code != 200:
                        self.log(f"[Thread {thread_id}] Check-in API failed: Status {resp_check.status_code}")
                        self.stat_fail += 1
                        self.update_stats_ui()
                        continue
                        
                    # 3. Call Registration API requests
                    token_reg = self.get_recaptcha_token_sync(page, "login", thread_id)
                    sync_cookies_to_curl(context, session)
                    resp_reg = session.post(
                        "https://account.noon.com/_vs/st/mp-identity-api/auth/sign-in-with-password",
                        json={
                            "email": email,
                            "password": password,
                            "recaptcha": {"token": token_reg, "action": "login", "key": RECAPTCHA_KEY},
                            "deviceName": "Windows / Chrome"
                        },
                        headers=headers
                    )
                    
                    if resp_reg.status_code != 200:
                        self.log(f"[Thread {thread_id}] Registration failed: {resp_reg.status_code}")
                        self.stat_fail += 1
                        self.update_stats_ui()
                        continue
                        
                    self.log(f"[Thread {thread_id}] Registered account: {email}")
                    self.stat_success += 1
                    self.update_stats_ui()
                    
                    # Sync cookies back to navigate logged-in page
                    sync_cookies_to_playwright(session, context)
                    
                    # 4. Open Profile page and phone modal in UI to load reCAPTCHA context
                    page.goto(f"https://account.noon.com/{url_suffix}/profile/", wait_until="domcontentloaded")
                    time.sleep(1)
                    
                    add_selectors = ['text="Add"', 'button:has-text("Add")', 'span:has-text("Add")']
                    safe_click(page, add_selectors, timeout=4000)
                    time.sleep(0.5)
                    
                    # 5. Trigger SMS OTPs directly via API requests (matching the original hybrid script)
                    try:
                        # Call 1: Trigger first OTP (WhatsApp)
                        self.log(f"[Thread {thread_id}] Triggering OTP 1 (WhatsApp) via API requests...")
                        token_otp1 = self.get_recaptcha_token_sync(page, "primary_phone_send_otp", thread_id)
                        
                        # Only sync once from browser to curl at the beginning of the phone flow
                        sync_cookies_to_curl(context, session)
                        
                        resp_otp1 = session.post(
                            "https://account.noon.com/_vs/st/mp-identity-api/phone/send-otp",
                            json={
                                "phone": formatted_phone,
                                "isPrimary": True,
                                "recaptcha": {"token": token_otp1, "action": "primary_phone_send_otp", "key": RECAPTCHA_KEY}
                            },
                            headers=headers
                        )
                        
                        self.log(f"[Thread {thread_id}] OTP 1 Response: {resp_otp1.status_code} - {resp_otp1.text}")
                        
                        if resp_otp1.status_code == 200:
                            self.log(f"[Thread {thread_id}] OTP 1 (WhatsApp) triggered successfully.")
                            self.stat_whatsapp += 1
                            self.update_stats_ui()
                            
                            # Sync updated cookies from session back to browser context
                            sync_cookies_to_playwright(session, context)
                            
                            # Reload profile page to force the verification modal to render in the browser UI
                            self.log(f"[Thread {thread_id}] Reloading page to display verification modal...")
                            page.goto(f"https://account.noon.com/{url_suffix}/profile/", wait_until="domcontentloaded")
                            time.sleep(2)
                            
                            # Wait 16 seconds cooldown for SMS 1
                            self.log(f"[Thread {thread_id}] Waiting 16 seconds cooldown for SMS 1...")
                            time.sleep(16)
                            
                            # Call 2: Trigger first SMS (SMS 1)
                            self.log(f"[Thread {thread_id}] Triggering SMS 1 via API requests...")
                            token_otp2 = self.get_recaptcha_token_sync(page, "primary_phone_send_otp", thread_id)
                            # DO NOT call sync_cookies_to_curl here to preserve updated session cookies!
                            
                            resp_otp2 = session.post(
                                "https://account.noon.com/_vs/st/mp-identity-api/phone/send-otp",
                                json={
                                    "phone": formatted_phone,
                                    "isPrimary": True,
                                    "otpChannel": "sms",
                                    "recaptcha": {"token": token_otp2, "action": "primary_phone_send_otp", "key": RECAPTCHA_KEY}
                                },
                                headers=headers
                            )
                            
                            self.log(f"[Thread {thread_id}] SMS 1 Response: {resp_otp2.status_code} - {resp_otp2.text}")
                            
                            if resp_otp2.status_code == 200:
                                self.log(f"[Thread {thread_id}] SMS 1 triggered successfully for {formatted_phone}")
                                self.stat_sms += 1
                                self.update_stats_ui()
                                
                                # Sync updated cookies from session back to browser context
                                sync_cookies_to_playwright(session, context)
                                
                                # Wait another 16 seconds cooldown for SMS 2
                                self.log(f"[Thread {thread_id}] Waiting 16 seconds cooldown for SMS 2...")
                                time.sleep(16)
                                
                                # Call 3: Trigger second SMS (SMS 2)
                                self.log(f"[Thread {thread_id}] Triggering SMS 2 via API requests...")
                                token_otp3 = self.get_recaptcha_token_sync(page, "primary_phone_send_otp", thread_id)
                                # DO NOT call sync_cookies_to_curl here to preserve updated session cookies!
                                
                                resp_otp3 = session.post(
                                    "https://account.noon.com/_vs/st/mp-identity-api/phone/send-otp",
                                    json={
                                        "phone": formatted_phone,
                                        "isPrimary": True,
                                        "otpChannel": "sms",
                                        "recaptcha": {"token": token_otp3, "action": "primary_phone_send_otp", "key": RECAPTCHA_KEY}
                                    },
                                    headers=headers
                                )
                                
                                self.log(f"[Thread {thread_id}] SMS 2 Response: {resp_otp3.status_code} - {resp_otp3.text}")
                                
                                if resp_otp3.status_code == 200:
                                    self.log(f"[Thread {thread_id}] SMS 2 triggered successfully for {formatted_phone} [COMPLETED]")
                                    self.stat_sms += 1
                                    self.update_stats_ui()
                                    
                                    # Sync updated cookies from session back to browser context
                                    sync_cookies_to_playwright(session, context)
                                    success = True
                                    
                                    # Save to used numbers file
                                    full_digits = f"{cc}{cleaned_num}"
                                    self.used_numbers.add(full_digits)
                                    try:
                                        with open(self.used_numbers_file, "a") as uf:
                                            uf.write(f"{full_digits}\n")
                                    except Exception as u_err:
                                        self.log(f"[Thread {thread_id}] Error saving to used numbers file: {u_err}")
                                else:
                                    self.log(f"[Thread {thread_id}] SMS 2 trigger failed: {resp_otp3.status_code} - {resp_otp3.text}")
                                    self.stat_fail += 1
                                    self.update_stats_ui()
                                    
                                    # Save failed number to database to skip in future
                                    full_digits = f"{cc}{cleaned_num}"
                                    self.used_numbers.add(full_digits)
                                    try:
                                        with open(self.used_numbers_file, "a") as uf:
                                            uf.write(f"{full_digits}\n")
                                    except Exception as u_err:
                                        pass
                            else:
                                self.log(f"[Thread {thread_id}] SMS 1 trigger failed: {resp_otp2.status_code} - {resp_otp2.text}")
                                self.stat_fail += 1
                                self.update_stats_ui()
                                
                                # Save failed number to database to skip in future
                                full_digits = f"{cc}{cleaned_num}"
                                self.used_numbers.add(full_digits)
                                try:
                                    with open(self.used_numbers_file, "a") as uf:
                                        uf.write(f"{full_digits}\n")
                                except Exception as u_err:
                                    pass
                        else:
                            self.log(f"[Thread {thread_id}] OTP 1 (WhatsApp) trigger failed: {resp_otp1.status_code} - {resp_otp1.text}")
                            self.stat_fail += 1
                            self.update_stats_ui()
                            
                            # Save rate-limited or failed number to skip it in the future
                            full_digits = f"{cc}{cleaned_num}"
                            self.used_numbers.add(full_digits)
                            try:
                                with open(self.used_numbers_file, "a") as uf:
                                    uf.write(f"{full_digits}\n")
                            except Exception as u_err:
                                pass
                                
                    except Exception as otp_err:
                        self.log(f"[Thread {thread_id}] [ERROR] OTP trigger exception: {otp_err}")
                        self.stat_fail += 1
                        self.update_stats_ui()
                                
                except Exception as ex:
                    self.log(f"[Thread {thread_id}] Exception error during run: {ex}")
                    self.stat_fail += 1
                    self.update_stats_ui()
                finally:
                    self.numbers_queue.task_done()
                    
            try:
                context.close()
            except Exception:
                pass
                
        self.log(f"[Thread {thread_id}] Worker finished operations.")
        
        # Check if all queue is finished to toggle button
        if self.numbers_queue.empty() and self.is_running:
            self.is_running = False
            self.btn_start.configure(state="normal")
            self.log("All numbers in execution queue have been processed.")

if __name__ == "__main__":
    app = NoonAutomationApp()
    app.mainloop()
