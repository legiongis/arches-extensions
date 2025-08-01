import os
import csv
import json
import logging
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from arches.app.models.models import Node, NodeGroup
from arches.app.models.resource import Resource
from arches.app.models.graph import Graph
from arches.app.search.search_engine_factory import SearchEngineInstance as se
from arches.app.models.tile import Tile

from arches_extensions.utils import ArchesHelpTextFormatter

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    """Generate a list of file names for file-list nodes within the
specific resources.

    Usage:

        python manage.py make_file_list

    Arguments:

        - `--resourceid`: Id for single instance to included.
        - `--graph`: Name of graph, all instances will be included.

    """

    def __init__(self, *args, **kwargs):
        self.help = self.__doc__

    def add_arguments(self, parser):

        parser.formatter_class = ArchesHelpTextFormatter

        parser.add_argument("--resourceid")

        parser.add_argument("--graph")

    def handle(self, *args, **options):

        resources = []
        id = None

        ## collect resources from arguments
        if options['resourceid']:
            id = options['resourceid']
            r = Resource.objects.get(pk=id)
            resources.append(r)
        elif options['graph']:
            id = options['graph']
            resources += Resource.objects.filter(graph__name=id)

        ## make list of individual resource entries
        output = []
        for res in resources:
            entry = self.process_resource(res)
            output.append(entry)

        ## make list of names for file nodes
        node_columns = set()
        for res in output:
            for node_name in res["file_data"].keys():
                node_columns.add(node_name)

        ## iterate all resource entries and create a row (list) for each one
        rows = []
        for res in output:
            row = [res["resourceid"], res["name"]]
            for file_node in node_columns:
                row.append(res["file_data"].get(file_node))
            rows.append(row)

        ## write header and all resource rows to CSV
        with open(f"file_data__{id}.csv", "w") as o:
            writer = csv.writer(o)
            writer.writerow(["resourceid", "name"] + list(node_columns))
            writer.writerows(rows)

    def process_resource(self, resource):

        ## get all file-list nodes for this resource's graph
        nodes = Node.objects.filter(datatype="file-list", graph__name=resource.graph.name)

        ## create lookup of node id to node name (to use later)
        node_lookup = {str(i.pk):i.name for i in nodes}

        ## stub out entry for this resource
        output = {
            "name": resource.displayname,
            "resourceid": str(resource.pk),
            "file_data": {}
        }

        ## stub out file data dict with all possible nodes for this resource
        stage_data = {str(i.pk): [] for i in nodes}

        ## get all tiles for this resource that contain any relevant nodes
        nodegroups = [i.nodegroup for i in nodes]
        tiles = Tile.objects.filter(nodegroup__in=nodegroups, resourceinstance=resource)

        ## iterate tiles and collect node data into
        for tile in tiles:
            for k, v in tile.data.items():
                if k in node_lookup:
                    # lose a little fidelity here by collapsing multiple instances of nodes but oh well
                    if v:
                        stage_data[k] += v

        ## use staged data and node_lookup to transform UUIDs to readable strings
        for k, v in stage_data.items():
            if len(v) > 0:
                output["file_data"][node_lookup[k]] = "|".join([i["name"] for i in v])

        return output
