from datetime import datetime, timezone


def now_iso():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def journey_stamp():
    return datetime.now().astimezone().strftime("%Y-%m-%dT%H-%M-%S")


def utc_hash_time():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
