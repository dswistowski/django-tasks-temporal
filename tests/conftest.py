import pytest
from django.tasks import task_backends
from django_tasks_temporal.backends import TemporalTaskBackend


@pytest.fixture
def backend() -> TemporalTaskBackend:
    """Fixture to provide a TemporalTaskBackend instance."""
    backend = task_backends["default"]
    return backend