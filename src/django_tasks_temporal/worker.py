import logging
from dataclasses import dataclass
from typing import Mapping, Any

from temporalio.client import Client
from temporalio.worker import Worker
from temporalio import workflow

from django_tasks_temporal.backends import Options
from django_tasks_temporal.client import get_client

from .workflows import RunDjangoTaskWorkflow
from .activities import run_django_task_activity


async def run_worker(options: Options):
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

    parser = argparse.ArgumentParser(description="Run a Temporal worker to process Django tasks.")
    parser.add_argument("--target_host", default="localhost:7233", help="The Temporal server host to connect to.")
    parser.add_argument("--namespace", default="default", help="The Temporal namespace to use (default: 'default').")
    parser.add_argument("--task_queue", default="django-tasks", help="The Temporal task queue to listen on (default: 'django-tasks').")
    parser.add_argument("--max_concurrent_workflow_tasks", type=int, help="Maximum number of concurrent workflow tasks.")
    parser.add_argument("--max_concurrent_activities", type=int, help="Maximum number of concurrent activities.")
    args = parser.parse_args()

    options = Options.from_options(vars(args))
    asyncio.run(run_worker(options))