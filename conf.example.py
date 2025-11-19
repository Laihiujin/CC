from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
XHS_SERVER = "http://127.0.0.1:11901"
LOCAL_CHROME_PATH = ""   # Optional: override if you want to use your own Chrome/Chromium binary
LOCAL_CHROME_HEADLESS = True

# Proxy/IP rotation
PROXY_POOL = [
    # Examples:
    # "http://127.0.0.1:7890",
    # {"server": "http://proxy_host:port", "username": "foo", "password": "bar"},
]
PROXY_ROTATE_INTERVAL = 900  # seconds
