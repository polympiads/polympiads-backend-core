
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response

from polympiads.contrib.auth.filters.users import UserFilterMixin
from polympiads.contrib.auth.models import User
from polympiads.contrib.auth.serializers.modify.groups import ModifyGroupsSerializer
from polympiads.contrib.auth.serializers.modify.permissions import ModifyPermissionsSerializer
from polympiads.contrib.auth.serializers.user import UserSerializers
from polympiads.contrib.utils.pagination import StandardPagination
from polympiads.contrib.utils.views import MultiSerializerViewSet
from polympiads.contrib.utils.permissions import ModelPermissions, ActionPermissionMixin
from polympiads.contrib.utils.views.multi import extra_serializer

class UserViewSet (ActionPermissionMixin, UserFilterMixin, MultiSerializerViewSet):
    pagination_class = StandardPagination

    permission_classes_default = [ModelPermissions]
    permission_classes_by_action = {
        "me": [IsAuthenticated]
    }

    summary_serializer_class = UserSerializers.List
    details_serializer_class = UserSerializers.Detail

    queryset = User.objects.all()

    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @extra_serializer(request=ModifyPermissionsSerializer, response=UserSerializers.Detail)
    @action(detail=True, methods=['patch'], url_path="permissions")
    def permissions(self, request, pk=None):
        user = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        if add_permissions := data.get("add_permissions"):
            user.user_permissions.add(*add_permissions)

        if remove_permissions := data.get("remove_permissions"):
            user.user_permissions.remove(*remove_permissions)

        response_serializer = self.get_response_serializer(user)
        return Response(response_serializer.data)

    @extra_serializer(request=ModifyGroupsSerializer, response=UserSerializers.Detail)
    @action(detail=True, methods=['patch'], url_path="groups")
    def groups(self, request, pk=None):
        user = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        if add_groups := data.get("add_groups"):
            user.groups.add(*add_groups)

        if remove_groups := data.get("remove_groups"):
            user.groups.remove(*remove_groups)

        response_serializer = self.get_response_serializer(user)
        return Response(response_serializer.data)
