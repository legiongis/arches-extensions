import uuid
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from arches.app.models.resource import Resource
from arches.app.models.models import FunctionXGraph, Value, TileModel, Relation

from arches_extensions.utils import ArchesHelpTextFormatter, ArchesCLIStyles

s = ArchesCLIStyles()

class Command(BaseCommand):
    """
    Commands for managing the loading and running of packages in Arches

    """

    def add_arguments(self, parser):

        parser.formatter_class = ArchesHelpTextFormatter
        parser.add_argument(
            '--graph',
            help='Name of Resource Model whose display descriptor values you want to reorder.'
        )
        
        parser.add_argument(
            '--resourceinstanceid',
            help='Optionally specify a single resource instance id to process.'
        )

        parser.add_argument(
            '--name',
            help='The label or UUID of the name type that should be pushed to the top.'
        )

        parser.add_argument(
            '--description',
            help='The label or UUID of the description type that should be pushed to the top.'
        )

        parser.add_argument(
            '--map_popup',
            help='The label or UUID of the map_popup description type that should be pushed to the top.'
        )

    def handle(self, *args, **options):

        if options["graph"]:
            resources = Resource.objects.filter(graph_id=descriptor_function.graph_id)
        elif options["resourceinstanceid"]:
            resources = Resource.objects.filter(pk=options["resourceinstanceid"])
            if not resources.exists():
                print(f"Invalid resourceinstanceid: {options['resourceinstanceid']}")
                exit()
        else:
            print("--graph or --resourceinstanceid must be provided.")
            exit()

        graph = resources[0].graph
        nametype_value = self.get_value_from_input(options['name'])
        desctype_value = self.get_value_from_input(options['description'])
        popuptype_value = self.get_value_from_input(options['map_popup'])

        descriptor_function = FunctionXGraph.objects.get(
            function_id="60000000-0000-0000-0000-000000000001",
            graph=graph,
        )

        totalct = resources.count()
        print(f"resources to process: {totalct}")

        for n, resource in enumerate(resources):
            
            self.process_resource(resource, descriptor_function.config,
                nametype=nametype_value,
                desctype=desctype_value,
                popuptype=popuptype_value
            )
            
            if (n+1) % 100 == 0:
                print(n+1),
            if n+1 == totalct:
                print(n+1)

        print("re-indexing resource instances")
        if options["graph"]:
            call_command("es", "index_resources_by_type", resource_types=[graph.graphid])
        elif options["resourceinstanceid"]:
            resources[0].index()

    def process_resource(self, resource, config, nametype=None, desctype=None, popuptype=None):

        resid = resource.resourceinstanceid
        if nametype is not None:
            self.reorder_tiles(resid, config['name']['nodegroup_id'], nametype)
        if desctype is not None:
            self.reorder_tiles(resid, config['description']['nodegroup_id'], desctype)
        if popuptype is not None:
            self.reorder_tiles(resid, config['map_popup']['nodegroup_id'], popuptype)

        resource.save(index=False)

    def reorder_tiles(self, resourceid, nodegroup, typevalue):
          
        tiles = TileModel.objects.filter(nodegroup_id=nodegroup, resourceinstance_id=resourceid).order_by("sortorder")
        
        print("before")
        for t in tiles:
            print(t.sortorder)
        primarytileuuid = None
        for t in tiles:
            print(str(typevalue.valueid))
            print(t.data.values())
            if str(typevalue.valueid) in t.data.values():
                print("match")
                t.sortorder = 0
                t.save()
                primarytileuuid = t.tileid
        
        print(primarytileuuid)
        # this means that the primary tile has been found and handled.
        # all other tiles must be re-saved with ascending sortorder
        if primarytileuuid is not None:
            for n, t in enumerate(tiles.exclude(tileid=primarytileuuid).order_by("sortorder")):
                t.sortorder = n+1
                t.save()
        
        print("after")
        for t in TileModel.objects.filter(nodegroup_id=nodegroup, resourceinstance_id=resourceid).order_by("sortorder"):
            print(t.sortorder)

    def get_value_from_input(self, input):
        
        if input is None:
            return None
        
        try:
            uuid.UUID(input)
            value = Value.objects.get(valueid=input)
            return value
        except ValueError:
            pass

        values = Value.objects.filter(value=input)
        if values.count() == 0:
            print(f"input value '{input}' not found")
            exit()
        elif values.count() > 1:
            print("multiple labels found. please choose one of the following:")
            choice_dict = {}
            for n, val in enumerate(values):
                parent_concept = Relation.objects.get(relationtype_id="member", conceptto=val.concept_id)
                parent_label = Value.objects.filter(concept_id=parent_concept.conceptfrom.conceptid)[0]
                print(f"{n+1} - {val.valueid} - {parent_label.value} --> {val.value}")
                choice_dict[str(n+1)] = val
            while True:
                choice = input("choose by entering one of the numbers above: ")
                if choice in choice_dict:
                    return choice_dict[choice]
                else:
                    print("invalid choice. to quit, use ctrl+c")
        else:
            return values[0]