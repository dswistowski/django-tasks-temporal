from io import StringIO

import pytest
from django.core.management import call_command

from django_tasks_temporal.backends import Options, TemporalTaskBackend
from django_tasks_temporal.management.commands import run_temporal_worker


def test_run_temporal_worker_starts_worker(
    backend: TemporalTaskBackend, monkeypatch: pytest.MonkeyPatch
):
    captured = {}

    async def fake_run_worker(options: Options) -> None:
        captured["options"] = options

    monkeypatch.setattr(run_temporal_worker, "task_backends", {"default": backend})
    monkeypatch.setattr(run_temporal_worker, "run_worker", fake_run_worker)

    stdout = StringIO()

    call_command("run_temporal_worker", stdout=stdout)

    assert captured["options"] == Options.from_options(backend.options)
    assert "Starting Temporal worker for backend 'default'" in stdout.getvalue()


def test_run_temporal_worker_rejects_non_temporal_backend(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(run_temporal_worker, "task_backends", {"default": object()})

    stderr = StringIO()

    with pytest.raises(SystemExit, match="1"):
        call_command("run_temporal_worker", stderr=stderr)

    assert "is not a TemporalTaskBackend" in stderr.getvalue()


def test_run_temporal_worker_falls_back_to_subprocess(
    backend: TemporalTaskBackend, monkeypatch: pytest.MonkeyPatch
):
    captured = {}

    async def failing_run_worker(options: Options) -> None:
        raise RuntimeError("Failed validating workflow")

    def fake_spawn_worker_subprocess(options: Options) -> int:
        captured["options"] = options
        return 7

    monkeypatch.setattr(run_temporal_worker, "task_backends", {"default": backend})
    monkeypatch.setattr(run_temporal_worker, "run_worker", failing_run_worker)
    monkeypatch.setattr(
        run_temporal_worker,
        "_spawn_worker_subprocess",
        fake_spawn_worker_subprocess,
    )

    stderr = StringIO()

    with pytest.raises(SystemExit, match="7"):
        call_command("run_temporal_worker", stderr=stderr)

    assert captured["options"] == Options.from_options(backend.options)
    assert "Retrying in a clean Python subprocess" in stderr.getvalue()


def test_run_temporal_worker_no_fallback_reraises_startup_error(
    backend: TemporalTaskBackend, monkeypatch: pytest.MonkeyPatch
):
    async def failing_run_worker(options: Options) -> None:
        raise RuntimeError("Failed validating workflow")

    monkeypatch.setattr(run_temporal_worker, "task_backends", {"default": backend})
    monkeypatch.setattr(run_temporal_worker, "run_worker", failing_run_worker)

    with pytest.raises(RuntimeError, match="Failed validating workflow"):
        call_command("run_temporal_worker", no_fallback=True)
