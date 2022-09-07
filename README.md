# Arches Dev Tools

The purpose of this package is unify some custom utilities that I've been developing while I work on different Arches projects. It is a work in progress. Hopefully, some of this content will eventually become part of core Arches, and in the meantime I hope others find it helpful.

So far, it is just a suite of Django management commands, though more content may be added in the future.

**repo** -- [legiongis/arches-dev-tools](https://github.com/legiongis/arches-dev-tools)

**docs site** -- [legiongis.github.io/arches-dev-tools](https://legiongis.github.io/arches-dev-tools).

**get in touch** -- Feel free to [open a ticket](https://github.com/legiongis/arches-dev-tools/issues) or get in touch directly, adam@legiongis.com. I'd love to collaborate if you see something here that could be better, or if you have ideas for other utilities that should be added. The only requirement is that the content be generic, not implementation-specific.

# Installation

These tools are packaged as a Django app so they can be easily integrated into an existing Arches installation. For this to work, you must install this package into your Arches virtual environment like this:

```
pip install git+https://github.com/legiongis/arches-dev-tools.git --no-binary arches-dev-tools
```

Alternatively, you can fork/clone the repo and pip install from a local clone:

```
git clone https://github.com/legiongis/arches-dev-tools
pip install -e arches-dev-tools
```

Now, in your Arches project's `settings.py` file, add `arches_dev_tools` to your `INSTALLED_APPS`:

```
INSTALLED_APPS += ('arches_dev_tools', )
```

It may be wiser to place this in your project's `settings_local.py` file, just remember to import `INSTALLED_APPS`:

```
from .settings import INSTALLED_APPS
INSTALLED_APPS += ('arches_dev_tools', )
```

That's it! You can now start using these management commands and other utilities in your existing Arches project.

To confirm the installation, run

```
python manage.py --help
```

and you should see a new section called `arches_dev_tools` with a list of new commands.

## Uninstall

To uninstall the app, remove the `INSTALLED_APPS` line above and then run

```
pip uninstall arches-dev-tools
```
