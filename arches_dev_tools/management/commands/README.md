# Commands

The management commands herein are generally designed like:

    python manage.py [topic] [operation] [--extra-options]

Where the topic may be `maplayer` and an operation may be `list` (list all maplayers).

> **IMPORTANT** - Some of these commands will alter your database content, so it is always a good idea to back up your database before using them.

In general, use `python manage.py [command] --help` to learn more about each management command. Some more explanation follows, or head to [management/commands](/arches_dev_tools/management/commands.html) and browse the submodules documentation.

## `extension`

Manage all custom extensions like widgets, functions, and datatypes. [Full Documentation](/arches_dev_tools/management/commands/extension.html)