
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response

from polympiads.contrib.auth.filters.users import UserFilterMixin
from polympiads.contrib.auth.models import User
from polympiads.contrib.auth.serializers.user import UserSerializers
from polympiads.contrib.utils.pagination import StandardPagination
from polympiads.contrib.utils.views import MultiSerializerViewSet
from polympiads.contrib.utils.permissions import ModelPermissions, ActionPermissionMixin

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
