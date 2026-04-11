from __future__ import annotations

from datetime import UTC, datetime, timedelta
from time import sleep
from typing import Any

import pytest
from django.tasks import Task, TaskResult, TaskResultStatus
from django_app import tasks

from django_tasks_temporal.backends import TemporalTaskBackend

pytestmark = [pytest.mark.timeout(60)]


def test_enqueue_task(backend: TemporalTaskBackend) -> None:
    result = tasks.add.enqueue(1, 2)
    assert result is not None
    assert result.id is not None
    assert result.status == TaskResultStatus.READY
    assert result.args == [1, 2]


def wait_for_task_completion(
    backend: TemporalTaskBackend, task_id: str
) -> TaskResult[Any, Any]:
    """Helper function to wait for a task to complete and return its final status."""
    retrieved = backend.get_result(task_id)
    while True:
        if retrieved.status != TaskResultStatus.RUNNING:
            return retrieved
        sleep(0.1)
        retrieved.refresh()


def test_get_result(backend: TemporalTaskBackend) -> None:
    """Test retrieving a task result."""

    result = tasks.add.enqueue(3, 4)

    task_id = result.id
    retrieved = wait_for_task_completion(backend, task_id)

    assert retrieved.id == task_id
    assert retrieved.status == TaskResultStatus.SUCCESSFUL
    assert retrieved.args == [3, 4]
    assert retrieved.return_value == 7


def test_enqueue_task_with_context(backend: TemporalTaskBackend) -> None:
    """Test enqueuing a task with context."""
    task_with_context: Task[..., str] = tasks.task_with_context
    result = task_with_context.enqueue("Hello")
    assert result is not None
    assert result.id is not None
    assert result.status == TaskResultStatus.READY
    assert result.args == ["Hello"]


def test_get_result_with_context(backend: TemporalTaskBackend) -> None:
    """Test retrieving a task result with context."""
    task_with_context: Task[..., str] = tasks.task_with_context
    result = task_with_context.enqueue("World")

    task_id = result.id

    retrieved = wait_for_task_completion(backend, task_id)

    assert retrieved.id == task_id
    assert retrieved.status == TaskResultStatus.SUCCESSFUL
    assert retrieved.args == ["World"]
    assert retrieved.task.takes_context
    assert len(retrieved.worker_ids)
    assert retrieved.return_value == "Task succeeded on attempt 3 with value: World"

    assert len(retrieved.errors)


def test_fail_task(backend: TemporalTaskBackend) -> None:
    """Test enqueuing a task that fails."""
    result = tasks.fail.enqueue("Something went wrong")

    task_id = result.id

    retrieved = wait_for_task_completion(backend, task_id)

    assert retrieved.id == task_id
    assert retrieved.status == TaskResultStatus.FAILED
    assert retrieved.args == ["Something went wrong"]
    assert len(retrieved.errors) == 1
    assert retrieved.errors[0].exception_class_path == "CriricalFailure"


def test_defer(backend: TemporalTaskBackend) -> None:
    """Test enqueuing a task that defers itself."""
    now = datetime.now(tz=UTC)
    result = tasks.time_difference.using(run_after=now + timedelta(seconds=2)).enqueue(
        now.isoformat()
    )

    task_id = result.id

    retrieved = wait_for_task_completion(backend, task_id)

    assert retrieved.id == task_id
    assert retrieved.status == TaskResultStatus.SUCCESSFUL
    time = datetime.strptime(retrieved.return_value, "%H:%M:%S.%f")
    delta = timedelta(
        hours=time.hour,
        minutes=time.minute,
        seconds=time.second,
        microseconds=time.microsecond,
    )
    assert delta >= timedelta(seconds=2)
