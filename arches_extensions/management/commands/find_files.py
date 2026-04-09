import os
import json
import psycopg2
from pathlib import Path

from datetime import datetime
from django.conf import settings
from django.core.management.base import BaseCommand
from django.contrib.gis.gdal import DataSource  # type: ignore
from django.contrib.gis.geos import MultiPolygon

from arches.app.models.resource import Resource
from arches.app.models.models import Node, File
from arches.app.models.tile import Tile


class Command(BaseCommand):

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):

        fnodes = Node.objects.filter(datatype="file-list", graph__name="Scout Report")
        nids = [str(i) for i in fnodes.values_list("pk", flat=True)]
        ngs = fnodes.values_list("nodegroup", flat=True)

        resources = Resource.objects.filter(createdtime__gte="2019-10-21", createdtime__lte="2020-06-30",graph__name="Scout Report")
        print(resources.count())
        res_with_img = []
        local_files = []
        for res in resources:
            tiles = Tile.objects.filter(nodegroup__in=ngs, resourceinstance_id=res.pk)
            if tiles.count() > 0:
                res_with_img.append(res)

            for t in tiles:
                for k in t.data.keys():
                    if k in nids and t.data[k] is not None:
                        for f in t.data[k]:
                            fileid = f['file_id']
                            ff = File.objects.get(pk=fileid)
                            local_path = Path("../photo-archive", str(ff.path).split("/")[-1])
                            if local_path.is_file():
                                print("resource: ", res.pk)
                                print(res.createdtime)
                                print(local_path)
                                local_files.append(local_path)
        print(len(res_with_img))
        print(len(local_files))

        print("---")


        tiles = Tile.objects.filter(nodegroup__in=ngs)
        used_ids = set()
        file_entries = []
        for t in tiles:
            to_save = False
            resid = str(t.resourceinstance.pk)
            tileid = str(t.pk)
            for k in t.data.keys():
                if k in nids and t.data[k] is not None:
                    for f in t.data[k]:
                        fileid = f['file_id']
                        f['resourceinstanceid'] = resid
                        f['tileid'] = tileid
                        used_ids.add(fileid)
                        file_entries.append(f)

        file_entries.sort(key=lambda k:k['name'])
        print(f"number of file entries in tiles: {len(file_entries)}")
        fileids_in_tiles = [i['file_id'] for i in file_entries]
#        for fe in file_entries:
#            if fileids_in_tiles.count(fe['file_id']) > 1:
#                print(fe['resourceinstanceid'], fe['file_id'], fe['name'])

        all_files = File.objects.all()
        print(f"total number of File objects: {all_files.count()}")

        orphan_files = File.objects.exclude(pk__in=used_ids)
        print(f"orphaned File objects: {orphan_files.count()}")

    def load_areas(self, source, group_names, level="", category=""):

        # generate load_id from filename and time.
        source_file = os.path.basename(source)
        file_name = os.path.splitext(source_file)[0]
        time_id = datetime.strftime(datetime.now(), "%m%d%y-%H%M%S")
        load_id = f"{file_name}__{time_id}"

        add_to_groups = []
        for group_name in group_names:
            try:
                group = ManagementAreaGroup.objects.get(name=group_name)
                response = input(f"Add to existing group '{group_name}'? Y/n ")
                if response.lower().startswith("n"):
                    exit()
            except ManagementAreaGroup.DoesNotExist:
                response = input(f"Create new group '{group_name}'? Y/n ")
                if response.lower().startswith("n"):
                    exit()
                group = ManagementAreaGroup.objects.create(name=group_name)
            add_to_groups.append(group)

        cat = None
        if category != "":
            if len(ManagementAreaCategory.objects.filter(name=category)) == 0:
                response = input(f"Create new category '{category}'? Y/n ")
                if response.lower().startswith("n"):
                    exit()
                cat = ManagementAreaCategory.objects.create(name=category)
            else:
                cat = ManagementAreaCategory.objects.get(name=category)

        # load the source file as an iterable layer. this method performs some
        # data integrity checks as well.
        dataset = self.load_source(source)

        # allow all case combinations for name field. previous check in
        # load_source ensures this won't fail.
        name_field = [i for i in dataset.fields if i.lower() == "name"][0]

        load_ct = 0
        for feature in dataset:
            geom = None
            if feature.geom.geom_type == "Polygon":
                geom = MultiPolygon(feature.geom.geos)
            elif feature.geom.geom_type == "MultiPolygon":
                geom = feature.geom.geos
            else:
                print("skipping invalid geom type: " + feature.geom.geom_type)
            new_ma = ManagementArea.objects.create(
                name=feature.get(name_field),
                geom=geom,
                load_id=load_id,
            )
            if category != "":
                new_ma.category = cat
            if level != "":
                new_ma.management_level = level
            new_ma.save()

            for group in add_to_groups:
                group.areas.add(new_ma)
            load_ct += 1

        print(f"{load_ct} Management Areas loaded.")
        print(f"load id: {load_id}")

        print("recreating materialized views")
        self.make_views()

        print("to undo to this load, run:")
        print(f"\n    python manage.py areas remove --load-id {load_id}\n")

    def load_source(self, source):

        try:
            ds = DataSource(source)
            layer = ds[0]
        except Exception as e:
            print("error loading datasource:")
            print(e)
            exit()

        # check for name field
        if "name" not in [i.lower() for i in layer.fields]:
            print("cancelling: no 'name' field present in dataset.")
            exit()

        # check SRID in first feature:
        for feature in layer:
            if feature.geom.srid != 4326:
                print(f"invalid SRID: {feature.geom.srid}.")
                print(
                    "cancelling: reproject dataset to EPGS:4326 (WGS84) "
                    "before trying again."
                )
                exit()
            break

        return layer

    def remove_areas(self, load_id):
        ma = ManagementArea.objects.filter(load_id=load_id)
        if len(ma) == 0:
            print("No Management Areas match this load id.")
            exit()
        response = input(f"Remove {len(ma)} Management Areas? Y/n ")
        if response.lower().startswith("n"):
            exit()
        ma.delete()

        print("recreating materialized views")
        self.make_views()

    def list_load_ids(self):

        ids = ManagementArea.objects.all().values("load_id").distinct()
        for id in ids:
            print(id)

    def make_hms_viewname(self, basename):

        prefix = "mv_hms"
        name = basename.lower().replace(" ", "_").replace("-", "_")
        view_name = f"{prefix}_{name}"

        return view_name

    def make_views(self, category=""):

        db = settings.DATABASES["default"]
        db_conn = "dbname = {} port = {} user = {} host = {} password = {}".format(
            db["NAME"], db["PORT"], db["USER"], db["HOST"], db["PASSWORD"]
        )
        conn = psycopg2.connect(db_conn)

        for cat in ManagementAreaCategory.objects.all():
            if category and cat.name != category:
                continue

            view_name = self.make_hms_viewname(cat.name)

            print(f"category: {cat.name}")
            print(f"creating materialized view {view_name}")

            sql = f"""
            DROP MATERIALIZED VIEW IF EXISTS {view_name};
            CREATE MATERIALIZED VIEW {view_name}
            AS
            SELECT * FROM hms_managementarea
            WHERE category_id = {cat.pk};
            """

            with conn.cursor() as cursor:
                cursor.execute(sql)
            conn.commit()

    def refresh_views(self, category=""):

        db = settings.DATABASES["default"]
        db_conn = "dbname = {} port = {} user = {} host = {} password = {}".format(
            db["NAME"], db["PORT"], db["USER"], db["HOST"], db["PASSWORD"]
        )
        conn = psycopg2.connect(db_conn)

        for cat in ManagementAreaCategory.objects.all():
            if category and cat.name != category:
                continue

            view_name = self.make_hms_viewname(cat.name)

            print(f"refreshing materialized view {view_name}")

            with conn.cursor() as cursor:
                cursor.execute(f"REFRESH MATERIALIZED VIEW {view_name};")
            conn.commit()

        conn.close()

