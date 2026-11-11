'''
ARCHES - a program developed to inventory and manage immovable cultural heritage.
Copyright (C) 2013 J. Paul Getty Trust and World Monuments Fund

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
'''

import uuid

from arches.app.models.graph import Graph
from arches.app.models.models import FunctionXGraph, Relation, TileModel, Value
from arches.app.models.resource import Resource
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """
    Commands for managing the loading and running of packages in Arches

    """

    def add_arguments(self, parser):

        parser.add_argument('resourcemodel', action='store', default=None,
            help='Name of Resource Model whose display descriptor values you want to reorder.')

        parser.add_argument('--name', action='store', default=None,
            help='The label or UUID of the name type that should be pushed to the top.')

        parser.add_argument('--description', action='store', default=None,
            help='The label or UUID of the description type that should be pushed to the top.')

        parser.add_argument('--map_popup', action='store', dest=None,
            help='The label or UUID of the map_popup description type that should be pushed to the top.')

    def handle(self, *args, **options):

        graph = Graph.objects.get(name=options['resourcemodel'])

        self.verbose = options["verbosity"] > 1

        nametype_value = self.get_value_from_input(options['name'])
        desctype_value = self.get_value_from_input(options['description'])
        popuptype_value = self.get_value_from_input(options['map_popup'])

        descriptor_function = FunctionXGraph.objects.get(
            function_id="60000000-0000-0000-0000-000000000001",
            graph=graph,
        )

        resources = Resource.objects.filter(graph_id=descriptor_function.graph_id)
        totalct = resources.count()

        print("name type:", options['name'], nametype_value)
        print("description type:", options['description'], desctype_value)
        print("popuptype type:", options['map_popup'], popuptype_value)

        print(f"resources to process: {totalct}")
        update_ct = 0
        for n, resource in enumerate(resources, start=1):

            if self.verbose:
                print(resource.pk)

            updated = self.process_resource(resource, descriptor_function.config,
                nametype=nametype_value,
                desctype=desctype_value,
                popuptype=popuptype_value
            )
            if updated:
                update_ct += 1

            if (n) % 1000 == 0:
                print(n),
            if n == totalct:
                print(n)

        print(f"{update_ct}/{totalct} resources updated")
        print("\nif any resources were updated, you must reindex them with this command:")
        print(f"\n    uv run manage.py es index_resources_by_type -rt {graph.pk} -rd")

    def process_resource(self, resource, config, nametype=None, desctype=None, popuptype=None):

        resid = resource.resourceinstanceid

        name_updated, desc_updated, popup_updated = None, None, None
        if nametype is not None:
            name_updated = self.reorder_tiles(resid, config['name']['nodegroup_id'], nametype)
        if desctype is not None:
            desc_updated = self.reorder_tiles(resid, config['description']['nodegroup_id'], desctype)
        if popuptype is not None:
            popup_updated = self.reorder_tiles(resid, config['map_popup']['nodegroup_id'], popuptype)

        resource_updated = any([name_updated, desc_updated, popup_updated])
        if resource_updated:
            resource.save()

        return resource_updated

    def reorder_tiles(self, resourceid, nodegroup, typevalue) -> bool:
        """ Reorders the tiles so the one matching in the input value has the
        lowest (first) sortorder. Return False if there aren't enough tiles to reorder (<=1). """

        tiles = TileModel.objects.filter(nodegroup_id=nodegroup, resourceinstance_id=resourceid).order_by("sortorder")
        if tiles.count() <= 1:
            if self.verbose:
                print("-- skipping, not enough tiles")
            return False

        primarytileuuid = None
        input_order = []
        for t in tiles:
            input_order.append((t.sortorder, str(t.pk)))
            if str(typevalue.valueid) in t.data.values():
                t.sortorder = 0
                t.save()
                primarytileuuid = t.tileid
        
        # this means that the primary tile has been found and handled.
        # all other tiles must be re-saved with ascending sortorder
        if primarytileuuid is not None:
            for n, t in enumerate(tiles.exclude(tileid=primarytileuuid).order_by("sortorder")):
                t.sortorder = n+1
                t.save()

        # refetch the tiles to see if the order did change
        tiles = TileModel.objects.filter(nodegroup_id=nodegroup, resourceinstance_id=resourceid).order_by("sortorder")
        output_order = []
        for t in tiles:
            output_order.append((t.sortorder, str(t.pk)))

        changed = input_order != output_order
        if self.verbose:
            if changed:
                print("BEFORE:")
                for i in input_order:
                    print(i)
                print("AFTER:")
                for i in output_order:
                    print(i)
            else:
                print("-- no change made")

        return changed

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
            print("input value '{}' not found").format(input)
            exit()
        elif values.count() > 1:
            print("multiple labels found. please choose one of the following:")
            choice_dict = {}
            for n, val in enumerate(values):
                parent_concept = Relation.objects.get(relationtype_id="member", conceptto=val.concept_id)
                parent_label = Value.objects.filter(concept_id=parent_concept.conceptfrom.conceptid)[0]
                print("{} - {} - {} --> {}").format(n+1, val.valueid, parent_label.value, val.value)
                choice_dict[str(n+1)] = val
            while True:
                choice = input("choose by entering one of the numbers above: ")
                if choice in choice_dict:
                    return choice_dict[choice]
                else:
                    print("invalid choice. to quit, use ^c")
        else:
            return values[0]
