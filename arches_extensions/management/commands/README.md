# Management commands overview

Use the **Submodules** menu on the left to navigate to detailed documentation for each command. All documentation is derived from docstrings within the codebase.

**Stable** commands:

*(none yet!)*

**Unstable** commands (functional but subject to change):

- [configure](./commands/configure.html)
    - Write derived systemd service files for backend components such as celery.
- [etl](./commands/etl.html)
    - Run ETL modules from the command line, especially useful during testing and development.
- [extension](./commands/extension.html)
    - Manage extensions within Arches such as custom widgets, datatypes, ETL modules, etc.
- [run_db_backup](./commands/run_db_backup.html)
    - A `pg_dump` wrapper that includes a sync to S3 using the AWS CLI. Implement this as a daily cronjob.
- [system-settings](./commands/system-settings.html)
    - Load Arches system settings Graph and Resource instance from standard locations.

**Incomplete** commands (partially functional but very much under construction):

- [bulk-update-tile](./commands/bulk-update-tile.html)
    - For managing bulk data updates to Tiles
- [get_files](./commands/get_files.html)
    - Check and interrogate File objects within the database as well as files on disk.
- [find_files](./commands/find_files.html)
    - Check and interrogate File objects within the database as well as files on disk.
- [indexes](./commands/indexes.html)
    - Operations for checking and repairing Elasticsearch resource indexes.
- [maplayer](./commands/maplayer.html)
    - Manage Map Layers.
- [resource](./commands/resource.html)
    - Manage resource instances (eventually this could replace `packages -o import_business_data`)