import time
from flask import request


def get_current_time() -> int:
    "Get current time in seconds, unix format"

    return int(time.time())


def get_time_hours_ago(hours: int) -> int:
    "Get time X hours ago, unix format"

    return int(time.time()) - (hours * 60 * 60)


def get_time_seconds_ago(seconds: int) -> int:
    "Get time X seconds ago, unix format"

    return int(time.time()) - seconds


def get_remote_ip() -> str:
    "Get the IP addres of the latest request."

    if "X-Forwarded-For" in request.headers:
        return request.headers["X-Forwarded-For"]
    else:
        return request.remote_addr
