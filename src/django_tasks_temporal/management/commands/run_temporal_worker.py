import argparse
import asyncio
import os
import subprocess
import sys
from typing import Any

from django.core.management import BaseCommand
from django.tasks import task_backends
from django.utils.translation import gettext as _

from django_tasks_temporal.backends import TemporalTaskBackend
from django_tasks_temporal.types import Options
from django_tasks_temporal.worker import run_worker


def _spawn_worker_subprocess(backend: str) -> int:
    cmd = [sys.executable, "-m", "django_tasks_temporal.worker", "--backend", backend]

    env = os.environ.copy()
    result = subprocess.run(cmd, env=env, check=False)
    return result.returncode


def _should_fallback(exc: BaseException) -> bool:
    message = str(exc)
    cause = exc.__cause__
    cause_message = str(cause) if cause else ""

    combined = f"{message}\n{cause_message}"

    return (
        "Failed validating workflow" in combined
        or "beartype.claw" in combined
        or "key_value.aio" in combined
        or "_clawstate" in combined
        or "partially initialized module 'beartype.claw._clawstate'" in combined
    )


class Command(BaseCommand):
    help = _("Run a worker to process temporal tasks")

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--backend",
            default="default",
            help=_("The task backend to use (default: 'default')"),
        )
        parser.add_argument(
            "--no-fallback",
            action="store_true",
            help=_("Do not fall back to spawning a clean worker subprocess."),
        )

    def handle(self, *args: Any, **options: Any) -> None:
        backend_name = str(options["backend"])
        backend = task_backends[backend_name]

        if not isinstance(backend, TemporalTaskBackend):
            self.stderr.write(
                self.style.ERROR(
                    f"Error: Backend '{backend_name}' is not a TemporalTaskBackend."
                )
            )
            raise SystemExit(1)

        worker_options = Options.from_options(backend.options)

        self.stdout.write(
            self.style.SUCCESS(
                f"Starting Temporal worker for backend '{backend_name}'..."
            )
        )

        try:
            asyncio.run(run_worker(worker_options))
            return
        except BaseException as exc:
            if options["no_fallback"] or not _should_fallback(exc):
                raise

            self.stderr.write(
                self.style.WARNING(
                    "Worker failed to start in-process due to an import/sandbox "
                    "conflict. Retrying in a clean Python subprocess..."
                )
            )

            exit_code = _spawn_worker_subprocess(backend_name)
            raise SystemExit(exit_code) from None
