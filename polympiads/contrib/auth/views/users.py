
from polympiads.contrib.auth.models import User
from polympiads.contrib.auth.serializers.user import UserSerializers

from polympiads.contrib.utils.views import MultiSerializerViewSet
from polympiads.contrib.utils.permissions import ModelPermissions, ActionPermissionMixin

class UserViewSet (ActionPermissionMixin, MultiSerializerViewSet):
    permission_classes_default = [ModelPermissions]
    permission_classes_by_action = {}

    summary_serializer_class = UserSerializers.List
    details_serializer_class = UserSerializers.Detail

    queryset = User.objects.all()
