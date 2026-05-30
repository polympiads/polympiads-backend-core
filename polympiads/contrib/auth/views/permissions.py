
from django.contrib.auth.models import Permission

from polympiads.contrib.auth.serializers.permission import PermissionSerializers

from polympiads.contrib.utils.views import MultiSerializerViewSet
from polympiads.contrib.utils.permissions import NeverAllow, ModelPermissions, ActionPermissionMixin

class PermissionViewSet (ActionPermissionMixin, MultiSerializerViewSet):
    permission_classes_default = [NeverAllow]

    permission_classes_by_action = {
        "get": [ModelPermissions]
    }

    summary_serializer_class = PermissionSerializers.Summary
    details_serializer_class = PermissionSerializers.Detail

    queryset = Permission.objects.all()
