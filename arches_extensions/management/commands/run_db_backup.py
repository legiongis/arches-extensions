import os
from datetime import datetime
import subprocess
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from arches_extensions.utils import ArchesHelpTextFormatter

class Command(BaseCommand):
    """Run pg_dump to SQL file. Creates a local file and then uploads to S3.

Follows this backup pattern:

1. Rotated daily backups for the last 10 days, stored locally and also synced to S3 bucket
2. Backups on the 1st and 15th of each month forever, only uploaded to S3 bucket (not stored locally)

Local storage directory structure:

```
.db_backups/
    daily/
        <db name>__<YYYYMMDD>.sql <- repeated for the last 10 days
```

S3 bucket directory structure:

```
bucket_name/
    daily/ <- synced from local daily directory (see above)
    <YYYY>/ <- all 1st and 15th of the month backups for one year
        <db name>__<YYYY>0101.sql <- Jan 1st backup
        <db name>__<YYYY>0115.sql <- Jan 15th backup
        <db name>__<YYYY>0201.sql <- etc.
```

This command assumes you have the [AWS CLI tool](https://aws.amazon.com/cli/) installed and configured.

Args:
    
- `bucket-name`: Name of the S3 bucket the backups will be synced to.
- `--aws-profile`: Optionally pass a specific aws profile to be used for the `aws s3 cp ...` command
- `--skip-sync`: Don't sync the daily backups to S3 (useful during testing)
- `--skip-rotate`: "Don't rotate i.e. trim off dailies older than 10 days"
    """

    def __init__(self, *args, **kwargs):
        self.help = self.__doc__

    def add_arguments(self, parser):
        parser.formatter_class = ArchesHelpTextFormatter
        parser.add_argument(
            "bucket-name",
            help="Name of the S3 bucket the backups will be synced to.",
        )
        parser.add_argument(
            "--aws-profile",
            help="Optionally pass a specific aws profile to be used for the ``aws s3 cp`` command"
        )
        parser.add_argument(
            "--skip-sync",
            action="store_true",
            help="Don't sync the daily backups to S3 (useful during testing)"
        )
        parser.add_argument(
            "--skip-rotate",
            action="store_true",
            help="Don't rotate i.e. trim off dailies older than 10 days"
        )

    def handle(self, *args, **options):

        def apply_profile(cmd: list):
            if options['aws_profile']:
                cmd += ["--profile", options['aws_profile']]
            return cmd

        bucket = options['bucket-name']
        now = datetime.now()

        backup_dir = Path(Path(settings.APP_ROOT).parent, ".db_backups", "daily")
        backup_dir.mkdir(exist_ok=True, parents=True)

        db_name = settings.DATABASES['default']['NAME']
        db_user = settings.DATABASES['default']['USER']
        db_host = settings.DATABASES['default']['HOST']
        db_pass = settings.DATABASES['default']['PASSWORD']
        db_port = settings.DATABASES['default']['PORT']

        fname = now.strftime(f"{db_name}__%Y%m%d.sql")
        fpath = Path(backup_dir, fname)

        cmd = [
            "pg_dump",
            "-U", db_user,
            "-h", db_host,
            "-p", str(db_port),
            "-f", str(fpath.resolve()),
            db_name,
        ]

        use_env = os.environ.copy()
        use_env['PGPASSWORD'] = db_pass
        p = subprocess.Popen(cmd, env=use_env)
        exit_code = p.wait()

        day, year = now.day, now.year

        ## on the 1st and 15th of the month upload the dump to yearly archive
        if day in [1, 15]:

            cmd2 = [
                "aws", "s3", "cp", fpath, f"s3://{bucket}/{year}/"
            ]
            cmd2 = apply_profile(cmd2)
            subprocess.run(cmd2)

        if not options["skip_rotate"]:
            ## cleanup any local files that are over 10 days old.
            ## sort all of the existing local daily files
            local_dailies = sorted(list(backup_dir.glob("*")))
            limit = 10
            ## slice off any local dailies beyond the limit
            for path in local_dailies[:-limit]:
                os.remove(path)

        if not options["skip_sync"]:
            cmd3 = [
                "aws", "s3", "sync", str(backup_dir.resolve()), f"s3://{bucket}/daily/", "--delete"
            ]
            cmd3 = apply_profile(cmd3)
            subprocess.run(cmd3)
