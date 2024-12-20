from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

import pdoc


class Command(BaseCommand):
    """
    This command uses pdoc to generate the html content for this
    documentation. It must be run from **within** an Arches project that uses a local 
    install of arches_extensions. New docs content will be written into arches_extensions/docs.
    """

    def __init__(self, *args, **kwargs):
        self.help = self.__doc__

    def handle(self, *args, **options):

        r = pdoc.pdoc(
            "arches_extensions",
            output_directory=Path(Path(__file__).parents[3], "docs"),
        )
