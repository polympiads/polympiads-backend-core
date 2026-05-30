
from rest_framework import serializers
from django.contrib.auth.models import Group
from polympiads.contrib.utils.serializers.mixins import BrowsableUrlMixin
from .permission import PermissionDetailSerializer, PermissionSummarySerializer

class GroupDetailSerializer (BrowsableUrlMixin, serializers.ModelSerializer):
    permissions = PermissionDetailSerializer(many=True, read_only=True)
    
    class Meta:
        model = Group
        fields = [ 'id', 'name', 'permissions' ]

class GroupListSerializer (BrowsableUrlMixin, serializers.ModelSerializer):
    permissions = PermissionSummarySerializer(many=True, read_only=True)

    class Meta:
        model = Group
        fields = [ 'id', 'name', 'permissions' ]

class GroupSummarySerializer (BrowsableUrlMixin, serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = [ 'id', 'name' ]

class GroupSerializers:
    Detail  = GroupDetailSerializer
    List    = GroupListSerializer
    Summary = GroupSummarySerializer
