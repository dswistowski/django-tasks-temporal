import logging
from collections.abc import Mapping
from typing import Any, cast

from django.conf import settings
from temporalio.worker import Worker

from django_tasks_temporal.client import get_client
from django_tasks_temporal.types import Options

from .activities import run_django_task_activity
from .workflows import RunDjangoTaskWorkflow


async def run_worker(options: Options) -> None:
    worker = Worker(
        await get_client(options),
        task_queue=options.task_queue,
        workflows=[RunDjangoTaskWorkflow],
        activities=[run_django_task_activity],
        max_concurrent_workflow_tasks=options.max_concurrent_workflow_tasks,
        max_concurrent_activities=options.max_concurrent_activities,
        debug_mode=options.debug_mode,
    )
    await worker.run()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import argparse
    import asyncio

    parser = argparse.ArgumentParser(
        description="Run a Temporal worker to process Django tasks."
    )
    parser.add_argument(
        "--backend",
        default="default",
        choices=list(settings.TASKS.keys()),
        help="The temporal backend to use",
    )
    args = parser.parse_args()

    raw_options = cast(
        Mapping[str, Any], settings.TASKS[args.backend].get("OPTIONS") or {}
    )
    options = Options.from_options(raw_options)
    asyncio.run(run_worker(options))
