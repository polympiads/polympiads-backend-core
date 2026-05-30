
from rest_framework import serializers

from django.contrib.auth.password_validation import validate_password as django_validate_password
from django.core.exceptions import ValidationError as DjangoValidationError

from polympiads.contrib.auth.models import User
from .group      import GroupDetailSerializer, GroupSummarySerializer
from .permission import PermissionDetailSerializer, PermissionSummarySerializer
from polympiads.contrib.utils.serializers.mixins import BrowsableUrlMixin

USER_SUMMARY_FIELDS = [ 'id', 'username' ]
USER_LIST_FIELDS = USER_SUMMARY_FIELDS \
    + [ 'first_name', 'last_name', 'email' ] \
    + [ 'is_active', 'is_staff', 'is_superuser' ] \
    + [ 'groups', 'permissions', 'last_login', 'date_joined' ]
USER_DETAILS_FIELDS = USER_LIST_FIELDS + [ 'password' ]

class UserDetailSerializer (BrowsableUrlMixin, serializers.ModelSerializer):
    groups = GroupDetailSerializer(many=True, read_only=True)
    permissions = PermissionDetailSerializer(many = True, read_only = True, source="user_permissions")

    password = serializers.CharField(
        write_only=True, required=False,
        style={'input_type': 'password'},
    )

    def validate_password(self, value):
        try:
            django_validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value
    
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = super().create(validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user

    class Meta:
        model  = User
        fields = USER_DETAILS_FIELDS
        read_only_fields = ['last_login', 'date_joined']

class UserListSerializer (BrowsableUrlMixin, serializers.ModelSerializer):
    groups = GroupSummarySerializer(many=True, read_only=True)
    permissions = PermissionSummarySerializer(many=True, read_only=True, source="user_permissions")
    
    class Meta:
        model  = User
        fields = USER_LIST_FIELDS
        read_only_fields = ['last_login', 'date_joined']
    
class UserSummarySerializer (BrowsableUrlMixin, serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = USER_SUMMARY_FIELDS

class UserSerializers:
    Detail  = UserDetailSerializer
    List    = UserListSerializer
    Summary = UserSummarySerializer
