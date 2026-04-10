from datetime import timedelta, timezone, datetime
from time import sleep

import pytest
from django.tasks import TaskResultStatus

from django_app import tasks
from django_tasks_temporal.backends import TemporalTaskBackend


def test_enqueue_task(backend: TemporalTaskBackend):
    result = tasks.add.enqueue(1, 2)
    assert result is not None
    assert result.id is not None
    assert result.status == TaskResultStatus.READY
    assert result.args == [1, 2]

@pytest.mark.timeout(10)
def test_get_result(backend: TemporalTaskBackend):
    """Test retrieving a task result."""

    result = tasks.add.enqueue(3, 4)

    task_id = result.id
    while True:
        retrieved = backend.get_result(task_id)
        if retrieved.status != TaskResultStatus.RUNNING:
            break

    assert retrieved.id == task_id
    assert retrieved.status == TaskResultStatus.SUCCESSFUL
    assert retrieved.args == [3, 4]
    assert retrieved.return_value == 7

def test_enqueue_task_with_context(backend: TemporalTaskBackend):
    """Test enqueuing a task with context."""
    result = tasks.task_with_context.enqueue("Hello")
    assert result is not None
    assert result.id is not None
    assert result.status == TaskResultStatus.READY
    assert result.args == ["Hello"]

@pytest.mark.timeout(20)
def test_get_result_with_context(backend: TemporalTaskBackend):
    """Test retrieving a task result with context."""
    result = tasks.task_with_context.enqueue("World")

    task_id = result.id

    while True:
        retrieved = backend.get_result(task_id)
        if retrieved.status != TaskResultStatus.RUNNING:
            break
        sleep(0.1)

    assert retrieved.id == task_id
    assert retrieved.status == TaskResultStatus.SUCCESSFUL
    assert retrieved.args == ["World"]
    assert retrieved.task.takes_context
    assert len(retrieved.worker_ids)
    assert retrieved.return_value == "Task succeeded on attempt 3 with value: World"

    assert len(retrieved.errors)


@pytest.mark.timeout(10)
def test_fail_task(backend: TemporalTaskBackend):
    """Test enqueuing a task that fails."""
    result = tasks.fail.enqueue("Something went wrong")

    task_id = result.id

    while True:
        retrieved = backend.get_result(task_id)
        if retrieved.status != TaskResultStatus.RUNNING:
            break
        sleep(0.1)

    assert retrieved.id == task_id
    assert retrieved.status == TaskResultStatus.FAILED
    assert retrieved.args == ["Something went wrong"]
    assert len(retrieved.errors) == 1
    assert retrieved.errors[0].exception_class_path == "CriricalFailure"

@pytest.mark.timeout(10)
def test_defer(backend: TemporalTaskBackend):
    """Test enqueuing a task that defers itself."""
    now = datetime.now(tz=timezone.utc)
    result = tasks.time_difference.using(run_after=now + timedelta(seconds=2)).enqueue(now.isoformat())

    task_id = result.id

    while True:
        retrieved = backend.get_result(task_id)
        if retrieved.status != TaskResultStatus.RUNNING:
            break
        sleep(0.1)

    assert retrieved.id == task_id
    assert retrieved.status == TaskResultStatus.SUCCESSFUL
    time = datetime.strptime(retrieved.return_value, "%H:%M:%S.%f")
    delta = timedelta(hours=time.hour, minutes=time.minute, seconds=time.second, microseconds=time.microsecond)
    assert delta >= timedelta(seconds=2)

