import os
import uuid
import json
from arches.app.models.models import MapSource, MapLayer
from django.db import transaction
from django.core.management.base import BaseCommand, CommandError
from django.db.utils import IntegrityError


class Command(BaseCommand):
    """
    Manage Arches map layers with this command.
    """

    def __init__(self, *args, **kwargs):
        self.help = self.__doc__

    def add_arguments(self, parser):

        parser.add_argument(
            "operation",
            choices=["add", "remove", "list"]
        )

        parser.add_argument(
            "-s", "--source",
            help="Widget json file to be loaded",
        )

        parser.add_argument(
            "-n", "--name",
            help="The name of the Map Layer to remove"
        )

    def handle(self, *args, **options):

        if options["operation"] == "add":
            self.add_layer(
                options["layer_name"],
                options["mapbox_json_path"],
                options["layer_icon"],
                options["is_basemap"],
            )

        if options["operation"] == "remove":
            self.remove_layer(
                options["name"]
            )

        if options["operation"] == "list":
            self.list()


    def add_layer(self, layer_name=False, mapbox_json_path=False, layer_icon="fa fa-globe", is_basemap=False,
    ):
        """not yet implemented"""
        if layer_name is not False and mapbox_json_path is not False:
            with open(mapbox_json_path) as data_file:
                data = json.load(data_file)
                with transaction.atomic():
                    for layer in data["layers"]:
                        if "source" in layer:
                            layer["source"] = layer["source"] + "-" + layer_name
                    for source_name, source_dict in data["sources"].items():
                        map_source = MapSource.objects.get_or_create(name=source_name + "-" + layer_name, source=source_dict)
                    map_layer = MapLayer(
                        name=layer_name, layerdefinitions=data["layers"], isoverlay=(not is_basemap), icon=layer_icon
                    )
                    try:
                        map_layer.save()
                    except IntegrityError as e:
                        print("Cannot save layer: {0} already exists".format(layer_name))

    def remove_layer(self, layer_name):
        try:
            layer = MapLayer.objects.get(name=layer_name)
        except MapLayer.DoesNotExist:
            print(f'error: Map Layer "{layer_name}" does not exist.')
            return
        sources = set([i.get("source") for i in layer.layerdefinitions])
        with transaction.atomic():
            # list through and delete sources that aren't None
            for source in [i for i in sources if i]:
                print(f'removing Map Source "{source}"')
                try:
                    MapSource.objects.get(name=source).delete()
                except MapSource.DoesNotExist:
                    pass
            print(f'removing Map Layer "{layer_name}"')
            layer.delete()

    def list(self):
        """
        Lists all registered map layers and the sources they use.
        """

        layers = MapLayer.objects.all()
        print(f"-- {layers.count()} Map Layers --")
        
        for layer in layers:
            print(f"{layer.name}")
            sources = set([i.get("source") for i in layer.layerdefinitions])
            print(f"  source(s): {', '.join([i for i in sources if i is not None])}")
