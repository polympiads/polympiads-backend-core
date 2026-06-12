
from rest_framework import serializers

from polympiads.contrib.auth.serializers.fields.permission import PermissionStringField
from polympiads.contrib.utils.serializers.mixins import BrowsableUrlMixin
from django.contrib.auth.models    import Permission

class PermissionDetailSerializer (BrowsableUrlMixin, serializers.ModelSerializer):
    permission = PermissionStringField(read_only=True)

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
