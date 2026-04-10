import logging

from django.conf import settings
from temporalio.worker import Worker

from django_tasks_temporal.backends import Options
from django_tasks_temporal.client import get_client

from .activities import run_django_task_activity
from .workflows import RunDjangoTaskWorkflow


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
    parser.add_argument("--backend", default="default", choices=list(settings.TASKS.keys()), help="The temporal backend to use")
    args = parser.parse_args()

    options = Options.from_options(settings.TASKS[args.backend].get("OPTIONS"))
    asyncio.run(run_worker(options))
