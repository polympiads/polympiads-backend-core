import pytest
from django.contrib.auth.models import Permission
from polympiads.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from polympiads.contrib.auth.views.permissions import PermissionViewSet

# Adjust these imports to match your project structure:
# from myapp.views import PermissionViewSet

factory = APIRequestFactory()


def make_user(username, permission_codenames=()):
    """Create a user and optionally assign Django model permissions."""
    user = User.objects.create_user(username=username, password="pw")
    for codename in permission_codenames:
        perm = Permission.objects.get(codename=codename)
        user.user_permissions.add(perm)
    return user


def get_view(action_method_map, pk=None):
    """Return a bound view callable for the given HTTP-method → action map."""
    view = PermissionViewSet.as_view(action_method_map)

    def dispatch(request):
        return view(request, pk=pk) if pk is not None else view(request)

    return dispatch


# ---------------------------------------------------------------------------
# 1. LIST  (GET /permissions/)
# ---------------------------------------------------------------------------

class TestListAction(TestCase):

    def test_unauthenticated_is_denied(self):
        request = factory.get("/permissions/")
        response = get_view({"get": "list"})(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_without_view_permission_is_denied(self):
        user = make_user("no_perms")
        request = factory.get("/permissions/")
        force_authenticate(request, user=user)
        response = get_view({"get": "list"})(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_with_view_permission_succeeds(self):
        user = make_user("viewer", permission_codenames=["view_permission"])
        request = factory.get("/permissions/")
        force_authenticate(request, user=user)
        response = get_view({"get": "list"})(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_response_is_a_list(self):
        user = make_user("viewer2", permission_codenames=["view_permission"])
        request = factory.get("/permissions/")
        force_authenticate(request, user=user)
        response = get_view({"get": "list"})(request)
        response.render()
        self.assertIsInstance(response.data, list)

    def test_user_with_only_add_permission_is_denied(self):
        user = make_user("adder", permission_codenames=["add_permission"])
        request = factory.get("/permissions/")
        force_authenticate(request, user=user)
        response = get_view({"get": "list"})(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_with_only_change_permission_is_denied(self):
        user = make_user("changer", permission_codenames=["change_permission"])
        request = factory.get("/permissions/")
        force_authenticate(request, user=user)
        response = get_view({"get": "list"})(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_with_only_delete_permission_is_denied(self):
        user = make_user("deleter", permission_codenames=["delete_permission"])
        request = factory.get("/permissions/")
        force_authenticate(request, user=user)
        response = get_view({"get": "list"})(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


# ---------------------------------------------------------------------------
# 2. RETRIEVE  (GET /permissions/<pk>/)
# ---------------------------------------------------------------------------

class TestRetrieveAction(TestCase):

    def setUp(self):
        ct = ContentType.objects.get_for_model(Permission)
        self.permission_instance = Permission.objects.filter(content_type=ct).first()

    def test_unauthenticated_is_denied(self):
        request = factory.get(f"/permissions/{self.permission_instance.pk}/")
        response = get_view({"get": "retrieve"}, pk=self.permission_instance.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_without_view_permission_is_denied(self):
        user = make_user("no_perms_r")
        request = factory.get(f"/permissions/{self.permission_instance.pk}/")
        force_authenticate(request, user=user)
        response = get_view({"get": "retrieve"}, pk=self.permission_instance.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_with_view_permission_succeeds(self):
        user = make_user("viewer_r", permission_codenames=["view_permission"])
        request = factory.get(f"/permissions/{self.permission_instance.pk}/")
        force_authenticate(request, user=user)
        response = get_view({"get": "retrieve"}, pk=self.permission_instance.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_response_contains_expected_fields(self):
        user = make_user("viewer_r2", permission_codenames=["view_permission"])
        request = factory.get(f"/permissions/{self.permission_instance.pk}/")
        force_authenticate(request, user=user)
        response = get_view({"get": "retrieve"}, pk=self.permission_instance.pk)(request)
        response.render()
        self.assertIn("id", response.data)
        self.assertIn("name", response.data)
        self.assertIn("permission", response.data)

    def test_retrieve_non_existent_pk_returns_404(self):
        user = make_user("viewer_r3", permission_codenames=["view_permission"])
        request = factory.get("/permissions/999999/")
        force_authenticate(request, user=user)
        response = get_view({"get": "retrieve"}, pk=999999)(request)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_with_only_change_permission_is_denied(self):
        user = make_user("changer_r", permission_codenames=["change_permission"])
        request = factory.get(f"/permissions/{self.permission_instance.pk}/")
        force_authenticate(request, user=user)
        response = get_view({"get": "retrieve"}, pk=self.permission_instance.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


# ---------------------------------------------------------------------------
# 3. CREATE  (POST /permissions/)   — NeverAllow blocks all users
# ---------------------------------------------------------------------------

class TestCreateAction(TestCase):

    payload = {"name": "Can do thing", "codename": "do_thing", "content_type": 1}

    def test_unauthenticated_is_denied(self):
        request = factory.post("/permissions/", self.payload)
        response = get_view({"post": "create"})(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_without_permissions_is_denied(self):
        user = make_user("no_perms_c")
        request = factory.post("/permissions/", self.payload)
        force_authenticate(request, user=user)
        response = get_view({"post": "create"})(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_with_add_permission_is_still_denied(self):
        """NeverAllow is the default; 'create' is not in permission_classes_by_action."""
        user = make_user("adder_c", permission_codenames=["add_permission"])
        request = factory.post("/permissions/", self.payload)
        force_authenticate(request, user=user)
        response = get_view({"post": "create"})(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_superuser_is_still_denied(self):
        user = User.objects.create_superuser(username="super_c", password="pw")
        request = factory.post("/permissions/", self.payload)
        force_authenticate(request, user=user)
        response = get_view({"post": "create"})(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


# ---------------------------------------------------------------------------
# 4. UPDATE  (PUT /permissions/<pk>/)   — NeverAllow blocks all users
# ---------------------------------------------------------------------------

class TestUpdateAction(TestCase):

    def setUp(self):
        ct = ContentType.objects.get_for_model(Permission)
        self.permission_instance = Permission.objects.filter(content_type=ct).first()
        self.payload = {
            "name": "Updated name",
            "codename": self.permission_instance.codename,
            "content_type": ct.pk,
        }
        self.url = f"/permissions/{self.permission_instance.pk}/"

    def test_unauthenticated_is_denied(self):
        request = factory.put(self.url, self.payload)
        response = get_view({"put": "update"}, pk=self.permission_instance.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED )

    def test_authenticated_without_permissions_is_denied(self):
        user = make_user("no_perms_u")
        request = factory.put(self.url, self.payload)
        force_authenticate(request, user=user)
        response = get_view({"put": "update"}, pk=self.permission_instance.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_with_change_permission_is_still_denied(self):
        """NeverAllow default overrides any model-level permission for this action."""
        user = make_user("changer_u", permission_codenames=["change_permission"])
        request = factory.put(self.url, self.payload)
        force_authenticate(request, user=user)
        response = get_view({"put": "update"}, pk=self.permission_instance.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_superuser_is_still_denied(self):
        user = User.objects.create_superuser(username="super_u", password="pw")
        request = factory.put(self.url, self.payload)
        force_authenticate(request, user=user)
        response = get_view({"put": "update"}, pk=self.permission_instance.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


# ---------------------------------------------------------------------------
# 5. PARTIAL UPDATE  (PATCH /permissions/<pk>/)   — NeverAllow blocks all users
# ---------------------------------------------------------------------------

class TestPartialUpdateAction(TestCase):

    def setUp(self):
        ct = ContentType.objects.get_for_model(Permission)
        self.permission_instance = Permission.objects.filter(content_type=ct).first()
        self.url = f"/permissions/{self.permission_instance.pk}/"

    def test_unauthenticated_is_denied(self):
        request = factory.patch(self.url, {"name": "Patched"})
        response = get_view({"patch": "partial_update"}, pk=self.permission_instance.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_without_permissions_is_denied(self):
        user = make_user("no_perms_p")
        request = factory.patch(self.url, {"name": "Patched"})
        force_authenticate(request, user=user)
        response = get_view({"patch": "partial_update"}, pk=self.permission_instance.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_with_change_permission_is_still_denied(self):
        user = make_user("changer_p", permission_codenames=["change_permission"])
        request = factory.patch(self.url, {"name": "Patched"})
        force_authenticate(request, user=user)
        response = get_view({"patch": "partial_update"}, pk=self.permission_instance.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_superuser_is_still_denied(self):
        user = User.objects.create_superuser(username="super_p", password="pw")
        request = factory.patch(self.url, {"name": "Patched"})
        force_authenticate(request, user=user)
        response = get_view({"patch": "partial_update"}, pk=self.permission_instance.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


# ---------------------------------------------------------------------------
# 6. DESTROY  (DELETE /permissions/<pk>/)   — NeverAllow blocks all users
# ---------------------------------------------------------------------------

class TestDestroyAction(TestCase):

    def setUp(self):
        ct = ContentType.objects.get_for_model(Permission)
        self.permission_instance = Permission.objects.filter(content_type=ct).first()
        self.url = f"/permissions/{self.permission_instance.pk}/"

    def test_unauthenticated_is_denied(self):
        request = factory.delete(self.url)
        response = get_view({"delete": "destroy"}, pk=self.permission_instance.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_without_permissions_is_denied(self):
        user = make_user("no_perms_d")
        request = factory.delete(self.url)
        force_authenticate(request, user=user)
        response = get_view({"delete": "destroy"}, pk=self.permission_instance.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_with_delete_permission_is_still_denied(self):
        """delete_permission would satisfy ModelPermissions — but NeverAllow wins here."""
        user = make_user("deleter_d", permission_codenames=["delete_permission"])
        request = factory.delete(self.url)
        force_authenticate(request, user=user)
        response = get_view({"delete": "destroy"}, pk=self.permission_instance.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_superuser_is_still_denied(self):
        user = User.objects.create_superuser(username="super_d", password="pw")
        request = factory.delete(self.url)
        force_authenticate(request, user=user)
        response = get_view({"delete": "destroy"}, pk=self.permission_instance.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)