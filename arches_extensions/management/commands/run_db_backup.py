import os
import imp
import uuid
import json
from datetime import datetime
import subprocess
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.utils import IntegrityError

class Command(BaseCommand):
    """
    """

    def __init__(self, *args, **kwargs):
        self.help = self.__doc__

    def add_arguments(self, parser):

        parser.add_argument(
            "bucket-name",
        )
        parser.add_argument(
            "--aws-profile",
            help="Optionally pass a specific aws profile to be used for the upload command"
        )
        parser.add_argument(
            "--skip-sync",
            action="store_true",
            help="Don't sync the daily backups to S3 (useful during testing)"
        )
        parser.add_argument(
            "--skip-rotate",
            action="store_true",
            help="Don't rotate and trim off dailies older than 10 days"
        )

    def handle(self, *args, **options):

        def apply_profile(cmd: list):
            if options['aws_profile']:
                cmd += ["--profile", options['aws_profile']]
            return cmd

        bucket = options['bucket-name']
        now = datetime.now()

        backup_dir = Path(Path(settings.APP_ROOT).parent, ".db_backups", "daily")
        backup_dir.mkdir(exist_ok=True)

        db_name = settings.DATABASES['default']['NAME']
        db_user = settings.DATABASES['default']['USER']
        db_host = settings.DATABASES['default']['HOST']
        db_pass = settings.DATABASES['default']['PASSWORD']
        db_port = settings.DATABASES['default']['PORT']

        fname = now.strftime(f"%Y%m%d__{db_name}.sql")
        fpath = Path(backup_dir, fname)

        cmd = [
            "pg_dump",
            "-U", db_user,
            "-h", db_host,
            "-p", db_port,
            "-f", str(fpath.resolve()),
            db_name,
        ]

        use_env = os.environ.copy()
        use_env['PGPASSWORD'] = db_pass
        print(' '.join(cmd))
        subprocess.Popen(cmd, env=use_env)

        day, year = now.day, now.year

        if day in [1, 15]:

            cmd2 = [
                "aws", "s3", "cp", fpath, f"s3://{bucket}/{year}/"
            ]

            cmd2 = apply_profile(cmd2)

            subprocess.Popen(cmd2)

        if not options["skip_rotate"]:
            ## cleanup any local files that are over 10 days old.
            ## sort all of the existing local daily files
            local_dailies = sorted(list(backup_dir.glob("*.sql")))
            limit = 10
            ## slice off any local dailies beyond the limit
            for path in local_dailies[:-limit]:
                os.remove(path)

        if not options["skip_sync"]:
            cmd3 = [
                "aws", "s3", "sync", str(backup_dir.resolve()), f"s3://{bucket}/daily/"
            ]
            cmd3 = apply_profile(cmd3)
            subprocess.Popen(cmd3)