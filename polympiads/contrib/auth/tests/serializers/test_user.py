
import datetime

from django.test import TestCase

from django.contrib.auth.models import Group, Permission
from polympiads.contrib.auth.serializers.user import UserDetailSerializer, UserListSerializer, UserSummarySerializer
from polympiads.contrib.auth.serializers.group import GroupDetailSerializer, GroupSummarySerializer
from polympiads.contrib.auth.serializers.permission import PermissionSummarySerializer, PermissionDetailSerializer
from polympiads.contrib.auth.models import User

class BaseTestUserSerializer (TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.group1 = Group.objects.create(name = "My Group 1")
        cls.group2 = Group.objects.create(name = "My Group 2")
        cls.group3 = Group.objects.create(name = "My Group 3")

        cls.group2.permissions.set([ Permission.objects.first() ])
        cls.group3.permissions.set(Permission.objects.all())

        cls.user1 = User.objects.create(
            username   = "user1",
            is_active  = False,
            first_name = "User",
            last_name  = "Name",
            email      = "user.name@example.org"
        )
        cls.user2 = User.objects.create(username = "user2")
        cls.user3 = User.objects.create(username = "user3", is_staff = True)
        cls.user4 = User.objects.create(username = "user4", is_staff = True, is_superuser = True)

        cls.user2.user_permissions.set([ Permission.objects.first() ])
        cls.user3.user_permissions.set(Permission.objects.all())
        cls.user4.user_permissions.set(Permission.objects.all())

        cls.user2.groups.set([ cls.group1 ])
        cls.user3.groups.set(Group.objects.all())

        return super().setUpTestData()

class TestUserListSerializer (BaseTestUserSerializer):
    def test_fields_expected (self):
        serializer = UserListSerializer(self.user1)
        self.assertEqual(
            serializer.data.keys(),
            { 'id', 'username', 'is_active', 'is_staff', 'is_superuser', 'groups', 'permissions',
              'first_name', 'last_name', 'email', 'last_login', 'date_joined' }
        )
    
    def test_user_serialized (self):
        for user in [ self.user1, self.user2, self.user3, self.user4 ]:
            serializer = UserListSerializer(user)
            self.assertEqual(serializer.data["id"], user.pk)
            self.assertEqual(serializer.data["username"], user.username)
            self.assertEqual(serializer.data["is_active"], user.is_active)
            self.assertEqual(serializer.data["is_staff"], user.is_staff)
            self.assertEqual(serializer.data["is_superuser"], user.is_superuser)
            self.assertEqual(serializer.data["first_name"], user.first_name)
            self.assertEqual(serializer.data["last_name"], user.last_name)
            self.assertEqual(serializer.data["last_login"], user.last_login)
            self.assertEqual(
                datetime.datetime.fromisoformat(serializer.data["date_joined"]),
                user.date_joined)

            groups, permissions = [], []
            for group in user.groups.all():
                groups.append(GroupSummarySerializer(group).data)
            for permission in user.user_permissions.all():
                permissions.append(PermissionSummarySerializer(permission).data)
            
            self.assertEqual(serializer.data["groups"], groups)
            self.assertEqual(serializer.data["permissions"], permissions)

class TestUserDetailsSerializer (BaseTestUserSerializer):
    def test_fields_expected (self):
        serializer = UserDetailSerializer(self.user1)
        self.assertEqual(
            serializer.data.keys(),
            { 'id', 'username', 'is_active', 'is_staff', 'is_superuser', 'groups', 'permissions',
              'first_name', 'last_name', 'email', 'last_login', 'date_joined' }
        )
    
    def test_user_serialized (self):
        for user in [ self.user1, self.user2, self.user3, self.user4 ]:
            serializer = UserDetailSerializer(user)
            self.assertEqual(serializer.data["id"], user.pk)
            self.assertEqual(serializer.data["username"], user.username)
            self.assertEqual(serializer.data["is_active"], user.is_active)
            self.assertEqual(serializer.data["is_staff"], user.is_staff)
            self.assertEqual(serializer.data["is_superuser"], user.is_superuser)
            self.assertEqual(serializer.data["first_name"], user.first_name)
            self.assertEqual(serializer.data["last_name"], user.last_name)
            self.assertEqual(serializer.data["last_login"], user.last_login)
            self.assertEqual(
                datetime.datetime.fromisoformat(serializer.data["date_joined"]),
                user.date_joined)

            groups, permissions = [], []
            for group in user.groups.all():
                groups.append(GroupDetailSerializer(group).data)
            for permission in user.user_permissions.all():
                permissions.append(PermissionDetailSerializer(permission).data)
            
            self.assertEqual(serializer.data["groups"], groups)
            self.assertEqual(serializer.data["permissions"], permissions)

class TestUserSummarySerializer (BaseTestUserSerializer):
    def test_fields_expected (self):
        serializer = UserSummarySerializer(self.user1)
        self.assertEqual(
            serializer.data.keys(),
            { 'id', 'username' }
        )
    
    def test_user_serialized (self):
        for user in [ self.user1, self.user2, self.user3, self.user4 ]:
            serializer = UserDetailSerializer(user)
            self.assertEqual(serializer.data["id"], user.pk)
            self.assertEqual(serializer.data["username"], user.username)
