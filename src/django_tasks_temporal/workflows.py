from datetime import timedelta

from temporalio import workflow
from .activities import run_django_task_activity

@workflow.defn
class RunDjangoTaskWorkflow:
    @workflow.run
    async def run(self, task):
        return await workflow.execute_activity(
            run_django_task_activity,
            task,
            start_to_close_timeout=timedelta(minutes=5),
        )