import os
import imp
import uuid
import json
from arches.app.models import models
from django.core.management.base import BaseCommand, CommandError
from django.db.utils import IntegrityError


class Command(BaseCommand):
    """
    Use this command to manage extensions within Arches. Usage:

    Manage extensions, like custom datatypes, widgets, functions, etc. 

    ```
    python manage.py extension [operation] [extension_type] [-s/--source] [-n/--name] [--overwrite]
    ```

    Operations are

    - `register`
    - `unregister`
    - `list`

    Extension types are

    - `card-component`
    - `datatype`
    - `function`
    - `plugin`
    - `report`
    - `search-filter`
    - `widget`

    > For Workflows use `plugin`.

    Other arguments:

    - `-s/--source` Use with `register` to provide a JSON or .py file when registering an extension. 
    - `-n/--name` Use with `unregister` for the name of the extension to remove.

    - `--overwrite` Use with `register` to overwrite an existing extension with the provided source definition.
    """

    def __init__(self, *args, **kwargs):
        self.help = self.__doc__

    def add_arguments(self, parser):

        parser.add_argument(
            "operation",
            choices=[
                "list",
                "register",
                "unregister",
            ]
        )

        parser.add_argument(
            "extension_type",
            choices=[
                "card-component",
                "datatype",
                "function",
                "plugins",
                "report",
                "search-filter",
                "widget",
            ]
        )

        parser.add_argument(
            "-s", "--source",
            action="store",
            help="Path to the source file for the extension to register. "\
                "In many cases this will be a .json file, but with functions, search-filters, etc. "\
                ", it will be a .py file.",
        )

        parser.add_argument(
            "-n", "--name",
            action="store",
            help="The name of the extension to unregister."
        )

        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Overwrite existing extension that matches the input extension name.",
        )

    def handle(self, *args, **options):

        if options["operation"] == "register":
            self.register(options["extension_type"], options["source"], overwrite=options['overwrite'])

        if options["operation"] == "unregister":
            self.unregister(options["extension_type"], name=options["name"])

        if options["operation"] == "list":
            self.list(options["extension_type"])

    def get_source_details(self, source_path):

        ## load details from a python module (functions, datatypes)
        if source_path.endswith(".py"):

            import imp
            try:
                source = imp.load_source("", source_path)
            ## more precise exception handling would be good here
            except Exception as e:
                raise(e)
            details = source.details
            return details

        ## load details form a json file (widgets, card_components, etc.)
        elif source_path.endswith(".json"):

            with open(source_path) as f:
                details = json.load(f)
            return details

        else:
            print("invalid source path")
            exit()


    def get_model(self, extension_type):

        if extension_type == "widget":
            return models.Widget
        elif extension_type == "datatype":
            return models.DDataType
        elif extension_type == "search":
            return models.SearchComponent
        else:
            print("this extension type not (yet) supported.")

    def register(self, extension_type, source, overwrite=False):
        """
        Registers a new extension in the database based on the provided source

        """

        details = self.get_source_details(source)
        model = self.get_model(extension_type)

        if extension_type == "widget":

            try:
                uuid.UUID(details["widgetid"])
            except:
                details["widgetid"] = str(uuid.uuid4())
            print("Registering widget with widgetid: {}".format(details["widgetid"]))

            instance = model(
                widgetid=details["widgetid"],
                name=details["name"],
                datatype=details["datatype"],
                helptext=details["helptext"],
                defaultconfig=details["defaultconfig"],
                component=details["component"],
            )

            instance.save()

        elif extension_type == "datatype":

            print(f"Registering datatype {details['datatype']}")
            dt = model(
                datatype=details["datatype"],
                iconclass=details["iconclass"],
                modulename=os.path.basename(source),
                classname=details["classname"],
                defaultwidget=details["defaultwidget"],
                defaultconfig=details["defaultconfig"],
                configcomponent=details["configcomponent"],
                configname=details["configname"],
                isgeometric=details["isgeometric"],
                issearchable=details.get("issearchable", False),
            )

            if len(model.objects.filter(datatype=dt.datatype)) == 0:
                dt.save()
            else:
                print("{0} already exists".format(dt.datatype))

        elif extension_type == "search":

            try:
                uuid.UUID(details["searchcomponentid"])
            except:
                details["searchcomponentid"] = str(uuid.uuid4())
            print("Registering the search component, %s, with componentid: %s" % (details["name"], details["searchcomponentid"]))

            instance = model(
                searchcomponentid=details["searchcomponentid"],
                name=details["name"],
                icon=details["icon"],
                modulename=details["modulename"],
                classname=details["classname"],
                type=details["type"],
                componentpath=details["componentpath"],
                componentname=details["componentname"],
                sortorder=details["sortorder"],
                enabled=details["enabled"],
            )

            instance.save()

        else:
            print("this extension type not (yet) supported.")

    def update(self, extension_type, source):
        """
        Updates an existing widget in the arches db

        """
        details = self.get_source_details(source)
        model = self.get_model(extension_type)

        if extension_type == "widget":
            instance = model.objects.get(name=details["name"])
            instance.datatype = details["datatype"]
            instance.helptext = details["helptext"]
            instance.defaultconfig = details["defaultconfig"]
            instance.component = details["component"]
            instance.save()
        
        if extension_type == "search":
            instance = model.objects.get(name=details["name"])
            instance.icon = details["icon"]
            instance.classname = details["classname"]
            instance.type = details["type"]
            instance.componentpath = details["componentpath"]
            instance.componentname = details["componentname"]
            instance.sortorder = details["sortorder"]
            instance.enabled = details["enabled"]
            instance.save()

        else:
            print("this extension type not (yet) supported.")

    def unregister(self, extension_type, name):
        """
        Removes an extension of the specified type from the database

        """
        print(f"unregistering {extension_type}: \"{name}\"")

        model = self.get_model(extension_type)
        try:
            if extension_type == "datatype":
                instance = model.objects.get(datatype=name)
            else:
                instance = model.objects.get(name=name)
            instance.delete()
        except Exception as e:
            print(e)

    def list(self, extension_type):
        """
        Lists registered extensions of a specified type

        """

        model = self.get_model(extension_type)
        try:
            instances = model.objects.all()
            for instance in instances:
                if extension_type == "datatype":
                    print(instance.datatype)
                else:
                    print(instance.name)
        except Exception as e:
            print(e)
