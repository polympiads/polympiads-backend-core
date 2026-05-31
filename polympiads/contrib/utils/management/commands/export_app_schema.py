
import yaml, json

from drf_spectacular.generators import SchemaGenerator

from django.core.management.base import BaseCommand

class AppFilteredSchemaGenerator(SchemaGenerator):
    def __init__(self, *args, app_label=None, **kwargs):
        self.app_label = app_label
        super().__init__(*args, **kwargs)

    def get_schema(self, request=None, public=False):
        schema = super().get_schema(request=request, public=public)
        return schema

    def _initialise_endpoints(self):
        super()._initialise_endpoints()
        if not self.app_label:
            return

        # self.endpoints is a list of (path, path_regex, method, callback)
        self.endpoints = [
            (path, path_regex, method, callback)
            for path, path_regex, method, callback in self.endpoints
            if getattr(callback, 'cls', None) and
               getattr(callback.cls, '__module__', '').startswith(self.app_label + '.')
        ]

class Command (BaseCommand):
    help = 'Export OpenAPI schema per app'

    def add_arguments(self, parser):
        parser.add_argument('app_label', type=str)
        parser.add_argument('--output', type=str, default=None)
        parser.add_argument('--format', choices=['yaml', 'json'], default='yaml')
    def handle(self, *args, **options):
        app_label = options['app_label']
        generator = AppFilteredSchemaGenerator(app_label=app_label)
        schema = generator.get_schema(request=None, public=True)

        if options['format'] == 'json':
            output = json.dumps(schema, indent=2)
        else:
            output = yaml.dump(schema, allow_unicode=True)

        if options['output']:
            with open(options['output'], 'w') as f:
                f.write(output)
            self.stdout.write(f"Schema written to {options['output']}")
        else:
            self.stdout.write(output)
