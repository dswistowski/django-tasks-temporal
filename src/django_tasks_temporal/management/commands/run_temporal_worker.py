import argparse
import asyncio

from django.core.management import BaseCommand
from django.utils.translation import gettext_lazy as _

from django_tasks_temporal.backends import TemporalTaskBackend
from django_tasks_temporal.worker import run_worker, WorkerOptions
from django.tasks import task_backends

class Command(BaseCommand):
    help = _("Run a worker to process temporal tasks")

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--backend",
            default="default",

            help=_("The task backend to use (default: 'default')"),
        )

    def handle(self, *args, **options):
        backend_name = options["backend"]
        backend = task_backends[backend_name]
        if not isinstance(backend, TemporalTaskBackend):
            self.stdout.write(
                self.style.ERROR(
                    f"Error: Backend '{backend_name}' is not a TemporalTaskBackend."
                )
            )
            exit(1)
        self.stdout.write(
            self.style.SUCCESS(f"Starting Temporal worker for backend '{backend}'...")
        )
        asyncio.run(run_worker(WorkerOptions.from_options(backend.options)))

