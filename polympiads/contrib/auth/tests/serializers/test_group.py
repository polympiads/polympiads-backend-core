
from django.test import TestCase

from django.contrib.auth.models import Permission, Group

from polympiads.contrib.auth.serializers.group import GroupDetailSerializer, GroupSummarySerializer, GroupListSerializer
from polympiads.contrib.auth.serializers.permission import PermissionDetailSerializer, PermissionSummarySerializer

class TestGroupSummarySerializer (TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.group1 = Group.objects.create(name = "My Group 1")
        cls.group2 = Group.objects.create(name = "My Group 2")
        cls.group3 = Group.objects.create(name = "My Group 3")

        cls.group2.permissions.set([ Permission.objects.first() ])
        cls.group3.permissions.set(Permission.objects.all())

        return super().setUpTestData()

    def test_fields_expected (self):
        serializer = GroupSummarySerializer(self.group1)
        self.assertEqual(
            serializer.data.keys(),
            { "id", "name" }
        )
    def test_serialized (self):
        for group in [ self.group1, self.group2, self.group3 ]:
            serializer = GroupSummarySerializer(group)
            self.assertEqual( serializer.data["id"], group.pk )
            self.assertEqual( serializer.data["name"], group.name )

class TestGroupListSerializer (TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.group1 = Group.objects.create(name = "My Group 1")
        cls.group2 = Group.objects.create(name = "My Group 2")
        cls.group3 = Group.objects.create(name = "My Group 3")

        cls.group2.permissions.set([ Permission.objects.first() ])
        cls.group3.permissions.set(Permission.objects.all())

        return super().setUpTestData()

    def test_fields_expected (self):
        serializer = GroupListSerializer(self.group1)
        self.assertEqual(
            serializer.data.keys(),
            { "id", "name", "permissions" }
        )
    def test_serialized (self):
        for group in [ self.group1, self.group2, self.group3 ]:
            serializer = GroupListSerializer(group)
            self.assertEqual( serializer.data["id"], group.pk )
            self.assertEqual( serializer.data["name"], group.name )

            permissions = []
            for permission in group.permissions.all():
                permissions.append(PermissionSummarySerializer(permission).data)
                
            self.assertEqual( serializer.data["permissions"], permissions )

class TestGroupDetailsSerializer (TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.group1 = Group.objects.create(name = "My Group 1")
        cls.group2 = Group.objects.create(name = "My Group 2")
        cls.group3 = Group.objects.create(name = "My Group 3")

        cls.group2.permissions.set([ Permission.objects.first() ])
        cls.group3.permissions.set(Permission.objects.all())

        return super().setUpTestData()

    def test_fields_expected (self):
        serializer = GroupDetailSerializer(self.group1)
        self.assertEqual(
            serializer.data.keys(),
            { "id", "name", "permissions" }
        )
    def test_serialized (self):
        for group in [ self.group1, self.group2, self.group3 ]:
            serializer = GroupDetailSerializer(group)
            self.assertEqual( serializer.data["id"], group.pk )
            self.assertEqual( serializer.data["name"], group.name )

            permissions = []
            for permission in group.permissions.all():
                permissions.append(PermissionDetailSerializer(permission).data)
                
            self.assertEqual( serializer.data["permissions"], permissions )

