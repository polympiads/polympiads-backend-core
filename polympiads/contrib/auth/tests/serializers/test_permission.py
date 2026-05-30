
from django.test import TestCase

from django.contrib.auth.models import Permission

from polympiads.contrib.auth.models.user import User
from polympiads.contrib.auth.serializers.permission import PermissionDetailSerializer, PermissionSummarySerializer

class TestPermissionDetailSerializer (TestCase):
    def setUp (self):
        self.permission = Permission.objects.first()

        self.assertIsNotNone(self.permission)
    
    def test_fixture_has_permissions(self):
        self.assertIsNotNone(self.permission)

    def test_fields_expected (self):
        serializer = PermissionDetailSerializer(self.permission)
        self.assertEqual(
            serializer.data.keys(),
            { "id", "name", "permission" }
        )

    def test_id_equals_permission_id (self):
        serializer = PermissionDetailSerializer(self.permission)
        self.assertEqual(
            serializer.data["id"],
            self.permission.pk
        )
    def test_name_equals_permission_name (self):
        serializer = PermissionDetailSerializer(self.permission)
        self.assertEqual(
            serializer.data["name"],
            self.permission.name
        )
    def test_permission_string_is_correct (self):
        serializer = PermissionDetailSerializer(self.permission)
        self.assertEqual(
            serializer.data["permission"],
            f"{self.permission.content_type.app_label}.{self.permission.codename}"
        )
    def test_permission_string_can_be_used_on_user (self):
        user = User.objects.create_user("user")
        user.user_permissions.add(self.permission)
        user.save()

        user.refresh_from_db()
        
        serializer = PermissionDetailSerializer(self.permission)
        self.assertTrue(user.has_perm(serializer.data["permission"]))

class TestPermissionSummarySerializer (TestCase):
    def setUp (self):
        self.permission = Permission.objects.first()

    def test_fixture_has_permissions(self):
        self.assertIsNotNone(self.permission)

    def test_fields_expected (self):
        serializer = PermissionSummarySerializer(self.permission)
        self.assertEqual(
            serializer.data.keys(),
            { "id", "name" }
        )

    def test_id_equals_permission_id (self):
        serializer = PermissionSummarySerializer(self.permission)
        self.assertEqual(
            serializer.data["id"],
            self.permission.pk
        )
    def test_name_equals_permission_name (self):
        serializer = PermissionSummarySerializer(self.permission)
        self.assertEqual(
            serializer.data["name"],
            self.permission.name
        )
