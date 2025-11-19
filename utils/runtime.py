from pathlib import Path
from typing import Iterable

from conf import BASE_DIR

DEFAULT_RUNTIME_DIRS = (
    "cookies",
    "cookiesFile",
    "videoFile",
    "logs",
)


def ensure_runtime_directories(extra_dirs: Iterable[str] | None = None) -> None:
    """
    Make sure frequently accessed folders exist to reduce manual setup.
    """
    folders = set(DEFAULT_RUNTIME_DIRS)
    if extra_dirs:
        folders.update(extra_dirs)

    for folder in folders:
        Path(BASE_DIR / folder).mkdir(parents=True, exist_ok=True)
