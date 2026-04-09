import os
import pdoc
import django
import shutil
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "arches_extensions.settings")

django.setup()

if (outdir := Path("docs")).is_dir():
    shutil.rmtree(outdir)
pdoc.pdoc("arches_extensions", output_directory=outdir)