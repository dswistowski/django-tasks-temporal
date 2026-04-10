import time
from datetime import timedelta

from django.tasks import task

@task
def add(x: int, y: int) -> int:
    return x + y

@task
def fail(message: str):
    raise RuntimeError(f"Task failed: {message}")


@task
def long_running_task(run_time: timedelta) -> str:
    time.sleep(run_time.total_seconds())
    return f"Finished long running task - slept for {run_time} seconds"