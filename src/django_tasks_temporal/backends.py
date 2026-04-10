from typing import override

from django.tasks.backends.base import BaseTaskBackend
from django.tasks.base import Task, TaskResult


class TemporalTaskBackend(BaseTaskBackend):
    supports_defer = False
    supports_async_task = False
    supports_get_result = False
    supports_priority = False

    @override
    def enqueue(self, task: Task, args, kwargs) -> TaskResult:
        self.validate_task(task)
        raise NotImplemented("Enqueueing tasks is not implemented in TemporalTaskBackend.")
