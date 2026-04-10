from __future__ import annotations

from datetime import datetime

from django.tasks import TaskContext, task
from temporalio.exceptions import ApplicationError


@task
def add(x: int, y: int) -> int:
    return x + y


@task
def fail(message: str) -> None:
    raise ApplicationError(
        f"Task failed: {message}", type="CriricalFailure", non_retryable=True
    )


@task(takes_context=True)
def task_with_context(context: TaskContext[..., str], value: str) -> str:
    if context.attempt <= 2:
        raise RuntimeError(f"Task failed on attempt {context.attempt}")
    return f"Task succeeded on attempt {context.attempt} with value: {value}"


@task
def time_difference(the_time_raw: str) -> str:
    the_time = datetime.fromisoformat(the_time_raw)
    now = datetime.now(tz=the_time.tzinfo)

    return str(now - the_time)
