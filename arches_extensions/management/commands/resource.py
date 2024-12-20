import os
import imp
import uuid
import json

from django.core.management.base import BaseCommand, CommandError
from django.db.utils import IntegrityError

from arches.app.models.models import ResourceInstance
from arches.app.models.graph import Graph

from arches_extensions.utils import get_graph

class Command(BaseCommand):
    """
    """

    def __init__(self, *args, **kwargs):
        self.help = self.__doc__

    def add_arguments(self, parser):

        parser.add_argument(
            "operation",
            choices=[
                "import",
                "export",
                "inspect",
            ]
        )

        parser.add_argument(
            "-s", "--source",
            action="store",
            help="Path to upload file.",
        )

        parser.add_argument(
            "-g", "--graph",
            action="store",
            help="Graph name"
        )

        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Overwrite existing extension that matches the input extension name.",
        )

    def handle(self, *args, **options):

        if options["operation"] == "import":
            self.register(options["extension_type"], options["source"], overwrite=options['overwrite'])

        if options["operation"] == "export":
            self.unregister(options["extension_type"], name=options["name"])

        if options["operation"] == "inspect":

            if options['graph']:
                graph = get_graph(options['graph'])
                if graph is None:
                    print("Invalid graph")
                    return
                graphs = [graph]
            else:
                graphs = Graph.objects.filter(isresource=True).exclude(name="Arches System Settings")
            self.inspect(graphs)

    def import_resources(self, source):
        pass

    def inspect(self, graphs=[]):

        for graph in graphs:
            print(graph.name)
            res = ResourceInstance.objects.filter(graph=graph)
            print(res.count())
