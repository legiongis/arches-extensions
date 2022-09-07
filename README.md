# Arches Dev Tools

Extra CLI commands to help with managing Arches. The intention with this app is to streamline the management of core Arches paradigms, like extensions, resources, and map layers, just to name a few.

## Install

After installing Arches into your Python virtual environment, you can pip install this package directly from GitHub like so:

```
pip install git+https://github.com/legiongis/arches-dev-tools.git
```

Or, you can fork/clone this repo and pip install from a local clone:

```
git clone https://github.com/legiongis/arches-dev-tools.git
pip install -e arches-dev-tools
```

Now, in your `settings.py`, add `arches_dev_tools` to your `INSTALLED_APPS`:

```
INSTALLED_APPS += ('arches_dev_tools',)
```

That's it! You can now start using these management commands and other utilities in your existing Arches project.
