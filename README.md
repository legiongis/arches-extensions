# arches-extended-cli
Extra CLI commands to help with managing Arches. The intention with this app is to streamline the management of core Arches paradigms, like extensions, resources, and map layers, just to name a few.

## Install

```
git clone https://github.com/legiongis/arches-extended-cli
pip install -e arches-exteneded-cli
```

In your `settings.py`, add `arches_extended_cli` to your `INSTALLED_APPS`:

```
INSTALLED_APPS += ('arches_extended_cli',)
