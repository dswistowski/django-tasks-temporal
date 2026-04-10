from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractContextManager
from datetime import UTC, datetime
from typing import Any, assert_never, cast, override
from uuid import uuid4

from asgiref.sync import AsyncSingleThreadContext, async_to_sync
from django.tasks.backends.base import BaseTaskBackend
from django.tasks.base import Task, TaskError, TaskResult, TaskResultStatus
from temporalio.client import Client, WorkflowExecutionStatus
from temporalio.common import Priority

from .client import get_client
from .types import DjangoWorkflowRunParams, Options
from .workflows import RunDjangoTaskWorkflow


def _async_single_thread_context() -> AbstractContextManager[None]:
    context_factory = cast(
        Callable[[], AbstractContextManager[None]], AsyncSingleThreadContext
    )
    return context_factory()


class TemporalTaskBackend(BaseTaskBackend):
    supports_defer = True
    supports_async_task = True
    supports_get_result = True
    supports_priority = True

    def get_options(self) -> Options:
        return Options.from_options(self.options)

    async def get_client(self) -> Client:
        return await get_client(self.get_options())

    @override
    def get_result(self, result_id: str) -> TaskResult[Any, Any]:
        with _async_single_thread_context():
            return async_to_sync(self.aget_result)(result_id)

    async def aget_result(self, result_id: str) -> TaskResult[Any, Any]:
        client = await self.get_client()
        handle = client.get_workflow_handle(result_id)
        description = await handle.describe()

        history = await handle.fetch_history()
        start_event = history.events[0]
        if not start_event.HasField("workflow_execution_started_event_attributes"):
            raise RuntimeError("First event is not workflow start")
        inputs = await handle._data_converter.decode_wrapper(
            start_event.workflow_execution_started_event_attributes.input
        )
        if len(inputs) > 1:
            raise RuntimeError("Expected exactly one input to workflow")
        input_parameters = DjangoWorkflowRunParams.from_dict(inputs[0])
        history = await handle.fetch_history()
        worker_ids = [
            event.workflow_task_started_event_attributes.identity
            for event in history.events
            if event.HasField("workflow_task_started_event_attributes")
        ]

        activity_started_event = next(
            (
                event
                for event in history.events
                if event.HasField("activity_task_started_event_attributes")
            ),
            None,
        )
        errors: list[TaskError] = []
        if activity_started_event is not None:
            activity_started_event_attributes = (
                activity_started_event.activity_task_started_event_attributes
            )
            if activity_started_event_attributes.HasField("last_failure"):
                last_error = activity_started_event_attributes.last_failure
                errors.append(
                    TaskError(
                        exception_class_path=last_error.application_failure_info.type,
                        traceback=last_error.stack_trace,
                    )
                )

        activity_completed_event = next(
            (
                event
                for event in history.events
                if event.HasField("activity_task_completed_event_attributes")
            ),
            None,
        )
        if activity_completed_event is not None:
            activity_completed_event_attributes = (
                activity_completed_event.activity_task_completed_event_attributes
            )
            worker_ids.append(activity_completed_event_attributes.identity)

        activity_task_failed_event = next(
            (
                event
                for event in history.events
                if event.HasField("activity_task_failed_event_attributes")
            ),
            None,
        )
        if activity_task_failed_event is not None:
            activity_task_failed_event_attributes = (
                activity_task_failed_event.activity_task_failed_event_attributes
            )
            worker_ids.append(activity_task_failed_event_attributes.identity)
            last_failure = activity_task_failed_event_attributes.failure
            errors.append(
                TaskError(
                    exception_class_path=last_failure.application_failure_info.type,
                    traceback=last_failure.stack_trace,
                )
            )

        task = input_parameters.get_task()
        task_result: TaskResult[Any, Any] = TaskResult(
            task=task,
            id=result_id,
            status=TaskResultStatus.RUNNING,
            enqueued_at=description.start_time,
            started_at=description.start_time,
            finished_at=description.close_time,
            last_attempted_at=description.start_time,
            args=list(input_parameters.args),
            kwargs=input_parameters.kwargs,
            backend=task.backend,
            worker_ids=worker_ids,
            errors=errors,
        )
        match description.status:
            case (
                WorkflowExecutionStatus.RUNNING
                | WorkflowExecutionStatus.CONTINUED_AS_NEW
            ):
                pass
            case WorkflowExecutionStatus.COMPLETED:
                result = await handle.result()
                object.__setattr__(task_result, "status", TaskResultStatus.SUCCESSFUL)
                object.__setattr__(task_result, "_return_value", result)
            case (
                WorkflowExecutionStatus.FAILED
                | WorkflowExecutionStatus.CANCELED
                | WorkflowExecutionStatus.TERMINATED
                | WorkflowExecutionStatus.TIMED_OUT
                | None
            ):
                object.__setattr__(task_result, "status", TaskResultStatus.FAILED)
            case _:
                assert_never(description.status)
        return task_result

    @override
    def enqueue(
        self,
        task: Task[Any, Any],
        args: list[Any],
        kwargs: dict[str, Any],
    ) -> TaskResult[Any, Any]:
        with _async_single_thread_context():
            return async_to_sync(self.aenqueue)(task, args, kwargs)

    async def aenqueue(
        self,
        task: Task[Any, Any],
        args: list[Any],
        kwargs: dict[str, Any],
    ) -> TaskResult[Any, Any]:
        self.validate_task(task)
        client = await self.get_client()
        task_id = f"{task.module_path}-{uuid4()}"

        if task.run_after:
            now = datetime.now(tz=UTC)
            delay = task.run_after - now
        else:
            delay = None

        # django priority -100 (highest) to 100 (lowest), temporal priority 1 (highest) to 201 (lowest)
        priority = (
            Priority(priority_key=task.priority + 101)
            if task.priority is not None
            else Priority.default
        )

        await client.start_workflow(
            RunDjangoTaskWorkflow.run,
            DjangoWorkflowRunParams.from_task(task, args=tuple(args), kwargs=kwargs),
            id=task_id,
            task_queue=self.get_options().task_queue,
            start_delay=delay,
            priority=priority,
        )
        return TaskResult(
            task=task,
            id=task_id,
            status=TaskResultStatus.READY,
            args=args,
            kwargs=kwargs,
            enqueued_at=datetime.now(tz=UTC),
            started_at=None,
            finished_at=None,
            last_attempted_at=None,
            backend=task.backend,
            worker_ids=[],
            errors=[],
        )
