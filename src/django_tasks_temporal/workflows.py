from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING
from temporalio import workflow

from .types import DjangoWorkflowRunParams

from .activities import run_django_task_activity

if TYPE_CHECKING:
    pass


@workflow.defn(sandboxed=False)
class RunDjangoTaskWorkflow:
    @workflow.run
    async def run(self, params: DjangoWorkflowRunParams):
        workflow_info = workflow.info()

        return await workflow.execute_activity(
            run_django_task_activity,
            args=(params, workflow_info.workflow_id, workflow_info.start_time),
            start_to_close_timeout=timedelta(minutes=5),
        )