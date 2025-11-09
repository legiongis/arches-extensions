import os
import csv
import json
import logging
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from arches.app.models.models import Node, NodeGroup, File
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

        python manage.py get_files

    Arguments:

        - `--resource`: Id for single resource instance to include (optional)
        - `--graph`: Name of graph, all instances will be included (optional)
        - `--make-csv`: Exports a CSV list of all file info, named for graph or instance (default=False)
        - `--make-archive`: Creates a zip archive of all files, named for graph or instance (default=False)
        - `--include-orphans`: Includes File objects that are no longer in tile data, but do exist in the database (default=False)

    """

    def __init__(self, *args, **kwargs):
        self.help = self.__doc__

    def add_arguments(self, parser):

        parser.formatter_class = ArchesHelpTextFormatter

        parser.add_argument("--resource")
        parser.add_argument("--graph")
        parser.add_argument("--make-csv", action="store_true")
        parser.add_argument("--make-archive", action="store_true")
        parser.add_argument("--include-orphans", action="store_true")

    def handle(self, *args, **options):

        scopes = []

        ## get all relevant file objects
        if options["resource"]:
            scopes.append((options["resource"], File.objects.filter(tile__resourceinstance_id=scope)))
        elif options["graph"]:
            scopes.append((options["graph"], File.objects.filter(tile__resourceinstance__graph__name=options["graph"])))
        else:
            for graph in Graph.objects.filter(isresource=True).exclude(name="Arches System Settings"):
                scopes.append((graph.name, File.objects.filter(tile__resourceinstance__graph=graph)))

        ## process all scopes
        for scope, files in scopes:
            print(f"Getting files for: {scope}")
            info = self.collect_file_info(files, include_orphans=options["include_orphans"])
            if options["make_csv"]:
                if len(info) == 0:
                    print("no data to write, skipping")
                else:
                    for i in info:
                        del i['file path']
                    csv_name = f"{scope}__filelist"
                    if options["include_orphans"]:
                        csv_name += "__withorphans"
                    with open(f"{csv_name}.csv", "w") as o:
                        writer = csv.DictWriter(o, fieldnames=info[0].keys())
                        writer.writeheader()
                        writer.writerows(info)

            if options["make_archive"]:
                if len(info) == 0:
                    print("no files to archive, skipping")
                else:
                    usefiles = File.objects.filter(fileid__in=[i['file id'] for i in info])
                    zip_name = f"{scope}__files"
                    if options["include_orphans"]:
                        zip_name += "__withorphans"
                    with ZipFile(f"{zip_name}.zip", "w") as zip_file:
                        for f in usefiles:
                            with f.path.open("rb") as content:
                                zip_file.writestr(f.path.name.split("/")[-1], content.read())

    def collect_file_info(self, files, include_orphans=False):
        print(f"File objects: {files.count()}")

        ## quick check for missing files
        missing = []
        for f in files:
            if not f.path.storage.exists(f.path.name):
                print("file missing:", f.path.path)
                missing.append(f)
        print(f"Missing files to be skipped: {len(missing)}")
        files = [i for i in files if not i in missing]

        ## iterate files and create a lookup for tiles they are referenced by
        file_lookup = {}
        tile_lookup = {}
        for f in files:
            file_lookup[str(f.fileid)] = f
            tileid = str(f.tile_id)
            if not tileid in tile_lookup:
                tile_lookup[tileid] = Tile.objects.get(pk=tileid)
        print(f"Tiles with files in them: {len(tile_lookup)}")

        ## iterate all tiles that have been identified to have files,
        ## and collect the file ids that are stored in the tile data
        ## also make lookups for resources and nodes along the way for later use
        node_lookup = {}
        res_lookup = {}
        file_info = []
        files_without_id = []
        orphan_total = 0
        matched_total = 0
        for t, tile in tile_lookup.items():
            resid = str(tile.resourceinstance_id)
            res = res_lookup.get(resid, Resource.objects.get(pk=resid))
            if not resid in res_lookup:
                res_lookup[resid] = res
            found_ids = []
            for k, v in tile.data.items():
                node = node_lookup.get(k, Node.objects.get(pk=k))
                if not k in node_lookup:
                    node_lookup[k] = node
                if node.datatype == "file-list":
                    for i in v:
                        id = str(i['file_id'])
                        if id == "None":
                            files_without_id.append(i)
                            continue
                        found_ids.append(id)
                        matched_total += 1
                        file_info.append({
                            "resource id": resid,
                            "resource name": res.displayname,
                            "node name": node.name,
                            "file id": id,
                            "file name (original)": i['name'],
                            "file name (actual)": Path(file_lookup[id].path.name).name,
                            "file path": file_lookup[id].path.path,
                        })
            orphans = File.objects.filter(tile=tile).exclude(fileid__in=found_ids)
            orphan_total += orphans.count()
            if include_orphans:
                for orphan in orphans:
                    id = str(orphan.pk)
                    file_info.append({
                        "resource id": resid,
                        "resource name": res.displayname,
                        "node name": "<unknown>",
                        "file id": id,
                        "file name (original)": "<unknown>",
                        "file name (actual)": Path(file_lookup[id].path.name).name,
                        "file path": file_lookup[id].path.path,
                    })

        print(f"Files in tiles without fileids: {len(files_without_id)}")
        file_info.sort(key=lambda x: x['resource name'])
        print(f"Number of files actually referenced in tiles: {matched_total}")
        print(f"Number of orphaned files: {orphan_total}")
        return file_info
