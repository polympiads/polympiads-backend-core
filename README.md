
# Polympiads Backend Core

This code is the main entrypoint of the Polympiads architecture.
It contains the skeleton for a default django project, a custom DRF
authentication app with API calls supporting querying and updating
users, permissions and groups as well as a login, as well as some utils.

# Creating a plugin

In order to create a plugin, you should create a github repo that contains
a standard `manage.py` from django, a `plugin_settings.py` (that will be used
for testing the plugin) and a `requirements.txt` containing
`git+https://github.com/polympiads/polympiads-backend-core.git` as well as the
other polympiads plugins your plugin depends on. After that, you can create a
`test.sh` that tests only your plugin with the same structure as the `test.sh`.

Now your plugin is ready to go ! To make it available for other plugins as a dependency,
you should add a `pyproject.toml` (you may follow the template from this repo).

## Registering routes

You should register your routes for an application in `apps.py`.
See `polympiads.contrib.auth.apps` for an example.

## Django App structure

- `filters/`: set of filters for the different views
- `views/`: set of views
- `serializers/`: set of serializers
- `models/`: models of app
- `signals/`: signals and receivers for the app
- `tests/`: tests of your app

## Making views

Most of your views should extend all of the classes in the following oreder:
`ActionPermissionMixin, XFilterMixin, MultiSerializerViewSet` where `XFilterMixin`
is the mixin for your filters. For the simplest example, take a look at
`polympiads.contrib.auth.views.permissions`.

## Making serializers

Most of your serializers should extend `BrowsableUrlMixin`. Using this will allow
you to move in between the objects in the Browsable vue of DjangoRestFramework as
well as displaying a warning that these URLs will disappear in the final serializer.

# Combining plugins into your full app

In order to create the app, you should create a github repo that contains
a standard `manage.py` from django, a `project_settings.py` and a `requirements.txt`
containing all the plugins you need. After that, you should register your plugins and their
settings inside your project settings.
