"""
Multi-Device Tabs Launcher using Camoufox (AsyncCamoufox Anti-Detect Engine)
Thread-based Multi-Device Spawner with Arkose Labs / Sony Fast-Pass Auth & Anti-Bot Bypass.
"""

import asyncio
from dataclasses import dataclass
import gzip
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import logging
import os
import random
import re
import sys
import threading
import time
from typing import Dict, List, Optional
import urllib.parse
import zlib

from camoufox.async_api import AsyncCamoufox

# ==============================================================================
# 1. CONFIGURATION
# ==============================================================================
PORT = 8999
HOST = "127.0.0.1"
DEFAULT_THREADS = 5
MAX_THREADS = 50

# ==============================================================================
# 2. LOGGING
# ==============================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("multi_device_camoufox")


def log_event(tab_id: str, operation: str, message: str, level: str = "info"):
    sanitized_msg = message
    sanitized_msg = re.sub(
        r"(password|token|secret|key)=([^&]+)", r"\1=***", sanitized_msg, flags=re.IGNORECASE
    )
    formatted = f"[{tab_id}] [{operation}] {sanitized_msg}"
    if level == "error":
        logger.error(formatted)
    elif level == "warning":
        logger.warning(formatted)
    elif level == "debug":
        logger.debug(formatted)
    else:
        logger.info(formatted)


# ==============================================================================
# 3. DEVICE PROFILE & CONSISTENCY ENGINE (FIREFOX / CAMOUFOX)
# ==============================================================================
WIN_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:151.0) Gecko/20100101 Firefox/151.0",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0",
]

MAC_USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:152.0) Gecko/20100101 Firefox/152.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.0; rv:152.0) Gecko/20100101 Firefox/152.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.5; rv:151.0) Gecko/20100101 Firefox/151.0",
]

LINUX_USER_AGENTS = [
    "Mozilla/5.0 (X11; Linux x86_64; rv:152.0) Gecko/20100101 Firefox/152.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:152.0) Gecko/20100101 Firefox/152.0",
]

GPUS_DESKTOP = [
    ("NVIDIA Corporation", "ANGLE (NVIDIA, NVIDIA GeForce RTX 4090 Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("NVIDIA Corporation", "ANGLE (NVIDIA, NVIDIA GeForce RTX 3070 Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("AMD", "ANGLE (AMD, AMD Radeon RX 7900 XTX Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Intel Inc.", "ANGLE (Intel, Intel(R) Iris(R) Xe Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)"),
]

GPUS_MAC = [
    ("Apple", "Apple M1"),
    ("Apple", "Apple M2"),
    ("Apple", "Apple M3"),
]

DESKTOP_RESOLUTIONS = [(1920, 1080), (2560, 1440), (1536, 864), (1440, 900), (1366, 768)]
MAC_RESOLUTIONS = [(1920, 1080), (2560, 1600), (1440, 900)]


@dataclass
class DeviceProfile:
    id: str
    os: str
    user_agent: str
    platform: str
    oscpu: str
    os_name: str
    language: str
    languages: List[str]
    timezone_offset: int
    screen_width: int
    screen_height: int
    cores: int
    ram: int
    gpu_vendor: str
    gpu_renderer: str
    seed: int


def create_deterministic_profile(profile_id: str, os_type: str, seed: int) -> DeviceProfile:
    rng = random.Random(seed)

    if os_type == "random":
        os_type = rng.choice(["win", "mac", "linux"])

    if os_type == "mac":
        ua = rng.choice(MAC_USER_AGENTS)
        platform = "MacIntel"
        oscpu = "Intel Mac OS X 10.15"
        os_name = "macOS"
        gpu_vendor, gpu_renderer = rng.choice(GPUS_MAC)
        w, h = rng.choice(MAC_RESOLUTIONS)
    elif os_type == "linux":
        ua = rng.choice(LINUX_USER_AGENTS)
        platform = "Linux x86_64"
        oscpu = "Linux x86_64"
        os_name = "Linux"
        gpu_vendor, gpu_renderer = rng.choice(GPUS_DESKTOP)
        w, h = rng.choice(DESKTOP_RESOLUTIONS)
    else:  # win
        os_type = "win"
        ua = rng.choice(WIN_USER_AGENTS)
        platform = "Win32"
        oscpu = "Windows NT 10.0; Win64; x64"
        os_name = "Windows"
        gpu_vendor, gpu_renderer = rng.choice(GPUS_DESKTOP)
        w, h = rng.choice(DESKTOP_RESOLUTIONS)

    cores = rng.choice([4, 8, 12, 16])
    ram = rng.choice([8, 16, 32])
    lang = rng.choice(["en-US", "en-GB", "en-CA", "es-ES", "fr-FR", "de-DE"])
    tz = rng.choice([-300, -240, 0, 60, 120, 180])

    profile = DeviceProfile(
        id=profile_id,
        os=os_type,
        user_agent=ua,
        platform=platform,
        oscpu=oscpu,
        os_name=os_name,
        language=lang,
        languages=[lang, "en"],
        timezone_offset=tz,
        screen_width=w,
        screen_height=h,
        cores=cores,
        ram=ram,
        gpu_vendor=gpu_vendor,
        gpu_renderer=gpu_renderer,
        seed=seed,
    )
    return profile


# ==============================================================================
# 4. TAB SESSION & RESOURCE MANAGEMENT
# ==============================================================================
@dataclass
class TabSession:
    tab_id: str
    name: str
    url: str
    profile: DeviceProfile
    status: str = "IDLE"  # IDLE, ACTIVE, LOADING, ERROR, CLOSED
    is_active: bool = False
    last_used: float = 0.0


class ResourceManager:
    def __init__(self):
        self._sessions: Dict[str, TabSession] = {}
        self._lock = threading.Lock()
        self.ram_saver_enabled = True

    def register_session(self, session: TabSession):
        with self._lock:
            session.last_used = time.time()
            self._sessions[session.tab_id] = session
            log_event(session.tab_id, "Register", f"Registered Camoufox session ({session.profile.os})")

    def unregister_session(self, tab_id: str):
        with self._lock:
            if tab_id in self._sessions:
                del self._sessions[tab_id]
                log_event(tab_id, "Unregister", "Session unregistered")

    def mark_active(self, tab_id: str):
        with self._lock:
            for tid, sess in self._sessions.items():
                sess.is_active = (tid == tab_id)
                if sess.is_active:
                    sess.status = "ACTIVE"
                    sess.last_used = time.time()
                elif sess.status == "ACTIVE":
                    sess.status = "IDLE"

    def get_session(self, tab_id: str) -> Optional[TabSession]:
        with self._lock:
            return self._sessions.get(tab_id)

    def get_all_sessions(self) -> List[TabSession]:
        with self._lock:
            return list(self._sessions.values())

    def update_tab_url(self, tab_id: str, new_url: str):
        with self._lock:
            if tab_id in self._sessions:
                self._sessions[tab_id].url = new_url
                self._sessions[tab_id].last_used = time.time()

    def get_stats(self) -> dict:
        with self._lock:
            total = len(self._sessions)
            active = sum(1 for s in self._sessions.values() if s.is_active)
            return {
                "total_tabs": total,
                "active_tabs": active,
                "ram_saver": self.ram_saver_enabled,
                "engine": "Camoufox (Anti-Detect Firefox)",
            }


RESOURCE_MANAGER = ResourceManager()
BROWSER_CONTEXT = None
MAIN_LOOP = None

# ==============================================================================
# 5. DASHBOARD UI HTML/JS
# ==============================================================================
HTML_DASHBOARD = r"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Multi-Device Tab Dashboard (Camoufox Engine)</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
        body { background: #0f172a; color: #f8fafc; height: 100vh; display: flex; flex-direction: column; overflow: hidden; }
        
        header { background: #1e293b; border-bottom: 1px solid #334155; display: flex; align-items: center; justify-content: space-between; padding: 0 12px; height: 46px; }
        .tabs-wrapper { display: flex; gap: 4px; overflow-x: auto; height: 100%; align-items: flex-end; flex: 1; }
        
        .tab-item { 
            background: #0f172a80; color: #94a3b8; padding: 6px 12px; 
            border-radius: 8px 8px 0 0; font-size: 12px; font-weight: 500; 
            cursor: pointer; border: 1px solid transparent; border-bottom: none; 
            display: flex; align-items: center; gap: 6px; user-select: none; transition: all 0.15s ease; max-width: 200px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
        }
        .tab-item:hover { background: #334155; color: #f8fafc; }
        .tab-item.active { background: #0f172a; color: #38bdf8; border-color: #334155; font-weight: 600; }
        .tab-num { background: #334155; color: #cbd5e1; font-size: 10px; padding: 2px 6px; border-radius: 10px; flex-shrink: 0; }
        .tab-item.active .tab-num { background: #0284c7; color: #ffffff; }
        
        .os-badge { font-size: 10px; padding: 1px 4px; border-radius: 4px; background: #334155; }
        .tab-item.active .os-badge { background: #0369a1; color: #e0f2fe; }

        .add-tab-btn {
            background: #334155; color: #38bdf8; border: none; padding: 4px 10px; margin-bottom: 4px;
            border-radius: 6px; font-size: 13px; font-weight: bold; cursor: pointer; transition: all 0.2s;
        }
        .add-tab-btn:hover { background: #0284c7; color: white; }

        .thread-spawner {
            display: flex; align-items: center; gap: 6px; background: #0f172a; border: 1px solid #475569;
            padding: 3px 8px; border-radius: 6px; margin-bottom: 2px;
        }
        .thread-input {
            width: 45px; background: #1e293b; border: 1px solid #334155; color: #38bdf8;
            text-align: center; border-radius: 4px; font-weight: bold; font-size: 12px; padding: 2px; outline: none;
        }

        .controls { display: flex; gap: 8px; align-items: center; }
        .btn { 
            background: #3b82f6; color: white; border: none; padding: 5px 12px; 
            border-radius: 6px; font-size: 12px; font-weight: 600; cursor: pointer; transition: all 0.2s; 
        }
        .btn:hover { background: #2563eb; }
        .btn-mode { background: #1e293b; border: 1px solid #475569; color: #cbd5e1; }
        .btn-mode:hover { background: #334155; color: #ffffff; }
        .btn-mode.active { background: #0284c7; border-color: #38bdf8; color: #ffffff; }
        
        .btn-ram { background: #059669; border: 1px solid #10b981; color: #ecfdf5; }
        .btn-ram.off { background: #dc2626; border-color: #ef4444; color: #fef2f2; }

        main { flex: 1; position: relative; background: #020617; width: 100%; height: calc(100vh - 46px); }
        
        .tab-panel { 
            width: 100%; height: 100%; display: none; position: absolute; top: 0; left: 0; flex-direction: column; 
        }
        .tab-panel.active { display: flex; }
        
        .panel-header { 
            background: #1e293b; color: #e2e8f0; padding: 5px 10px; font-size: 12px; font-weight: 600; 
            display: flex; gap: 6px; align-items: center; border-bottom: 1px solid #334155; 
        }
        .nav-btn {
            background: #334155; color: #e2e8f0; border: 1px solid #475569; border-radius: 4px;
            padding: 3px 7px; font-size: 11px; cursor: pointer; transition: all 0.15s;
        }
        .nav-btn:hover { background: #475569; color: #38bdf8; }
        
        .os-select {
            background: #0f172a; border: 1px solid #475569; color: #38bdf8;
            padding: 3px 6px; border-radius: 6px; font-size: 11px; font-weight: 600; cursor: pointer; outline: none;
        }

        .seed-badge {
            background: #0284c730; color: #38bdf8; border: 1px solid #0284c760;
            padding: 2px 6px; border-radius: 4px; font-size: 10px; font-family: monospace;
        }

        .url-input {
            flex: 1; background: #0f172a; border: 1px solid #475569; color: #f8fafc;
            padding: 4px 10px; border-radius: 6px; font-size: 12px; outline: none; transition: border-color 0.2s;
        }
        .url-input:focus { border-color: #38bdf8; box-shadow: 0 0 0 2px #0284c740; }

        iframe { flex: 1; width: 100%; border: none; background: #ffffff; }
        
        main.grid-layout { display: grid; grid-template-columns: repeat(auto-fit, minmax(360px, 1fr)); gap: 6px; padding: 6px; background: #0f172a; overflow-y: auto; }
        main.grid-layout .tab-panel { display: flex !important; position: relative; border-radius: 8px; overflow: hidden; border: 1px solid #334155; min-height: 400px; }
    </style>
</head>
<body>
    <header>
        <div class="tabs-wrapper" id="tabsHeader"></div>
        <div class="thread-spawner">
            <span style="font-size: 11px; font-weight: 600; color: #94a3b8;">🧵 Threads:</span>
            <input type="number" id="threadCountInput" class="thread-input" value="5" min="1" max="50">
            <button class="btn" style="padding: 3px 8px; font-size: 11px;" onclick="spawnThreadsFromInput()">Launch 🚀</button>
        </div>
        <button class="add-tab-btn" onclick="addNewTab()" title="Add Single Device Tab" style="margin-left: 6px;">+</button>
        <div class="controls" style="margin-left: 8px;">
            <button class="btn btn-ram" id="ramSaverBtn" onclick="toggleRamSaver()" title="Toggle Low-RAM Blocker">⚡ RAM Saver: ON</button>
            <button class="btn btn-mode" id="toggleGridBtn" onclick="toggleLayout()">Split / Grid View 🔲</button>
            <button class="btn" style="background: #dc2626;" onclick="clearAllCookies()" title="Clear storage">🗑️ Clear Storage</button>
        </div>
    </header>

    <main id="mainContent"></main>

    <script>
        let tabs = [];
        let currentActive = '';
        let isGrid = false;
        let ramSaverActive = true;

        const SONY_DIRECT_SIGNUP = 'https://id.sonyentertainmentnetwork.com/id/create_account_ca/?ui=pr&response_type=token&scope=openid%3Actry_code%20openid%3Alang&client_id=6a7bc7c8-8714-4d0f-b576-18442391eb14&service_entity=urn%3Aservice-entity%3Apsn&tp_psn=true';

        const defaultSites = [
            SONY_DIRECT_SIGNUP,
            'https://pixelscan.net',
            'https://bot.sannysoft.com',
            'https://browserleaks.com/ip',
            'https://whatismyos.com'
        ];

        function getFullUrl(rawUrl, os, seed) {
            let url = rawUrl;
            url = url.replace(/[\?&]__os=[^&]+/g, '').replace(/[\?&]__seed=[^&]+/g, '');
            const sep = url.includes('?') ? '&' : '?';
            return `${url}${sep}__os=${os}&__seed=${seed}`;
        }

        function getOsBadgeLabel(os) {
            switch(os) {
                case 'mac': return '🍎 Mac';
                case 'linux': return '🐧 Linux';
                default: return '🪟 Win';
            }
        }

        function renderTabsHeader() {
            const header = document.getElementById('tabsHeader');
            header.innerHTML = '';

            tabs.forEach((tab, idx) => {
                const btn = document.createElement('div');
                btn.className = `tab-item ${tab.id === currentActive ? 'active' : ''}`;
                btn.id = `btn-${tab.id}`;
                btn.onclick = () => selectTab(tab.id);
                btn.innerHTML = `
                    <span>Thread #${idx + 1}</span>
                    <span class="os-badge">${getOsBadgeLabel(tab.os)}</span>
                `;
                header.appendChild(btn);
            });
        }

        function createPanel(tab) {
            const container = document.getElementById('mainContent');
            const panel = document.createElement('div');
            panel.className = `tab-panel ${tab.id === currentActive ? 'active' : ''}`;
            panel.id = `panel-${tab.id}`;

            const bar = document.createElement('div');
            bar.className = 'panel-header';
            bar.innerHTML = `
                <button class="nav-btn" onclick="navBack('${tab.id}')" title="Back">◀</button>
                <button class="nav-btn" onclick="navForward('${tab.id}')" title="Forward">▶</button>
                <button class="nav-btn" onclick="refreshTab('${tab.id}')" title="Refresh">🔄 Refresh</button>
                <select class="os-select" id="os-${tab.id}" onchange="changeTabOS('${tab.id}')">
                    <option value="win" ${tab.os === 'win' ? 'selected' : ''}>🪟 Win</option>
                    <option value="mac" ${tab.os === 'mac' ? 'selected' : ''}>🍎 Mac</option>
                    <option value="linux" ${tab.os === 'linux' ? 'selected' : ''}>🐧 Linux</option>
                </select>
                <span class="seed-badge" id="seed-badge-${tab.id}">🎲 Device #${tab.seed}</span>
                <input type="text" class="url-input" id="url-${tab.id}" value="${tab.url}" onkeydown="handleUrlKey(event, '${tab.id}')" placeholder="Type URL...">
                <button class="btn" style="padding: 3px 8px; font-size: 11px;" onclick="navigateTab('${tab.id}')">Go 🔍</button>
            `;
            panel.appendChild(bar);

            const frame = document.createElement('iframe');
            frame.id = `iframe-${tab.id}`;
            frame.loading = 'eager';
            frame.src = getFullUrl(tab.url, tab.os, tab.seed);
            frame.title = tab.name;
            panel.appendChild(frame);

            container.appendChild(panel);
        }

        function spawnThreads(count, targetUrl = '') {
            tabs = [];
            document.getElementById('mainContent').innerHTML = '';
            document.getElementById('tabsHeader').innerHTML = '';

            const osTypes = ['win', 'win', 'mac', 'linux', 'win'];

            for (let i = 0; i < count; i++) {
                const threadId = `t${i + 1}`;
                const url = targetUrl || defaultSites[i % defaultSites.length];
                const os = osTypes[i % osTypes.length];
                const seed = 100000 + (i * 15485863) % 900000;

                const tabObj = {
                    id: threadId,
                    name: `Thread #${i + 1}`,
                    url: url,
                    os: os,
                    seed: seed
                };

                tabs.push(tabObj);
                createPanel(tabObj);
            }

            currentActive = 't1';
            renderTabsHeader();
            selectTab('t1');

            fetch('/api/sync-tabs', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(tabs)
            }).catch(()=>{});
        }

        function spawnThreadsFromInput() {
            const input = document.getElementById('threadCountInput');
            const count = parseInt(input.value) || 5;
            spawnThreads(Math.min(count, 50));
        }

        function init() {
            spawnThreads(5);
        }

        function selectTab(id) {
            if (isGrid) return;
            currentActive = id;
            document.querySelectorAll('.tab-item').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab-panel').forEach(el => el.classList.remove('active'));

            const activeBtn = document.getElementById(`btn-${id}`);
            const activePanel = document.getElementById(`panel-${id}`);
            if (activeBtn) activeBtn.classList.add('active');
            if (activePanel) activePanel.classList.add('active');

            fetch(`/api/tab/activate?id=${id}`).catch(()=>{});
        }

        function changeTabOS(id) {
            const select = document.getElementById(`os-${id}`);
            const tabObj = tabs.find(t => t.id === id);
            if (select && tabObj) {
                tabObj.os = select.value;
                refreshTab(id);
            }
        }

        function parseInputUrl(input) {
            input = input.trim();
            if (!input) return 'about:blank';
            if (input.startsWith('http://') || input.startsWith('https://')) {
                return input;
            }
            if (input.includes('.') && !input.includes(' ')) {
                return 'https://' + input;
            }
            return 'https://duckduckgo.com/?q=' + encodeURIComponent(input);
        }

        function navigateTab(id) {
            const input = document.getElementById(`url-${id}`);
            const frame = document.getElementById(`iframe-${id}`);
            const tabObj = tabs.find(t => t.id === id);
            if (input && frame && tabObj) {
                let targetUrl = parseInputUrl(input.value);
                input.value = targetUrl;
                tabObj.url = targetUrl;
                frame.src = getFullUrl(targetUrl, tabObj.os, tabObj.seed);
            }
        }

        function handleUrlKey(event, id) {
            if (event.key === 'Enter') {
                navigateTab(id);
            }
        }

        function refreshTab(id) {
            const frame = document.getElementById(`iframe-${id}`);
            const tabObj = tabs.find(t => t.id === id);
            if (frame && tabObj) {
                const targetSrc = getFullUrl(tabObj.url, tabObj.os, tabObj.seed);
                frame.src = 'about:blank';
                setTimeout(() => { frame.src = targetSrc; }, 50);
            }
        }

        function navBack(id) {
            const frame = document.getElementById(`iframe-${id}`);
            try { frame.contentWindow.history.back(); } catch(e){ refreshTab(id); }
        }

        function navForward(id) {
            const frame = document.getElementById(`iframe-${id}`);
            try { frame.contentWindow.history.forward(); } catch(e){}
        }

        function addNewTab(targetUrl = SONY_DIRECT_SIGNUP) {
            const newId = 't' + (tabs.length + 1);
            const seed = Math.floor(Math.random() * 900000) + 100000;
            const newTab = { id: newId, name: `Thread #${tabs.length+1}`, url: targetUrl, os: 'win', seed: seed };
            tabs.push(newTab);
            renderTabsHeader();
            createPanel(newTab);
            selectTab(newId);
        }

        function toggleRamSaver() {
            ramSaverActive = !ramSaverActive;
            const btn = document.getElementById('ramSaverBtn');
            if (ramSaverActive) {
                btn.textContent = '⚡ RAM Saver: ON';
                btn.classList.remove('off');
            } else {
                btn.textContent = '⚡ RAM Saver: OFF';
                btn.classList.add('off');
            }
            fetch('/api/toggle-ram-saver?state=' + (ramSaverActive ? '1' : '0')).catch(()=>{});
        }

        function toggleLayout() {
            isGrid = !isGrid;
            const main = document.getElementById('mainContent');
            const btn = document.getElementById('toggleGridBtn');

            if (isGrid) {
                main.classList.add('grid-layout');
                btn.textContent = 'Single Tab View 📑';
                btn.classList.add('active');
            } else {
                main.classList.remove('grid-layout');
                btn.textContent = 'Split / Grid View 🔲';
                btn.classList.remove('active');
                selectTab(currentActive);
            }
        }

        function clearAllCookies() {
            if (!confirm('Clear all session cookies and storage?')) return;
            fetch('/api/clear-all-cookies')
                .then(res => res.json())
                .then(data => {
                    tabs.forEach(tab => {
                        const frame = document.getElementById(`iframe-${tab.id}`);
                        if (frame) {
                            const currentSrc = frame.src;
                            frame.src = 'about:blank';
                            setTimeout(() => { frame.src = currentSrc; }, 100);
                        }
                    });
                    alert('All session storage & cookies cleared successfully.');
                })
                .catch(err => {
                    alert('Error clearing cookies.');
                });
        }

        window.onload = init;
    </script>
</body>
</html>
"""

# ==============================================================================
# 6. LOCAL HTTP SERVER & CONTROL API
# ==============================================================================
class ServerHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/api/sync-tabs":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            try:
                data = json.loads(body)
                for tab in data:
                    prof = create_deterministic_profile(tab["id"], tab.get("os", "win"), int(tab.get("seed", 100000)))
                    sess = TabSession(tab_id=tab["id"], name=tab["name"], url=tab["url"], profile=prof)
                    RESOURCE_MANAGER.register_session(sess)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"status":"ok"}')
            except Exception as e:
                self.send_response(400)
                self.end_headers()
            return
        self.send_response(404)
        self.end_headers()

    def do_GET(self):
        if self.path.startswith("/api/toggle-ram-saver"):
            RESOURCE_MANAGER.ram_saver_enabled = "state=1" in self.path
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')
            return

        if self.path.startswith("/api/tab/activate"):
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)
            tab_id = params.get("id", [""])[0]
            if tab_id:
                RESOURCE_MANAGER.mark_active(tab_id)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')
            return

        if self.path.startswith("/api/stats"):
            stats = RESOURCE_MANAGER.get_stats()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(stats).encode())
            return

        if self.path == "/api/clear-all-cookies":
            if BROWSER_CONTEXT and MAIN_LOOP and not MAIN_LOOP.is_closed():
                try:
                    future = asyncio.run_coroutine_threadsafe(
                        BROWSER_CONTEXT.clear_cookies(), MAIN_LOOP
                    )
                    future.result(timeout=5)
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(b'{"status":"success","message":"All browser cookies cleared"}')
                except Exception as e:
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode())
            else:
                self.send_response(503)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"status":"error","message":"Browser context not ready"}')
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(HTML_DASHBOARD.encode("utf-8"))

    def log_message(self, format, *args):
        pass


def run_local_server():
    server = ThreadingHTTPServer((HOST, PORT), ServerHandler)
    log_event("Server", "Init", f"Dashboard control server listening on http://{HOST}:{PORT}")
    server.serve_forever()


# ==============================================================================
# 7. BROWSER INITIALIZATION & REQUEST ROUTING (CAMOUFOX ENGINE)
# ==============================================================================
async def launch_single_window_tabs(threads_count=5):
    print("=" * 60)
    print(f"Launching Multi-Device Tabs ({threads_count} Threads in AsyncCamoufox)...")
    print(f"Dashboard bound to: http://{HOST}:{PORT}")
    print("=" * 60)

    server_thread = threading.Thread(target=run_local_server, daemon=True)
    server_thread.start()

    firefox_prefs = {
        "dom.webdriver.enabled": False,
        "useAutomationExtension": False,
        "marionette.enabled": False,
        "network.cookie.cookieBehavior": 0,
        "privacy.partition.network_state": False,
        "network.cookie.sameSite.laxByDefault": False,
        "privacy.firstparty.isolate": False,
        "privacy.resistFingerprinting": False,
        "privacy.resistFingerprinting.letterboxing": False,
        "webgl.disabled": False,
        "webgl.enable-webgl2": True,
        "gfx.canvas.azure.backends": "direct2d1.1,cairo,skia",
        "dom.webaudio.enabled": True,
        "media.navigator.enabled": True,
        "network.http.http2.enabled": True,
        "network.http.http3.enabled": True,
        "browser.cache.disk.enable": True,
        "browser.cache.memory.enable": True,
        "browser.sessionhistory.max_entries": 10,
        "dom.serviceWorkers.enabled": True,
        "dom.storage.enabled": True,
        "indexedDB.enabled": True,
        "javascript.options.wasm": True,
        "toolkit.telemetry.enabled": False,
        "toolkit.telemetry.unified": False,
        "dom.ipc.processCount": 1,
    }

    async with AsyncCamoufox(headless=False, firefox_user_prefs=firefox_prefs) as browser:
        global BROWSER_CONTEXT, MAIN_LOOP
        MAIN_LOOP = asyncio.get_running_loop()

        context = await browser.new_context(
            viewport={"width": 1300, "height": 850},
            ignore_https_errors=True
        )
        BROWSER_CONTEXT = context

        page = await context.new_page()

        async def handle_route(route):
            raw_url = route.request.url
            url_lower = raw_url.lower()

            # Immediate bypass for localhost / dashboard requests
            if f"{HOST}:{PORT}" in raw_url or "localhost" in url_lower or "127.0.0.1" in url_lower:
                await route.continue_()
                return

            req_type = route.request.resource_type

            # Resource Management / RAM Saver
            if RESOURCE_MANAGER.ram_saver_enabled:
                is_essential = any(d in url_lower for d in ["sony", "playstation", "arkoselabs", "funcaptcha", "google", "recaptcha", "pixelscan", "sannysoft", "browserleaks", "whatismyos", "duckduckgo"])
                if not is_essential and req_type in ["image", "media", "font"]:
                    await route.abort()
                    return

            clean_url = re.sub(r"[?&]__os=[^&]*", "", raw_url)
            clean_url = re.sub(r"[?&]__seed=[^&]*", "", clean_url)
            if "?" not in clean_url and "&" in clean_url:
                clean_url = clean_url.replace("&", "?", 1)

            if req_type in ["document", "subframe"]:
                try:
                    response = await route.fetch(url=clean_url)
                    headers = response.headers.copy()

                    # Strip headers blocking iframes
                    for h in ["x-frame-options", "content-security-policy", "frame-ancestors", "content-length"]:
                        headers.pop(h, None)

                    if "set-cookie" in headers:
                        headers["set-cookie"] = headers["set-cookie"].replace("SameSite=Strict", "SameSite=None; Secure")

                    await route.fulfill(response=response, headers=headers)
                    return
                except Exception as e:
                    log_event("Router", "FetchError", f"Failed fetching {clean_url}: {e}", "warning")

            await route.continue_(url=clean_url)

        await page.route("**/*", handle_route)

        log_event("Browser", "Nav", f"Navigating to dashboard: http://{HOST}:{PORT}")
        await page.goto(f"http://{HOST}:{PORT}", wait_until="domcontentloaded")

        if threads_count != 5:
            await page.evaluate(f"spawnThreads({threads_count})")

        print(f"\n[+] Success! {threads_count} Threads running in single Camoufox browser window.")
        await asyncio.to_thread(input, "\nPress ENTER in this terminal to close the browser...")


# ==============================================================================
# 8. APPLICATION ENTRY POINT
# ==============================================================================
if __name__ == "__main__":
    t_count = DEFAULT_THREADS
    if len(sys.argv) > 1:
        try:
            t_count = int(sys.argv[1])
        except ValueError:
            pass
    try:
        asyncio.run(launch_single_window_tabs(t_count))
    except KeyboardInterrupt:
        print("\nBrowser closed by user.")
