from __future__ import annotations
import socket
import subprocess
import sys
import time
from pathlib import Path
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright


def _default_chrome_exe() -> str:
    if sys.platform == "win32":
        return r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    if sys.platform == "darwin":
        return "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    return "/usr/bin/google-chrome"


def _default_profile_dir() -> str:
    if sys.platform == "win32":
        import os
        return str(Path(os.environ.get("LOCALAPPDATA", "")) / "Google" / "Chrome" / "User Data")
    if sys.platform == "darwin":
        import os
        return str(Path(os.environ.get("HOME", "")) / "Library" / "Application Support" / "Google" / "Chrome")
    import os
    return str(Path(os.environ.get("HOME", "")) / ".config" / "google-chrome")


class BrowserManager:
    def __init__(
        self,
        cdp_url: str = "http://127.0.0.1:9222",
        chrome_exe: str = "",
        profile_dir: str = "",
        auto_launch: bool = True,
    ) -> None:
        self._cdp_url = cdp_url
        self._chrome_exe = chrome_exe or _default_chrome_exe()
        self._profile_dir = profile_dir or _default_profile_dir()
        self._auto_launch = auto_launch
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._proc: subprocess.Popen | None = None

    @property
    def _debug_port(self) -> int:
        # parse port from cdp_url like "http://127.0.0.1:9222"
        return int(self._cdp_url.rsplit(":", 1)[-1])

    def _debug_port_ready(self) -> bool:
        try:
            with socket.create_connection(("127.0.0.1", self._debug_port), timeout=1):
                return True
        except OSError:
            return False

    async def _launch_chrome(self) -> None:
        port = self._debug_port
        print("  Launching Chrome with debug port...")
        subprocess.run("taskkill /F /IM chrome.exe /T", shell=True, capture_output=True)
        time.sleep(3)
        for lock in ("SingletonLock", "SingletonSocket", "SingletonCookie"):
            Path(self._profile_dir, lock).unlink(missing_ok=True)

        self._proc = subprocess.Popen([
            self._chrome_exe,
            f"--remote-debugging-port={port}",
            "--remote-debugging-address=127.0.0.1",
            f"--user-data-dir={self._profile_dir}",
            "--profile-directory=Default",
            "--no-first-run",
            "--no-default-browser-check",
        ])
        deadline = time.time() + 20
        while time.time() < deadline:
            if self._debug_port_ready():
                return
            time.sleep(0.5)

        print(
            "  Could not auto-launch Chrome with debug port.\n"
            "  Please run this manually, then retry:\n"
            f'  & "{self._chrome_exe}" --remote-debugging-port={port}'
            f' --user-data-dir="{self._profile_dir}" --profile-directory=Default'
        )
        self._proc.terminate()
        self._proc = None
        raise RuntimeError(f"Chrome did not open debug port {port} within 20s")

    async def connect(self) -> Browser:
        if self._browser is not None:
            return self._browser

        if self._debug_port_ready():
            print("  Chrome already running with debug port — connecting.")
        elif self._auto_launch:
            await self._launch_chrome()
        else:
            raise RuntimeError(
                f"Chrome is not running on {self._cdp_url} and auto_launch=False"
            )

        self._playwright = await async_playwright().start()
        try:
            self._browser = await self._playwright.chromium.connect_over_cdp(self._cdp_url)
        except Exception as e:
            if self._proc:
                self._proc.terminate()
                self._proc = None
            raise RuntimeError(f"Could not connect to Chrome: {e}") from e

        return self._browser

    async def get_page(self) -> Page:
        browser = await self.connect()
        context: BrowserContext = (
            browser.contexts[0] if browser.contexts else await browser.new_context()
        )
        return context.pages[0] if context.pages else await context.new_page()

    async def new_page(self) -> Page:
        browser = await self.connect()
        context: BrowserContext = (
            browser.contexts[0] if browser.contexts else await browser.new_context()
        )
        return await context.new_page()

    async def close(self) -> None:
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        if self._proc:
            self._proc.terminate()
            self._proc = None
