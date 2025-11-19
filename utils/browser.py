import os
import platform
from functools import lru_cache
from pathlib import Path
from typing import Dict, Optional

from conf import BASE_DIR, LOCAL_CHROME_PATH, LOCAL_CHROME_HEADLESS
from utils.proxy_manager import global_proxy_manager

_PLATFORM = platform.system().lower()


def _candidate_paths() -> list[str]:
    candidates = []
    env_path = os.environ.get("SAU_CHROME_PATH")
    if env_path:
        candidates.append(env_path)

    if LOCAL_CHROME_PATH:
        candidates.append(LOCAL_CHROME_PATH)

    if _PLATFORM == "darwin":
        candidates.extend([
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary",
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        ])
    elif _PLATFORM == "windows":
        program_files = os.environ.get("PROGRAMFILES", r"C:\Program Files")
        program_files_x86 = os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)")
        candidates.extend([
            rf"{program_files}\Google\Chrome\Application\chrome.exe",
            rf"{program_files_x86}\Google\Chrome\Application\chrome.exe",
            rf"{program_files}\Microsoft\Edge\Application\msedge.exe",
            rf"{program_files_x86}\Microsoft\Edge\Application\msedge.exe",
        ])
    else:
        candidates.extend([
            "/usr/bin/google-chrome",
            "/usr/bin/chromium-browser",
            "/usr/bin/chromium",
        ])

    # Last fallback: packaged chromium installed via Playwright
    candidates.append(str(Path(BASE_DIR / "chrome-linux" / "chrome")))

    return candidates


@lru_cache
def resolve_chrome_executable() -> Optional[str]:
    for candidate in _candidate_paths():
        candidate_path = Path(candidate).expanduser()
        if candidate_path.exists():
            return str(candidate_path)
    return None


def build_launch_options(headless: bool | None = None, extra: Optional[Dict] = None) -> Dict:
    """
    Compose launch args with builtin browser detection and proxy rotation.
    """
    options: Dict = {
        "headless": LOCAL_CHROME_HEADLESS if headless is None else headless
    }

    executable = resolve_chrome_executable()
    if executable:
        options["executable_path"] = executable

    proxy = global_proxy_manager.get_current_proxy()
    if proxy:
        options["proxy"] = proxy

    if extra:
        options.update(extra)
    return options
