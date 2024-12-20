import pdoc
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    """
    This command uses pdoc to generate the html content for this
    documentation. Run

        python manage.py generate_pdocs

    from any Arches project and new content will be written into /docs.
    """

    def __init__(self, *args, **kwargs):
        self.help = self.__doc__

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):

        module_path = Path(__file__).parents[2]
        output = Path(Path(__file__).parents[3], "docs")
        r = pdoc.pdoc(
            "arches_extensions",
            output_directory=output,
        )
