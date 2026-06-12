
from rest_framework import serializers

from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import Permission
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.openapi import OpenApiTypes

@extend_schema_field(OpenApiTypes.STR)
class PermissionStringField (serializers.Field):
    """For output only - formats a Permission instance as 'app_label.codename'."""
    def __init__ (self, **kwargs):
        kwargs.setdefault("source", "*")
        return super().__init__(**kwargs)
    
    def to_representation(self, obj):
        return f"{obj.content_type.app_label}.{obj.codename}"

@extend_schema_field(OpenApiTypes.STR)
class PermissionStringRelatedField (serializers.RelatedField):
    """
    A read-write field that targets permissions with their
    codename and app_label combined as the standard 'app_label.codename'
    """
    default_error_messages = {
        "invalid_type": _("Expected a string, got {type}."),
        'does_not_exist': _('Permission with app_label.codename={value} does not exist.'),
        'invalid_format': _('Expected format: app_label.codename, got \'{value}\'.')
    }

    def get_queryset(self):
        return Permission.objects.select_related("content_type")

    def to_internal_value(self, data):
        if not isinstance(data, str):
            self.fail("invalid_type", type=type(data).__name__)

        try:
            app_label, codename = data.split(".")
        except ValueError:
            self.fail("invalid_format", value=data)
        
        try:
            return self.get_queryset().get(
                content_type__app_label=app_label,
                codename=codename,
            )
        except Permission.DoesNotExist:
            self.fail("does_not_exist", value=data)

    def to_representation(self, obj):
        return f"{obj.content_type.app_label}.{obj.codename}"
