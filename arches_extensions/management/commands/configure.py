import sys
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    """
    Configure service files used for Arches.

    Usage:

        python manage.py configure [operation]

    Operations:

        - `celery`

    """

    def __init__(self, *args, **kwargs):
        self.help = self.__doc__

    def add_arguments(self, parser):

        parser.add_argument(
            "operation",
            choices=["celery"]
        )
        parser.add_argument(
            "-a", "--app",
            help="Optional path for output. Defaults to .services/ in root directory."
        )
        parser.add_argument(
            "-d", "--destination",
            default=".services",
            help="Optional path for output. Defaults to .services/ in root directory."
        )
        parser.add_argument(
            "--log-dir",
            default=".logs",
            help="Path to where logs and pid files will go. Defaults to .logs in root directory."
        )
        parser.add_argument(
            "--log-level",
            default="DEBUG",
            choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL', 'FATAL'],
            help="Set log level for celery. Default is DEBUG."
        )
        parser.add_argument(
            "--prefix",
            help="Optional prefix for the names of the services to be written."
        )
        parser.add_argument(
            "--require-rabbitmq",
            action="store_true",
            default=False,
            help="If true, Celery services will require rabbitmq.service",
        )

    def handle(self, *args, **options):

        self.dest = Path(options["destination"])
        self.dest.mkdir(exist_ok=True)

        self.log_dir = Path(options["log_dir"]).resolve()
        self.log_dir.mkdir(exist_ok=True)

        python_env = Path(sys.executable).parent.parent
        self.celery_bin = Path(python_env, "bin", "celery")

        self.working_directory = Path(".").resolve()

        if options["operation"] == "celery":
            app = options["app"]
            if not app:
                print("-a/--app is require for celery configuration. cancelling.")
                exit()
            self.write_celery_services(
                options["app"],
                prefix=options["prefix"],
                log_level=options["log_level"],
                require_rabbitmq=options["require_rabbitmq"],
            )

    def write_celery_services(self, app_name, prefix=None, log_level="DEBUG", require_rabbitmq=False):

        if require_rabbitmq:
            requirement_block = "After=rabbitmq-server.service\nRequires=rabbitmq-server.service"
        else:
            "After=network.target"

        prefix_ = "" if not prefix else f"{prefix}_"
        main_fname = f"{prefix_}celery.service"
        with open(Path(self.dest, main_fname), "w") as o:
            o.write(f"""[Unit]
Description=Celery Service{f" ({prefix})" if prefix else ""}
{requirement_block}

[Service]
Type=simple
WorkingDirectory={self.working_directory}
ExecStart=/bin/sh -c '{self.celery_bin} \\
    -A {app_name} worker -n worker1@%h \\
    -B \\
    -s celerybeat-schedule \\
    --pidfile={self.log_dir}/{prefix_}celery.pid \\
    --logfile={self.log_dir}/{prefix_}celery.log \\
    --loglevel={log_level}'
ExecStop=/bin/sh -c '{self.celery_bin} worker stopwait \\
    --pidfile={self.log_dir}/{prefix_}celery.pid \\
    --logfile={self.log_dir}/{prefix_}celery.log \\
    --loglevel={log_level}'
Restart=always
RestartSec=1

[Install]
WantedBy=multi-user.target
""")

        beat_fname = f"{prefix_}celerybeat.service"
        with open(Path(self.dest, beat_fname), "w") as o:
            o.write(f"""[Unit]
Description=Celery Beat Service{f" ({prefix})" if prefix else ""}
After=network.target

[Service]
Type=simple
WorkingDirectory={self.working_directory}
ExecStart=/bin/sh -c '{self.celery_bin} \\
    -A {app_name} beat  \\
    --pidfile={self.log_dir}/{prefix_}celerybeat.pid \\
    --logfile={self.log_dir}/{prefix_}celerybeat.log \\
    --loglevel={log_level}'
Restart=always
RestartSec=1

[Install]
WantedBy=multi-user.target
""")
