import time
from datetime import timedelta, datetime

from django.tasks import task
from temporalio.exceptions import ApplicationError


@task
def add(x: int, y: int) -> int:
    return x + y

@task
def fail(message: str):
    raise ApplicationError(f"Task failed: {message}", type="CriricalFailure",  non_retryable=True)


@task
def long_running_task(run_time: timedelta) -> str:
    time.sleep(run_time.total_seconds())
    return f"Finished long running task - slept for {run_time} seconds"

@task(takes_context=True)
def task_with_context(context, value: str) -> str:
    if context.attempt <= 2:
        raise RuntimeError(f"Task failed on attempt {context.attempt}")
    return f"Task succeeded on attempt {context.attempt} with value: {value}"


@task
def time_difference(the_time_raw: str) -> str:
    the_time = datetime.fromisoformat(the_time_raw)
    now = datetime.now(tz=the_time.tzinfo)

    return str(now - the_time)