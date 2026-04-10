import logging
from dataclasses import dataclass
from typing import Mapping, Any

from temporalio.client import Client
from temporalio.worker import Worker
from temporalio import workflow
with workflow.unsafe.imports_passed_through():
    from .workflows import RunDjangoTaskWorkflow
    from .activities import run_django_task_activity

def lazy_django_debug() -> bool:
    from django.conf import settings
    return settings.DEBUG

@dataclass(frozen=True)
class WorkerOptions:
    target_host: str
    debug_mode: bool = False
    namespace: str = "default"
    task_queue: str = "django-tasks"
    max_concurrent_workflow_tasks: int | None = None
    max_concurrent_activities: int | None = None

    @classmethod
    def from_options(cls, options: Mapping[str, Any]) -> "WorkerOptions":

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

async def run_worker(options: WorkerOptions):
    client = await Client.connect(options.target_host, namespace=options.namespace)
    worker = Worker(
        client,
        task_queue=options.task_queue,
        workflows=[RunDjangoTaskWorkflow],
        activities=[run_django_task_activity],
        # max_concurrent_workflow_tasks=options.max_concurrent_workflow_tasks,
        # max_concurrent_activities=options.max_concurrent_activities,
        # debug_mode=options.debug_mode,
    )
    await worker.run()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    import argparse
    import asyncio

    parser = argparse.ArgumentParser(description="Run a Temporal worker to process Django tasks.")
    parser.add_argument("--target_host", default="localhost:7233", help="The Temporal server host to connect to.")
    parser.add_argument("--namespace", default="default", help="The Temporal namespace to use (default: 'default').")
    parser.add_argument("--task_queue", default="django-tasks", help="The Temporal task queue to listen on (default: 'django-tasks').")
    parser.add_argument("--max_concurrent_workflow_tasks", type=int, help="Maximum number of concurrent workflow tasks.")
    parser.add_argument("--max_concurrent_activities", type=int, help="Maximum number of concurrent activities.")
    args = parser.parse_args()

    options = WorkerOptions.from_options(vars(args))
    asyncio.run(run_worker(options))