# Commands

The management commands herein are generally designed like:

    python manage.py [topic] [operation] [--extra-options]

Where the topic may be `maplayer` and an operation may be `list` (list all maplayers).

For help, use

```
python manage.py [command] --help
```

to learn more about any specific command.

A brief overview of each command is provided below, but for the real details you should head to [management/commands](https://legiongis.github.io/arches-dev-tools/arches_dev_tools/management/commands.html) and browse the submodules documentation.


> **IMPORTANT** - Some of these commands will alter your database content, so it is always a good idea to back up your database before using them.

> **These are all a work in progress, some will surely fail right now** Also be aware that some of the commands will alter database content, though any changes to resources should be preceded with a confirmation prompt.

## `python manage.py extension`

Manage all custom extensions like widgets, functions, and datatypes. Full documentation:  [extension.py](https://legiongis.github.io/arches-dev-tools/arches_dev_tools/management/commands/extension.html)

## `python manage.py indexes`

Some utilities for managing ElasticSearch index content. Full documentation: [indexes.py](https://legiongis.github.io/arches-dev-tools/arches_dev_tools/management/commands/indexes.html)

## `python manage.py maplayer`

Add, remove, list maplayers. Full documentation: [maplayer.py](https://legiongis.github.io/arches-dev-tools/arches_dev_tools/management/commands/maplayer.html)