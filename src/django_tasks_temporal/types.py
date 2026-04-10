from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Mapping, Any, Callable

from django.tasks import Task
from django.utils.module_loading import import_string

def lazy_django_debug() -> bool:
    from django.conf import settings
    return settings.DEBUG

@dataclass(frozen=True)
class Options:
    target_host: str
    debug_mode: bool = False
    namespace: str = "default"
    task_queue: str = "django-tasks"
    max_concurrent_workflow_tasks: int | None = None
    max_concurrent_activities: int | None = None

    @classmethod
    def from_options(cls, options: Mapping[str, Any]) -> "Options":
        if not options.get("target_host"):
            raise ValueError("The 'target_host' option is required to run the Temporal worker.")
        return cls(
            target_host=options["target_host"],
            debug_mode=lazy_django_debug(),
            namespace=options.get("namespace", "default"),
            task_queue=options.get("task_queue", "django-tasks"),
            max_concurrent_workflow_tasks=options.get("max_concurrent_workflow_tasks"),
            max_concurrent_activities=options.get("max_concurrent_activities"),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class DjangoWorkflowRunParams:
    task_path: str
    args: tuple
    kwargs: dict


    @classmethod
    def from_task(cls, task: Task, args: tuple, kwargs: dict) -> "DjangoWorkflowRunParams":
        task_path = f"{task.func.__module__}.{task.func.__qualname__}"
        return DjangoWorkflowRunParams(
            task_path=task_path,
            args=args,
            kwargs=kwargs,
        )

    def get_task(self) -> Task:
        return import_string(self.task_path)

    @classmethod
    def from_dict(cls, input: dict) -> "DjangoWorkflowRunParams":
        return cls(
            task_path=input["task_path"],
            args=tuple(input["args"]),
            kwargs=input["kwargs"],
        )