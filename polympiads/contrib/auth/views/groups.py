
from django.contrib.auth.models import Group
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.response import Response

from polympiads.contrib.auth.filters.groups import GroupFilterMixin
from polympiads.contrib.auth.serializers.group import GroupSerializers

from polympiads.contrib.auth.serializers.modify.permissions import ModifyPermissionsSerializer
from polympiads.contrib.utils.pagination import StandardPagination
from polympiads.contrib.utils.views import MultiSerializerViewSet
from polympiads.contrib.utils.permissions import ModelPermissions, ActionPermissionMixin
from polympiads.contrib.utils.views.multi import extra_serializer

class GroupViewSet (ActionPermissionMixin, GroupFilterMixin, MultiSerializerViewSet):
    pagination_class = StandardPagination
    
    permission_classes_default = [ModelPermissions]
    permission_classes_by_action = {}

    summary_serializer_class = GroupSerializers.List
    details_serializer_class = GroupSerializers.Detail

    queryset = Group.objects.all()

    @extra_serializer(request=ModifyPermissionsSerializer, response=GroupSerializers.Detail)
    @action(detail=True, methods=['patch'], url_path="permissions")
    def permissions(self, request, pk=None):
        group = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        if add_permissions := data.get("add_permissions"):
            group.permissions.add(*add_permissions)

        if remove_permissions := data.get("remove_permissions"):
            group.permissions.remove(*remove_permissions)

        response_serializer = self.get_response_serializer(group)
        return Response(response_serializer.data)
