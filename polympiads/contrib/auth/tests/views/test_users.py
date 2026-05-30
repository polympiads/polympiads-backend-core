from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from polympiads.contrib.auth.models import User
from polympiads.contrib.auth.views.users import UserViewSet

# from polympiads.contrib.auth.views import UserViewSet

factory = APIRequestFactory()

USER_LIST_FIELDS = (
    "id", "username", "first_name", "last_name", "email",
    "is_active", "is_staff", "is_superuser",
    "groups", "permissions", "last_login", "date_joined",
)


def make_user(username, permission_codenames=()):
    """Create a plain user and optionally assign User model permissions."""
    user = User.objects.create_user(username=username, password="pw")
    ct = ContentType.objects.get_for_model(User)
    for codename in permission_codenames:
        perm = Permission.objects.get(codename=codename, content_type=ct)
        user.user_permissions.add(perm)
    return user


def get_view(action_method_map, pk=None):
    view = UserViewSet.as_view(action_method_map)

    def dispatch(request):
        return view(request, pk=pk) if pk is not None else view(request)

    return dispatch


# ---------------------------------------------------------------------------
# 1. LIST  (GET /users/)  —  requires view_user
# ---------------------------------------------------------------------------

class TestListAction(TestCase):

    def test_unauthenticated_returns_401(self):
        request = factory.get("/users/")
        response = get_view({"get": "list"})(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_without_permissions_is_denied(self):
        user = make_user("no_perms_l")
        request = factory.get("/users/")
        force_authenticate(request, user=user)
        response = get_view({"get": "list"})(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_with_view_permission_succeeds(self):
        user = make_user("viewer_l", permission_codenames=["view_user"])
        request = factory.get("/users/")
        force_authenticate(request, user=user)
        response = get_view({"get": "list"})(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_response_is_a_list(self):
        user = make_user("viewer_l2", permission_codenames=["view_user"])
        request = factory.get("/users/")
        force_authenticate(request, user=user)
        response = get_view({"get": "list"})(request)
        response.render()
        self.assertIsInstance(response.data, list)

    def test_response_items_contain_expected_fields(self):
        user = make_user("viewer_l3", permission_codenames=["view_user"])
        request = factory.get("/users/")
        force_authenticate(request, user=user)
        response = get_view({"get": "list"})(request)
        response.render()
        self.assertTrue(len(response.data) > 0)
        item = response.data[0]
        for field in USER_LIST_FIELDS:
            self.assertIn(field, item, msg=f"Missing field '{field}' in list response")

    def test_password_not_exposed_in_list(self):
        user = make_user("viewer_l4", permission_codenames=["view_user"])
        request = factory.get("/users/")
        force_authenticate(request, user=user)
        response = get_view({"get": "list"})(request)
        response.render()
        for item in response.data:
            self.assertNotIn("password", item)

    def test_authenticated_with_only_add_permission_is_denied(self):
        user = make_user("adder_l", permission_codenames=["add_user"])
        request = factory.get("/users/")
        force_authenticate(request, user=user)
        response = get_view({"get": "list"})(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_with_only_change_permission_is_denied(self):
        user = make_user("changer_l", permission_codenames=["change_user"])
        request = factory.get("/users/")
        force_authenticate(request, user=user)
        response = get_view({"get": "list"})(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_with_only_delete_permission_is_denied(self):
        user = make_user("deleter_l", permission_codenames=["delete_user"])
        request = factory.get("/users/")
        force_authenticate(request, user=user)
        response = get_view({"get": "list"})(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


# ---------------------------------------------------------------------------
# 2. RETRIEVE  (GET /users/<pk>/)  —  requires view_user
# ---------------------------------------------------------------------------

class TestRetrieveAction(TestCase):

    def setUp(self):
        self.target = make_user("retrieve_target")

    def test_unauthenticated_returns_401(self):
        request = factory.get(f"/users/{self.target.pk}/")
        response = get_view({"get": "retrieve"}, pk=self.target.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_without_permissions_is_denied(self):
        user = make_user("no_perms_r")
        request = factory.get(f"/users/{self.target.pk}/")
        force_authenticate(request, user=user)
        response = get_view({"get": "retrieve"}, pk=self.target.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_with_view_permission_succeeds(self):
        user = make_user("viewer_r", permission_codenames=["view_user"])
        request = factory.get(f"/users/{self.target.pk}/")
        force_authenticate(request, user=user)
        response = get_view({"get": "retrieve"}, pk=self.target.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_response_contains_expected_fields(self):
        user = make_user("viewer_r2", permission_codenames=["view_user"])
        request = factory.get(f"/users/{self.target.pk}/")
        force_authenticate(request, user=user)
        response = get_view({"get": "retrieve"}, pk=self.target.pk)(request)
        response.render()
        for field in USER_LIST_FIELDS:
            self.assertIn(field, response.data, msg=f"Missing field '{field}' in detail response")

    def test_password_not_exposed_in_retrieve(self):
        user = make_user("viewer_r3", permission_codenames=["view_user"])
        request = factory.get(f"/users/{self.target.pk}/")
        force_authenticate(request, user=user)
        response = get_view({"get": "retrieve"}, pk=self.target.pk)(request)
        response.render()
        self.assertNotIn("password", response.data)

    def test_retrieve_non_existent_pk_returns_404(self):
        user = make_user("viewer_r4", permission_codenames=["view_user"])
        request = factory.get("/users/999999/")
        force_authenticate(request, user=user)
        response = get_view({"get": "retrieve"}, pk=999999)(request)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_authenticated_with_only_change_permission_is_denied(self):
        user = make_user("changer_r", permission_codenames=["change_user"])
        request = factory.get(f"/users/{self.target.pk}/")
        force_authenticate(request, user=user)
        response = get_view({"get": "retrieve"}, pk=self.target.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


# ---------------------------------------------------------------------------
# 3. CREATE  (POST /users/)  —  requires add_user
# ---------------------------------------------------------------------------

class TestCreateAction(TestCase):

    base_payload = {
        "username": "created_user",
        "first_name": "Created",
        "last_name": "User",
        "email": "created@example.com",
        "is_active": True,
        "is_staff": False,
        "is_superuser": False,
    }

    def test_unauthenticated_returns_401(self):
        request = factory.post("/users/", self.base_payload)
        response = get_view({"post": "create"})(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_without_permissions_is_denied(self):
        user = make_user("no_perms_c")
        request = factory.post("/users/", self.base_payload)
        force_authenticate(request, user=user)
        response = get_view({"post": "create"})(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_with_only_view_permission_is_denied(self):
        user = make_user("viewer_c", permission_codenames=["view_user"])
        request = factory.post("/users/", self.base_payload)
        force_authenticate(request, user=user)
        response = get_view({"post": "create"})(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_with_only_change_permission_is_denied(self):
        user = make_user("changer_c", permission_codenames=["change_user"])
        request = factory.post("/users/", self.base_payload)
        force_authenticate(request, user=user)
        response = get_view({"post": "create"})(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_with_add_permission_succeeds(self):
        user = make_user("adder_c", permission_codenames=["add_user"])
        request = factory.post("/users/", self.base_payload)
        force_authenticate(request, user=user)
        response = get_view({"post": "create"})(request)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_persists_to_database(self):
        user = make_user("adder_c2", permission_codenames=["add_user"])
        payload = {**self.base_payload, "username": "persisted_user"}
        request = factory.post("/users/", payload)
        force_authenticate(request, user=user)
        get_view({"post": "create"})(request)
        self.assertTrue(User.objects.filter(username="persisted_user").exists())

    def test_create_without_password_succeeds(self):
        user = make_user("adder_c3", permission_codenames=["add_user"])
        payload = {**self.base_payload, "username": "no_password_user"}
        request = factory.post("/users/", payload)
        force_authenticate(request, user=user)
        response = get_view({"post": "create"})(request)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="no_password_user").exists())

    def test_create_with_password_is_hashed(self):
        user = make_user("adder_c4", permission_codenames=["add_user"])
        payload = {**self.base_payload, "username": "password_user", "password": "Str0ng!Pass"}
        request = factory.post("/users/", payload)
        force_authenticate(request, user=user)
        get_view({"post": "create"})(request)
        created = User.objects.get(username="password_user")
        # Stored value must never be the raw password
        self.assertNotEqual(created.password, "Str0ng!Pass")
        # And the hash must verify correctly
        self.assertTrue(created.check_password("Str0ng!Pass"))

    def test_password_not_exposed_in_create_response(self):
        user = make_user("adder_c5", permission_codenames=["add_user"])
        payload = {**self.base_payload, "username": "exposed_user", "password": "Str0ng!Pass"}
        request = factory.post("/users/", payload)
        force_authenticate(request, user=user)
        response = get_view({"post": "create"})(request)
        response.render()
        self.assertNotIn("password", response.data)

    def test_create_with_duplicate_username_returns_400(self):
        make_user("duplicate_user")
        user = make_user("adder_c6", permission_codenames=["add_user"])
        request = factory.post("/users/", {**self.base_payload, "username": "duplicate_user"})
        force_authenticate(request, user=user)
        response = get_view({"post": "create"})(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_with_too_short_password_returns_400(self):
        """MinimumLengthValidator requires at least 8 characters."""
        user = make_user("adder_c7", permission_codenames=["add_user"])
        payload = {**self.base_payload, "username": "short_pass_user", "password": "abc"}
        request = factory.post("/users/", payload)
        force_authenticate(request, user=user)
        response = get_view({"post": "create"})(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)


# ---------------------------------------------------------------------------
# 4. UPDATE  (PUT /users/<pk>/)  —  requires change_user
# ---------------------------------------------------------------------------

class TestUpdateAction(TestCase):

    def setUp(self):
        self.target = make_user("update_target")
        self.url = f"/users/{self.target.pk}/"
        self.payload = {
            "username": "update_target",
            "first_name": "Updated",
            "last_name": "Name",
            "email": "updated@example.com",
            "is_active": True,
            "is_staff": False,
            "is_superuser": False,
        }

    def test_unauthenticated_returns_401(self):
        request = factory.put(self.url, self.payload)
        response = get_view({"put": "update"}, pk=self.target.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_without_permissions_is_denied(self):
        user = make_user("no_perms_u")
        request = factory.put(self.url, self.payload)
        force_authenticate(request, user=user)
        response = get_view({"put": "update"}, pk=self.target.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_with_only_view_permission_is_denied(self):
        user = make_user("viewer_u", permission_codenames=["view_user"])
        request = factory.put(self.url, self.payload)
        force_authenticate(request, user=user)
        response = get_view({"put": "update"}, pk=self.target.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_with_only_add_permission_is_denied(self):
        user = make_user("adder_u", permission_codenames=["add_user"])
        request = factory.put(self.url, self.payload)
        force_authenticate(request, user=user)
        response = get_view({"put": "update"}, pk=self.target.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_with_change_permission_succeeds(self):
        user = make_user("changer_u", permission_codenames=["change_user"])
        request = factory.put(self.url, self.payload)
        force_authenticate(request, user=user)
        response = get_view({"put": "update"}, pk=self.target.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_persists_to_database(self):
        user = make_user("changer_u2", permission_codenames=["change_user"])
        request = factory.put(self.url, {**self.payload, "first_name": "Persisted"})
        force_authenticate(request, user=user)
        get_view({"put": "update"}, pk=self.target.pk)(request)
        self.target.refresh_from_db()
        self.assertEqual(self.target.first_name, "Persisted")

    def test_update_without_password_leaves_password_unchanged(self):
        user = make_user("changer_u3", permission_codenames=["change_user"])
        original_password = self.target.password
        request = factory.put(self.url, self.payload)
        force_authenticate(request, user=user)
        get_view({"put": "update"}, pk=self.target.pk)(request)
        self.target.refresh_from_db()
        self.assertEqual(self.target.password, original_password)

    def test_update_with_password_is_hashed(self):
        user = make_user("changer_u4", permission_codenames=["change_user"])
        request = factory.put(self.url, {**self.payload, "password": "NewStr0ng!Pass"})
        force_authenticate(request, user=user)
        get_view({"put": "update"}, pk=self.target.pk)(request)
        self.target.refresh_from_db()
        self.assertNotEqual(self.target.password, "NewStr0ng!Pass")
        self.assertTrue(self.target.check_password("NewStr0ng!Pass"))

    def test_update_password_replaces_old_password(self):
        self.target.set_password("OldPass!1")
        self.target.save()
        user = make_user("changer_u5", permission_codenames=["change_user"])
        request = factory.put(self.url, {**self.payload, "password": "NewStr0ng!Pass"})
        force_authenticate(request, user=user)
        get_view({"put": "update"}, pk=self.target.pk)(request)
        self.target.refresh_from_db()
        self.assertFalse(self.target.check_password("OldPass!1"))
        self.assertTrue(self.target.check_password("NewStr0ng!Pass"))

    def test_update_with_too_short_password_returns_400(self):
        """MinimumLengthValidator requires at least 8 characters."""
        user = make_user("changer_u6", permission_codenames=["change_user"])
        request = factory.put(self.url, {**self.payload, "password": "abc"})
        force_authenticate(request, user=user)
        response = get_view({"put": "update"}, pk=self.target.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_password_not_exposed_in_update_response(self):
        user = make_user("changer_u6", permission_codenames=["change_user"])
        request = factory.put(self.url, {**self.payload, "password": "NewStr0ng!Pass"})
        force_authenticate(request, user=user)
        response = get_view({"put": "update"}, pk=self.target.pk)(request)
        response.render()
        self.assertNotIn("password", response.data)


# ---------------------------------------------------------------------------
# 5. PARTIAL UPDATE  (PATCH /users/<pk>/)  —  requires change_user
# ---------------------------------------------------------------------------

class TestPartialUpdateAction(TestCase):

    def setUp(self):
        self.target = make_user("patch_target")
        self.target.set_password("OldPass!1")
        self.target.save()
        self.url = f"/users/{self.target.pk}/"

    def test_unauthenticated_returns_401(self):
        request = factory.patch(self.url, {"first_name": "Patched"})
        response = get_view({"patch": "partial_update"}, pk=self.target.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_without_permissions_is_denied(self):
        user = make_user("no_perms_p")
        request = factory.patch(self.url, {"first_name": "Patched"})
        force_authenticate(request, user=user)
        response = get_view({"patch": "partial_update"}, pk=self.target.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_with_only_view_permission_is_denied(self):
        user = make_user("viewer_p", permission_codenames=["view_user"])
        request = factory.patch(self.url, {"first_name": "Patched"})
        force_authenticate(request, user=user)
        response = get_view({"patch": "partial_update"}, pk=self.target.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_with_only_add_permission_is_denied(self):
        user = make_user("adder_p", permission_codenames=["add_user"])
        request = factory.patch(self.url, {"first_name": "Patched"})
        force_authenticate(request, user=user)
        response = get_view({"patch": "partial_update"}, pk=self.target.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_with_change_permission_succeeds(self):
        user = make_user("changer_p", permission_codenames=["change_user"])
        request = factory.patch(self.url, {"first_name": "Patched"})
        force_authenticate(request, user=user)
        response = get_view({"patch": "partial_update"}, pk=self.target.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_partial_update_persists_to_database(self):
        user = make_user("changer_p2", permission_codenames=["change_user"])
        request = factory.patch(self.url, {"first_name": "Partially Updated"})
        force_authenticate(request, user=user)
        get_view({"patch": "partial_update"}, pk=self.target.pk)(request)
        self.target.refresh_from_db()
        self.assertEqual(self.target.first_name, "Partially Updated")

    def test_partial_update_without_password_leaves_password_unchanged(self):
        user = make_user("changer_p3", permission_codenames=["change_user"])
        original_password = self.target.password
        request = factory.patch(self.url, {"first_name": "Patched"})
        force_authenticate(request, user=user)
        get_view({"patch": "partial_update"}, pk=self.target.pk)(request)
        self.target.refresh_from_db()
        self.assertEqual(self.target.password, original_password)

    def test_partial_update_with_password_is_hashed(self):
        user = make_user("changer_p4", permission_codenames=["change_user"])
        request = factory.patch(self.url, {"password": "NewStr0ng!Pass"})
        force_authenticate(request, user=user)
        get_view({"patch": "partial_update"}, pk=self.target.pk)(request)
        self.target.refresh_from_db()
        self.assertNotEqual(self.target.password, "NewStr0ng!Pass")
        self.assertTrue(self.target.check_password("NewStr0ng!Pass"))

    def test_partial_update_password_replaces_old_password(self):
        user = make_user("changer_p5", permission_codenames=["change_user"])
        request = factory.patch(self.url, {"password": "NewStr0ng!Pass"})
        force_authenticate(request, user=user)
        get_view({"patch": "partial_update"}, pk=self.target.pk)(request)
        self.target.refresh_from_db()
        self.assertFalse(self.target.check_password("OldPass!1"))
        self.assertTrue(self.target.check_password("NewStr0ng!Pass"))

    def test_partial_update_with_too_short_password_returns_400(self):
        """MinimumLengthValidator requires at least 8 characters."""
        user = make_user("changer_p6", permission_codenames=["change_user"])
        request = factory.patch(self.url, {"password": "abc"})
        force_authenticate(request, user=user)
        response = get_view({"patch": "partial_update"}, pk=self.target.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_password_not_exposed_in_partial_update_response(self):
        user = make_user("changer_p6", permission_codenames=["change_user"])
        request = factory.patch(self.url, {"password": "NewStr0ng!Pass"})
        force_authenticate(request, user=user)
        response = get_view({"patch": "partial_update"}, pk=self.target.pk)(request)
        response.render()
        self.assertNotIn("password", response.data)


# ---------------------------------------------------------------------------
# 6. DESTROY  (DELETE /users/<pk>/)  —  requires delete_user
# ---------------------------------------------------------------------------

class TestDestroyAction(TestCase):

    def setUp(self):
        self.target = make_user("delete_target")
        self.url = f"/users/{self.target.pk}/"

    def test_unauthenticated_returns_401(self):
        request = factory.delete(self.url)
        response = get_view({"delete": "destroy"}, pk=self.target.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_without_permissions_is_denied(self):
        user = make_user("no_perms_d")
        request = factory.delete(self.url)
        force_authenticate(request, user=user)
        response = get_view({"delete": "destroy"}, pk=self.target.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_with_only_view_permission_is_denied(self):
        user = make_user("viewer_d", permission_codenames=["view_user"])
        request = factory.delete(self.url)
        force_authenticate(request, user=user)
        response = get_view({"delete": "destroy"}, pk=self.target.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_with_only_change_permission_is_denied(self):
        user = make_user("changer_d", permission_codenames=["change_user"])
        request = factory.delete(self.url)
        force_authenticate(request, user=user)
        response = get_view({"delete": "destroy"}, pk=self.target.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_with_delete_permission_succeeds(self):
        user = make_user("deleter_d", permission_codenames=["delete_user"])
        request = factory.delete(self.url)
        force_authenticate(request, user=user)
        response = get_view({"delete": "destroy"}, pk=self.target.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_removes_from_database(self):
        user = make_user("deleter_d2", permission_codenames=["delete_user"])
        pk = self.target.pk
        request = factory.delete(self.url)
        force_authenticate(request, user=user)
        get_view({"delete": "destroy"}, pk=pk)(request)
        self.assertFalse(User.objects.filter(pk=pk).exists())

    def test_delete_non_existent_pk_returns_404(self):
        user = make_user("deleter_d3", permission_codenames=["delete_user"])
        request = factory.delete("/users/999999/")
        force_authenticate(request, user=user)
        response = get_view({"delete": "destroy"}, pk=999999)(request)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)