import threading
import time
from typing import Dict, List, Optional, Union

import conf

PROXY_POOL = getattr(conf, "PROXY_POOL", [])
PROXY_ROTATE_INTERVAL = getattr(conf, "PROXY_ROTATE_INTERVAL", 900)


ProxyInput = Union[str, Dict[str, str]]


class ProxyManager:
    """
    Lightweight proxy/IP rotation helper.
    """

    def __init__(self, proxies: Optional[List[ProxyInput]] = None, rotate_seconds: int = 900,
                 auto_start: bool = True):
        self.proxies: List[Dict[str, str]] = self._normalize(proxies or [])
        self.rotate_seconds = max(1, int(rotate_seconds or 1))
        self._lock = threading.Lock()
        self._index = -1
        self._current: Optional[Dict[str, str]] = None
        self._last_rotated = 0.0
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

        if self.proxies and auto_start:
            self.start()

    def _normalize(self, proxies: List[ProxyInput]) -> List[Dict[str, str]]:
        normalized: List[Dict[str, str]] = []
        for proxy in proxies:
            if isinstance(proxy, str):
                normalized.append({"server": proxy})
            elif isinstance(proxy, dict) and proxy.get("server"):
                normalized.append({
                    "server": proxy["server"],
                    "username": proxy.get("username", ""),
                    "password": proxy.get("password", "")
                })
        return normalized

    def _rotate_locked(self) -> Dict[str, str]:
        self._index = (self._index + 1) % len(self.proxies)
        self._current = self.proxies[self._index]
        self._last_rotated = time.time()
        print(f"[ProxyManager] Rotated to {self._current['server']}")
        return self._current

    def get_current_proxy(self) -> Optional[Dict[str, str]]:
        if not self.proxies:
            return None

        with self._lock:
            now = time.time()
            if self._current is None or now - self._last_rotated >= self.rotate_seconds:
                self._rotate_locked()
            return dict(self._current)

    def force_rotate(self) -> Optional[Dict[str, str]]:
        if not self.proxies:
            return None
        with self._lock:
            return dict(self._rotate_locked())

    def start(self) -> None:
        if not self.proxies:
            return
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._rotation_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=1)

    def _rotation_loop(self) -> None:
        while not self._stop_event.wait(self.rotate_seconds):
            self.force_rotate()

    def status(self) -> Optional[Dict[str, str]]:
        if not self.proxies:
            return None
        with self._lock:
            if self._current is None:
                self._rotate_locked()
            masked = dict(self._current)
            if masked.get("password"):
                masked["password"] = "***"
            return masked


global_proxy_manager = ProxyManager(PROXY_POOL, PROXY_ROTATE_INTERVAL)
