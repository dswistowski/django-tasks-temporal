from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, cast

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
    def from_options(cls, options: Mapping[str, Any]) -> Options:
        if not options.get("target_host"):
            raise ValueError(
                "The 'target_host' option is required to run the Temporal worker."
            )
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
    args: tuple[Any, ...]
    kwargs: dict[str, Any]

    @classmethod
    def from_task(
        cls,
        task: Task[..., Any],
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> DjangoWorkflowRunParams:
        task_path = f"{task.func.__module__}.{task.func.__qualname__}"
        return DjangoWorkflowRunParams(
            task_path=task_path,
            args=args,
            kwargs=kwargs,
        )

    def get_task(self) -> Task[..., Any]:
        task: Task[..., Any] = cast(Any, import_string(self.task_path))
        return task

    @classmethod
    def from_dict(cls, input: dict[str, Any]) -> DjangoWorkflowRunParams:
        return cls(
            task_path=cast(str, input["task_path"]),
            args=tuple(cast(list[Any], input["args"])),
            kwargs=cast(dict[str, Any], input["kwargs"]),
        )
