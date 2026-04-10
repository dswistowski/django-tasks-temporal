from typing import cast

import pytest
from django.tasks import task_backends

from django_tasks_temporal.backends import TemporalTaskBackend


@pytest.fixture
def backend() -> TemporalTaskBackend:
    """Fixture to provide a TemporalTaskBackend instance."""
    backend = cast(TemporalTaskBackend, task_backends["default"])
    return backend
