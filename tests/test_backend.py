from django.tasks import TaskResultStatus

from django_app import tasks
from django_tasks_temporal.backends import TemporalTaskBackend


def test_enqueue_task(backend: TemporalTaskBackend):
    result = tasks.add.enqueue(1, 2)
    assert result is not None
    assert result.id is not None
    assert result.status == TaskResultStatus.READY
    assert result.args == [1, 2]


def test_get_result(backend: TemporalTaskBackend):
    """Test retrieving a task result."""

    result = tasks.add.enqueue(3, 4)

    task_id = result.id

    retrieved = backend.get_result(task_id)

    assert retrieved.id == task_id
    assert retrieved.status == TaskResultStatus.READY
    assert retrieved.args == [3, 4]