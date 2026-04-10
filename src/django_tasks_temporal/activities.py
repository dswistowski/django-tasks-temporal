from temporalio import activity


@activity.defn
async def run_django_task_activity(task):
    """
    Activity to run a Django task.

    This is a placeholder implementation. In a real implementation, this would
    execute the task and return the result.
    """
    raise NotImplemented("Running Django tasks is not implemented in TemporalTaskBackend.")