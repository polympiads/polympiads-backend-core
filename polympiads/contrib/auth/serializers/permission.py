
from rest_framework import serializers

from polympiads.contrib.utils.serializers.mixins import BrowsableUrlMixin
from django.contrib.auth.models    import Permission

class PermissionDetailSerializer (BrowsableUrlMixin, serializers.ModelSerializer):
    permission = serializers.SerializerMethodField()

    def get_permission (self, permission: Permission):
        """Returns 'app_label.codename' - the format used in has_perm()"""
        return f"{permission.content_type.app_label}.{permission.codename}"

    class Meta:
        model = Permission
        fields = [ 'id', "name", "permission" ]

class PermissionSummarySerializer (BrowsableUrlMixin, serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = [ 'id', "name" ]

class PermissionSerializers:
    Detail  = PermissionDetailSerializer
    Summary = PermissionSummarySerializer
