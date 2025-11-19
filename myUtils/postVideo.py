import asyncio
from pathlib import Path
from typing import Iterable, List

from conf import BASE_DIR
from uploader.douyin_uploader.main import DouYinVideo
from uploader.ks_uploader.main import KSVideo
from uploader.tencent_uploader.main import TencentVideo
from uploader.xiaohongshu_uploader.main import XiaoHongShuVideo
from utils.constant import TencentZoneTypes
from utils.files_times import generate_schedule_time_next_day

def _generate_publish_times(file_count, enable_timer, videos_per_day, daily_times, start_days):
    if file_count == 0:
        return []
    videos_per_day = videos_per_day or 1
    if enable_timer:
        return generate_schedule_time_next_day(file_count, videos_per_day, daily_times, start_days)
    return [0 for _ in range(file_count)]


def _resolve_paths(files: Iterable[str], folder: str) -> List[Path]:
    return [Path(BASE_DIR / folder / file) for file in files]


def _dispatch_plan(files: List[Path], accounts: List[Path], publish_times: List[object],
                   mode: str):
    if not files or not accounts:
        return iter([])

    mode = (mode or "replicate").lower()
    if mode == "round_robin":
        def iterator():
            for index, file in enumerate(files):
                account = accounts[index % len(accounts)]
                yield file, account, publish_times[index]
        return iterator()
    if mode == "one_to_one":
        def iterator():
            for index in range(min(len(files), len(accounts))):
                yield files[index], accounts[index], publish_times[index]
        return iterator()

    # default: replicate each file to all accounts
    def iterator():
        for index, file in enumerate(files):
            for account in accounts:
                yield file, account, publish_times[index]
    return iterator()


def post_video_tencent(title, files, tags, account_file, category=TencentZoneTypes.LIFESTYLE.value, enableTimer=False,
                       videos_per_day=1, daily_times=None, start_days=0, is_draft=False, distribution_mode="replicate"):
    account_file = _resolve_paths(account_file, "cookiesFile")
    files = _resolve_paths(files, "videoFile")
    publish_datetimes = _generate_publish_times(len(files), enableTimer, videos_per_day, daily_times, start_days)

    for file_path, cookie, publish_time in _dispatch_plan(files, account_file, publish_datetimes, distribution_mode):
        print(f"文件路径{file_path}")
        print(f"视频文件名：{file_path}")
        print(f"标题：{title}")
        print(f"Hashtag：{tags}")
        app = TencentVideo(title, str(file_path), tags, publish_time, cookie, category, is_draft)
        asyncio.run(app.main(), debug=False)


def post_video_DouYin(title, files, tags, account_file, category=TencentZoneTypes.LIFESTYLE.value, enableTimer=False,
                      videos_per_day=1, daily_times=None, start_days=0, thumbnail_path='',
                      productLink='', productTitle='', distribution_mode="replicate"):
    account_file = _resolve_paths(account_file, "cookiesFile")
    files = _resolve_paths(files, "videoFile")
    publish_datetimes = _generate_publish_times(len(files), enableTimer, videos_per_day, daily_times, start_days)

    for file_path, cookie, publish_time in _dispatch_plan(files, account_file, publish_datetimes, distribution_mode):
        print(f"文件路径{file_path}")
        print(f"视频文件名：{file_path}")
        print(f"标题：{title}")
        print(f"Hashtag：{tags}")
        app = DouYinVideo(title, str(file_path), tags, publish_time, cookie, thumbnail_path, productLink, productTitle)
        asyncio.run(app.main(), debug=False)


def post_video_ks(title, files, tags, account_file, category=TencentZoneTypes.LIFESTYLE.value, enableTimer=False,
                  videos_per_day=1, daily_times=None, start_days=0, distribution_mode="replicate"):
    account_file = _resolve_paths(account_file, "cookiesFile")
    files = _resolve_paths(files, "videoFile")
    publish_datetimes = _generate_publish_times(len(files), enableTimer, videos_per_day, daily_times, start_days)

    for file_path, cookie, publish_time in _dispatch_plan(files, account_file, publish_datetimes, distribution_mode):
        print(f"文件路径{file_path}")
        print(f"视频文件名：{file_path}")
        print(f"标题：{title}")
        print(f"Hashtag：{tags}")
        app = KSVideo(title, str(file_path), tags, publish_time, cookie)
        asyncio.run(app.main(), debug=False)


def post_video_xhs(title, files, tags, account_file, category=TencentZoneTypes.LIFESTYLE.value, enableTimer=False,
                   videos_per_day=1, daily_times=None, start_days=0, distribution_mode="replicate"):
    account_file = _resolve_paths(account_file, "cookiesFile")
    files = _resolve_paths(files, "videoFile")
    publish_datetimes = _generate_publish_times(len(files), enableTimer, videos_per_day, daily_times, start_days)

    for file_path, cookie, publish_time in _dispatch_plan(files, account_file, publish_datetimes, distribution_mode):
        print(f"视频文件名：{file_path}")
        print(f"标题：{title}")
        print(f"Hashtag：{tags}")
        app = XiaoHongShuVideo(title, str(file_path), tags, publish_time, cookie)
        asyncio.run(app.main(), debug=False)
