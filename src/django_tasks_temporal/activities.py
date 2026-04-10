from datetime import datetime

from django.tasks import Task, TaskContext, TaskResult, TaskResultStatus
from temporalio import activity

from .types import DjangoWorkflowRunParams


@activity.defn
async def run_django_task_activity(param: DjangoWorkflowRunParams, workflow_id: str, workflow_start_time: datetime):
    task = param.get_task()
    if not isinstance(task, Task):
        raise RuntimeError("Expected a Task")
    if task.takes_context:
        activity_info = activity.info()
        context = TaskContext(
            task_result=TaskResult(
                task=param.get_task(),
                id=workflow_id,
                status=TaskResultStatus.RUNNING,
                enqueued_at=workflow_start_time,
                started_at=activity_info.started_time,
                finished_at=None,
                last_attempted_at=activity_info.started_time,
                args=param.args,
                kwargs=param.kwargs,
                  backend=task.backend,
                worker_ids=['temporal-worker'] * activity_info.attempt,  # This is a bit of a hack since Temporal doesn't provide worker IDs to activities
                errors=[],
            )
        )
        return await task.acall(context, *param.args, **param.kwargs)
    return await task.acall(*param.args, **param.kwargs)
