# Arches Dev Tools

The purpose of [this repository](https://github.com/legiongis/arches-dev-tools) is to consolidate and streamline some custom utilities that I've been developing while I work on different Arches projects. It is a work in progress. Hopefully, some of this content will eventually become part of core Arches.

**docs site**: [legiongis.github.io/arches-dev-tools](https://legiongis.github.io/arches-dev-tools).

**get in touch!** I'd love to collaborate if you see something here that could be better, or if you have ideas for other utilities that should be added. The only requirement is that the content be generic, not implementation-specific.

Feel free to [open a ticket](https://github.com/legiongis/arches-dev-tools/issues) or get in touch directly, adam@legiongis.com.

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

Now, in your `settings.py` or `settings_local.py` file, add `arches_dev_tools` to your `INSTALLED_APPS`:

```
INSTALLED_APPS += ('arches_dev_tools',)
```

> In `settings_local.py`, add `from .settings import INSTALLED_APPS` to the top of the file.

That's it! You can now start using these management commands and other utilities in your existing Arches project. To confirm, run

```
python manage.py --help
```

and you should see a new section called `arches_dev_tools` with a list of all management commands.

## Uninstall

To remove this app, remove the `INSTALLED_APPS` line above, and then run

```
pip uninstall arches-dev-tools
```
