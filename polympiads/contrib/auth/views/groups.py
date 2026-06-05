
from django.contrib.auth.models import Group

from polympiads.contrib.auth.filters.groups import GroupFilterMixin
from polympiads.contrib.auth.serializers.group import GroupSerializers

from polympiads.contrib.utils.pagination import StandardPagination
from polympiads.contrib.utils.views import MultiSerializerViewSet
from polympiads.contrib.utils.permissions import ModelPermissions, ActionPermissionMixin

class GroupViewSet (ActionPermissionMixin, GroupFilterMixin, MultiSerializerViewSet):
    pagination_class = StandardPagination
    
    permission_classes_default = [ModelPermissions]
    permission_classes_by_action = {}

    summary_serializer_class = GroupSerializers.List
    details_serializer_class = GroupSerializers.Detail

    queryset = Group.objects.all()
