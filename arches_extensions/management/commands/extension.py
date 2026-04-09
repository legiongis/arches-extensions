from django.core.management.base import BaseCommand

from arches_extensions.utils import ArchesHelpTextFormatter, ArchesCLIStyles
from arches_extensions.managers import ExtensionManager

_s = ArchesCLIStyles()

class Command(BaseCommand):
    """
Use this command to manage extensions within Arches.

Usage:

    python manage.py extension [operation] [extension_type] [-s/--source] [-n/--name] [--overwrite]

Operations:

- `list`
    - Use `list` for quick inspection of the database. If you need to supply a `--name` 
for an operation, use the value that is printed by the `list` operation.
- `register`
    - When you `register` an extension a new database object for that extension instance is 
created. Add `--overwrite` 
update an existing instance based on the primary key of the extension defined in 
`--source`. Note: the name of the primary key field is different for every extension, 
but generally is something like "widgetid".
- `unregister`
    - Running `unregister` will delete the specified instance from the database.
- `activate`
    - The `activate` and `deactivate` operations are only valid operations for a few different
extension types. These actions alter an instance's `config['show']` value, but do not
create or delete the instance. A deactivated extension will be hidden from the user
interface but remain in the database.
- `deactivate`
    See above.

Extension types:

- `card-component`
- `datatype`
- `etl-module`
- `function`
- `plugin` &rarr; use this for "workflows"
- `report`
- `search-filter`
- `widget`


    """

    def __init__(self, *args, **kwargs):
        """ @private """
        self.help = self.__doc__

    def add_arguments(self, parser):
        # """@private"""
        parser.formatter_class = ArchesHelpTextFormatter
        parser.add_argument(
            "operation",
            choices=[
                "list",
                "register",
                "unregister",
                "activate",
                "deactivate",
            ],
            help=f"""OPERATION
            {_s.req('list')}: List registered extensions of the specified type. The {_s.opt('name')} of each extension is printed.
            {_s.req('register')}: Register extension from source file (provide {_s.opt('-s/--source')}).
            {_s.req('unregister')}: Unregister the specified extension (provide {_s.opt('-n/--name')}).
            {_s.req('activate')}: Activate this extension (not available for all extension types) (provide {_s.opt('-n/--name')}).
            {_s.req('deactivate')}: Deactivate this extension but don't unregister it (not available for all extension types, experimental) (provide {_s.opt('-n/--name')}).
            """
        )
        parser.add_argument(
            "extension_type",
            choices=[
                "card-component",
                "datatype",
                "etl-module",
                "function",
                "plugin",
                "report",
                "search-filter",
                "widget",
            ],
            help="""EXTENSION TYPE
            Specify what type of extension you are managing.
            """
        )
        parser.add_argument(
            "-s", "--source",
            help=f"Use with {_s.req('register')} to provide a JSON or .py file when registering an extension.",
        )
        parser.add_argument(
            "-n", "--name",
            help=f"Use with {_s.req('unregister')} for the name of the extension to remove."
        )
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help=f"Use with {_s.req('register')} to overwrite an existing extension with the provided source definition.",
        )

    def handle(self, *args, **options):

        ex = options["extension_type"]
        manager = ExtensionManager(extension_type=ex)

        # the list operation only makes sense in the context of the CLI,
        # so all code sits here, not in the manager.
        if options["operation"] == "list":
            manager.print_list()

        if options["operation"] == "register":
            print(f"Register {ex}: {options['source']} (overwrite = {options['overwrite']}")
            manager.register(options["source"], overwrite=options['overwrite'])

        if options["operation"] == "unregister":
            print(f"Unregister {ex}: {options['name']}")
            manager.unregister(options["name"])

        if options["operation"] == "activate":
            print(f"Activate {ex}: {options['name']}")
            manager.set_active(name=options["name"])

        if options["operation"] == "deactivate":
            print(_s.warn("Warning: Deactivating core Arches extensions, like the Advanced "\
            "search filter, may cause unintended consequences."))
            print(f"Deactivate {ex}: {options['name']}")
            manager.set_active(name=options["name"], active=False)
