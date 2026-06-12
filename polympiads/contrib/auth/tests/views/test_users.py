from django.contrib.auth.models import Group, Permission
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
        self.assertIsInstance(response.data, dict)
        self.assertIsInstance(response.data["results"], list)

    def test_response_items_contain_expected_fields(self):
        user = make_user("viewer_l3", permission_codenames=["view_user"])
        request = factory.get("/users/")
        force_authenticate(request, user=user)
        response = get_view({"get": "list"})(request)
        response.render()
        self.assertTrue(len(response.data) > 0)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["next"], None)
        self.assertEqual(response.data["previous"], None)
        item = response.data["results"][0]
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

# ---------------------------------------------------------------------------
# 7. ME  (GET /users/me/)  —  requires only IsAuthenticated
# ---------------------------------------------------------------------------

class TestMeAction(TestCase):

    def setUp(self):
        self.user = make_user("me_user")

    def test_unauthenticated_returns_401(self):
        request = factory.get("/users/me/")
        response = get_view({"get": "me"})(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_without_model_permissions_succeeds(self):
        """me only requires IsAuthenticated, no model permission needed."""
        user = make_user("me_no_perms")
        request = factory.get("/users/me/")
        force_authenticate(request, user=user)
        response = get_view({"get": "me"})(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_returns_authenticated_user_data(self):
        request = factory.get("/users/me/")
        force_authenticate(request, user=self.user)
        response = get_view({"get": "me"})(request)
        response.render()
        self.assertEqual(response.data["username"], self.user.username)

    def test_does_not_return_another_users_data(self):
        other = make_user("other_me_user")
        request = factory.get("/users/me/")
        force_authenticate(request, user=self.user)
        response = get_view({"get": "me"})(request)
        response.render()
        self.assertNotEqual(response.data["username"], other.username)

    def test_response_contains_expected_fields(self):
        request = factory.get("/users/me/")
        force_authenticate(request, user=self.user)
        response = get_view({"get": "me"})(request)
        response.render()
        for field in USER_LIST_FIELDS:
            self.assertIn(field, response.data, msg=f"Missing field '{field}' in me response")

    def test_password_not_exposed(self):
        request = factory.get("/users/me/")
        force_authenticate(request, user=self.user)
        response = get_view({"get": "me"})(request)
        response.render()
        self.assertNotIn("password", response.data)

    def test_superuser_can_access_me(self):
        superuser = User.objects.create_superuser(username="super_me", password="pw")
        request = factory.get("/users/me/")
        force_authenticate(request, user=superuser)
        response = get_view({"get": "me"})(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response.render()
        self.assertEqual(response.data["username"], "super_me")

    def test_me_returns_own_id(self):
        request = factory.get("/users/me/")
        force_authenticate(request, user=self.user)
        response = get_view({"get": "me"})(request)
        response.render()
        self.assertEqual(response.data["id"], self.user.pk)

    def test_me_is_not_a_list(self):
        request = factory.get("/users/me/")
        force_authenticate(request, user=self.user)
        response = get_view({"get": "me"})(request)
        response.render()
        self.assertIsInstance(response.data, dict)

    def test_view_permission_not_required(self):
        """Explicitly confirm view_user permission is not needed for me."""
        user = make_user("me_view_perm", permission_codenames=["view_user"])
        user.user_permissions.clear()
        request = factory.get("/users/me/")
        force_authenticate(request, user=user)
        response = get_view({"get": "me"})(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

# ---------------------------------------------------------------------------
# 8. FILTERING, SEARCHING & ORDERING  (GET /users/)
# ---------------------------------------------------------------------------

class TestFilteringSearchingOrdering(TestCase):

    def setUp(self):
        self.viewer = make_user("viewer_f", permission_codenames=["view_user"])

        self.alice = make_user("alice")
        self.alice.first_name = "Alice"
        self.alice.last_name  = "Smith"
        self.alice.email      = "alice@example.com"
        self.alice.is_active  = True
        self.alice.is_staff   = False
        self.alice.save()

        self.bob = make_user("bob")
        self.bob.first_name = "Bob"
        self.bob.last_name  = "Jones"
        self.bob.email      = "bob@example.com"
        self.bob.is_active  = True
        self.bob.is_staff   = True
        self.bob.save()

        self.inactive = make_user("inactive_user")
        self.inactive.is_active = False
        self.inactive.save()

    def _list(self, query_params=None):
        request = factory.get("/users/", query_params or {})
        force_authenticate(request, user=self.viewer)
        response = get_view({"get": "list"})(request)
        response.render()
        return response

    def _usernames(self, response):
        return [u["username"] for u in response.data["results"]]

    # ------------------------------------------------------------------ #
    # Pagination structure                                                 #
    # ------------------------------------------------------------------ #

    def test_response_has_pagination_envelope(self):
        response = self._list()
        for key in ("count", "next", "previous", "results"):
            self.assertIn(key, response.data)

    def test_count_reflects_total_not_page_size(self):
        response = self._list({"page_size": 1})
        # 4 users total: viewer_f, alice, bob, inactive_user
        self.assertEqual(response.data["count"], 4)
        self.assertEqual(len(response.data["results"]), 1)

    def test_next_is_present_when_results_exceed_page_size(self):
        response = self._list({"page_size": 1})
        self.assertIsNotNone(response.data["next"])

    def test_previous_is_none_on_first_page(self):
        response = self._list({"page_size": 1})
        self.assertIsNone(response.data["previous"])

    def test_page_2_returns_different_results(self):
        page1 = self._usernames(self._list({"page_size": 2, "page": 1}))
        page2 = self._usernames(self._list({"page_size": 2, "page": 2}))
        self.assertEqual(len(set(page1) & set(page2)), 0)

    # ------------------------------------------------------------------ #
    # Filtering — username                                                 #
    # ------------------------------------------------------------------ #

    def test_filter_username_icontains_matches(self):
        response = self._list({"username": "ali"})
        usernames = self._usernames(response)
        self.assertIn("alice", usernames)
        self.assertNotIn("bob", usernames)

    def test_filter_username_case_insensitive(self):
        response = self._list({"username": "ALI"})
        self.assertIn("alice", self._usernames(response))

    def test_filter_username_no_match_returns_empty(self):
        response = self._list({"username": "zzznomatch"})
        self.assertEqual(response.data["count"], 0)
        self.assertEqual(response.data["results"], [])

    # ------------------------------------------------------------------ #
    # Filtering — email                                                    #
    # ------------------------------------------------------------------ #

    def test_filter_email_icontains_matches(self):
        response = self._list({"email": "alice@"})
        self.assertIn("alice", self._usernames(response))
        self.assertNotIn("bob", self._usernames(response))

    # ------------------------------------------------------------------ #
    # Filtering — first_name / last_name                                  #
    # ------------------------------------------------------------------ #

    def test_filter_first_name_icontains(self):
        response = self._list({"first_name": "bob"})
        self.assertIn("bob", self._usernames(response))
        self.assertNotIn("alice", self._usernames(response))

    def test_filter_last_name_icontains(self):
        response = self._list({"last_name": "smith"})
        self.assertIn("alice", self._usernames(response))
        self.assertNotIn("bob", self._usernames(response))

    # ------------------------------------------------------------------ #
    # Filtering — boolean fields                                           #
    # ------------------------------------------------------------------ #

    def test_filter_is_active_false(self):
        response = self._list({"is_active": "false"})
        usernames = self._usernames(response)
        self.assertIn("inactive_user", usernames)
        self.assertNotIn("alice", usernames)
        self.assertNotIn("bob", usernames)

    def test_filter_is_active_true(self):
        response = self._list({"is_active": "true"})
        usernames = self._usernames(response)
        self.assertNotIn("inactive_user", usernames)

    def test_filter_is_staff_true(self):
        response = self._list({"is_staff": "true"})
        usernames = self._usernames(response)
        self.assertIn("bob", usernames)
        self.assertNotIn("alice", usernames)

    def test_filter_is_staff_false(self):
        response = self._list({"is_staff": "false"})
        self.assertNotIn("bob", self._usernames(response))

    def test_filter_is_superuser_false(self):
        response = self._list({"is_superuser": "false"})
        usernames = self._usernames(response)
        self.assertIn("alice", usernames)
        self.assertIn("bob", usernames)

    # ------------------------------------------------------------------ #
    # Filtering — combined                                                 #
    # ------------------------------------------------------------------ #

    def test_filter_combined_is_active_and_is_staff(self):
        response = self._list({"is_active": "true", "is_staff": "true"})
        usernames = self._usernames(response)
        self.assertIn("bob", usernames)
        self.assertNotIn("alice", usernames)
        self.assertNotIn("inactive_user", usernames)

    def test_filter_combined_no_match_returns_empty(self):
        response = self._list({"is_active": "false", "is_staff": "true"})
        self.assertEqual(response.data["count"], 0)

    # ------------------------------------------------------------------ #
    # Search                                                               #
    # ------------------------------------------------------------------ #

    def test_search_matches_username(self):
        response = self._list({"search": "alice"})
        self.assertIn("alice", self._usernames(response))
        self.assertNotIn("bob", self._usernames(response))

    def test_search_matches_email(self):
        response = self._list({"search": "bob@example"})
        self.assertIn("bob", self._usernames(response))
        self.assertNotIn("alice", self._usernames(response))

    def test_search_matches_first_name(self):
        response = self._list({"search": "Alice"})
        self.assertIn("alice", self._usernames(response))

    def test_search_matches_last_name(self):
        response = self._list({"search": "Jones"})
        self.assertIn("bob", self._usernames(response))
        self.assertNotIn("alice", self._usernames(response))

    def test_search_is_case_insensitive(self):
        response = self._list({"search": "ALICE"})
        self.assertIn("alice", self._usernames(response))

    def test_search_no_match_returns_empty(self):
        response = self._list({"search": "zzznomatch"})
        self.assertEqual(response.data["count"], 0)

    def test_search_count_reflects_matches(self):
        response = self._list({"search": "alice"})
        self.assertEqual(response.data["count"], 1)

    # ------------------------------------------------------------------ #
    # Ordering                                                             #
    # ------------------------------------------------------------------ #

    def test_default_ordering_is_by_pk(self):
        response = self._list()
        ids = [u["id"] for u in response.data["results"]]
        self.assertEqual(ids, sorted(ids, reverse=True))

    def test_ordering_username_ascending(self):
        response = self._list({"ordering": "username"})
        usernames = self._usernames(response)
        self.assertEqual(usernames, sorted(usernames))

    def test_ordering_username_descending(self):
        response = self._list({"ordering": "-username"})
        usernames = self._usernames(response)
        self.assertEqual(usernames, sorted(usernames, reverse=True))

    def test_ordering_email_ascending(self):
        response = self._list({"ordering": "email"})
        emails = [u["email"] for u in response.data["results"]]
        self.assertEqual(emails, sorted(emails))

    def test_ordering_date_joined_descending(self):
        response = self._list({"ordering": "-date_joined"})
        dates = [u["date_joined"] for u in response.data["results"]]
        self.assertEqual(dates, sorted(dates, reverse=True))

    def test_ordering_is_active_ascending(self):
        response = self._list({"ordering": "is_active"})
        flags = [u["is_active"] for u in response.data["results"]]
        self.assertEqual(flags, sorted(flags))

    def test_ordering_non_whitelisted_field_is_ignored(self):
        """Ordering by a non-whitelisted field must not raise an error."""
        response = self._list({"ordering": "password"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_ordering_unknown_field_falls_back_to_default(self):
        default   = self._usernames(self._list())
        with_junk = self._usernames(self._list({"ordering": "nonexistent_field"}))
        self.assertEqual(default, with_junk)

    # ------------------------------------------------------------------ #
    # Combined filter + search + ordering + pagination                     #
    # ------------------------------------------------------------------ #

    def test_filter_and_search_combined(self):
        response = self._list({"is_active": "true", "search": "alice"})
        usernames = self._usernames(response)
        self.assertIn("alice", usernames)
        self.assertNotIn("bob", usernames)
        self.assertNotIn("inactive_user", usernames)

    def test_filter_search_ordering_pagination_combined(self):
        response = self._list({
            "is_active": "true",
            "search":    "example.com",
            "ordering":  "username",
            "page":      1,
            "page_size": 1,
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data["count"], 1)
        results = response.data["results"]
        self.assertEqual(len(results), 1)
# ---------------------------------------------------------------------------
# 9. PERMISSIONS  (PATCH /users/<pk>/permissions/)  —  requires change_user
# ---------------------------------------------------------------------------

class TestPermissionsAction(TestCase):

    def setUp(self):
        self.target = make_user("permissions_target")
        self.url = f"/users/{self.target.pk}/permissions/"

        self.content_type = ContentType.objects.get_for_model(User)
        app_label = self.content_type.app_label

        self.view_perm   = f"{app_label}.view_user"
        self.add_perm    = f"{app_label}.add_user"
        self.change_perm = f"{app_label}.change_user"

    def _permission(self, codename):
        return Permission.objects.get(codename=codename, content_type=self.content_type)

    def test_unauthenticated_returns_401(self):
        request = factory.patch(self.url, {"add_permissions": [self.view_perm]}, format="json")
        response = get_view({"patch": "permissions"}, pk=self.target.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_without_permissions_is_denied(self):
        user = make_user("no_perms_perm")
        request = factory.patch(self.url, {"add_permissions": [self.view_perm]}, format="json")
        force_authenticate(request, user=user)
        response = get_view({"patch": "permissions"}, pk=self.target.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_with_only_view_permission_is_denied(self):
        user = make_user("viewer_perm", permission_codenames=["view_user"])
        request = factory.patch(self.url, {"add_permissions": [self.view_perm]}, format="json")
        force_authenticate(request, user=user)
        response = get_view({"patch": "permissions"}, pk=self.target.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_with_change_permission_succeeds(self):
        user = make_user("changer_perm", permission_codenames=["change_user"])
        request = factory.patch(self.url, {"add_permissions": [self.view_perm]}, format="json")
        force_authenticate(request, user=user)
        response = get_view({"patch": "permissions"}, pk=self.target.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_add_permissions_persists_to_database(self):
        user = make_user("changer_perm2", permission_codenames=["change_user"])
        request = factory.patch(self.url, {"add_permissions": [self.view_perm, self.add_perm]}, format="json")
        force_authenticate(request, user=user)
        get_view({"patch": "permissions"}, pk=self.target.pk)(request)
        self.target.refresh_from_db()
        codenames = set(self.target.user_permissions.values_list("codename", flat=True))
        self.assertIn("view_user", codenames)
        self.assertIn("add_user", codenames)

    def test_remove_permissions_persists_to_database(self):
        self.target.user_permissions.add(self._permission("view_user"))
        user = make_user("changer_perm3", permission_codenames=["change_user"])
        request = factory.patch(self.url, {"remove_permissions": [self.view_perm]}, format="json")
        force_authenticate(request, user=user)
        get_view({"patch": "permissions"}, pk=self.target.pk)(request)
        self.target.refresh_from_db()
        codenames = set(self.target.user_permissions.values_list("codename", flat=True))
        self.assertNotIn("view_user", codenames)

    def test_add_and_remove_combined(self):
        self.target.user_permissions.add(self._permission("view_user"))
        user = make_user("changer_perm4", permission_codenames=["change_user"])
        request = factory.patch(self.url, {
            "add_permissions": [self.add_perm],
            "remove_permissions": [self.view_perm],
        }, format="json")
        force_authenticate(request, user=user)
        response = get_view({"patch": "permissions"}, pk=self.target.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.target.refresh_from_db()
        codenames = set(self.target.user_permissions.values_list("codename", flat=True))
        self.assertIn("add_user", codenames)
        self.assertNotIn("view_user", codenames)

    def test_response_contains_expected_fields(self):
        user = make_user("changer_perm5", permission_codenames=["change_user"])
        request = factory.patch(self.url, {"add_permissions": [self.view_perm]}, format="json")
        force_authenticate(request, user=user)
        response = get_view({"patch": "permissions"}, pk=self.target.pk)(request)
        response.render()
        for field in USER_LIST_FIELDS:
            self.assertIn(field, response.data, msg=f"Missing field '{field}' in permissions response")
    
    def test_response_reflects_updated_permissions(self):
        user = make_user("changer_perm6", permission_codenames=["change_user"])
        request = factory.patch(self.url, {"add_permissions": [self.view_perm, self.add_perm]}, format="json")
        force_authenticate(request, user=user)
        response = get_view({"patch": "permissions"}, pk=self.target.pk)(request)
        response.render()

        permission_codes = [p["permission"] for p in response.data["permissions"]]
        self.assertIn(self.view_perm, permission_codes)
        self.assertIn(self.add_perm, permission_codes)

    def test_password_not_exposed_in_response(self):
        user = make_user("changer_perm7", permission_codenames=["change_user"])
        request = factory.patch(self.url, {"add_permissions": [self.view_perm]}, format="json")
        force_authenticate(request, user=user)
        response = get_view({"patch": "permissions"}, pk=self.target.pk)(request)
        response.render()
        self.assertNotIn("password", response.data)

    def test_empty_payload_returns_400(self):
        user = make_user("changer_perm8", permission_codenames=["change_user"])
        request = factory.patch(self.url, {}, format="json")
        force_authenticate(request, user=user)
        response = get_view({"patch": "permissions"}, pk=self.target.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_overlapping_add_and_remove_returns_400(self):
        user = make_user("changer_perm9", permission_codenames=["change_user"])
        request = factory.patch(self.url, {
            "add_permissions": [self.view_perm],
            "remove_permissions": [self.view_perm],
        }, format="json")
        force_authenticate(request, user=user)
        response = get_view({"patch": "permissions"}, pk=self.target.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_permission_format_returns_400(self):
        user = make_user("changer_perm10", permission_codenames=["change_user"])
        request = factory.patch(self.url, {"add_permissions": ["not_a_valid_format"]}, format="json")
        force_authenticate(request, user=user)
        response = get_view({"patch": "permissions"}, pk=self.target.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_nonexistent_permission_returns_400(self):
        user = make_user("changer_perm11", permission_codenames=["change_user"])
        app_label = self.content_type.app_label
        request = factory.patch(self.url, {"add_permissions": [f"{app_label}.does_not_exist_perm"]}, format="json")
        force_authenticate(request, user=user)
        response = get_view({"patch": "permissions"}, pk=self.target.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_permissions_on_non_existent_pk_returns_404(self):
        user = make_user("changer_perm12", permission_codenames=["change_user"])
        request = factory.patch("/users/999999/permissions/", {"add_permissions": [self.view_perm]}, format="json")
        force_authenticate(request, user=user)
        response = get_view({"patch": "permissions"}, pk=999999)(request)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

# ---------------------------------------------------------------------------
# 10. GROUPS  (PATCH /users/<pk>/groups/)  —  requires change_user
# ---------------------------------------------------------------------------

class TestGroupsAction(TestCase):

    def setUp(self):
        self.target = make_user("groups_target")
        self.url = f"/users/{self.target.pk}/groups/"

        self.admins  = Group.objects.create(name="Admins")
        self.editors = Group.objects.create(name="Editors")
        self.viewers = Group.objects.create(name="Viewers")

    def test_unauthenticated_returns_401(self):
        request = factory.patch(self.url, {"add_groups": ["Admins"]}, format="json")
        response = get_view({"patch": "groups"}, pk=self.target.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_without_permissions_is_denied(self):
        user = make_user("no_perms_groups")
        request = factory.patch(self.url, {"add_groups": ["Admins"]}, format="json")
        force_authenticate(request, user=user)
        response = get_view({"patch": "groups"}, pk=self.target.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_with_only_view_permission_is_denied(self):
        user = make_user("viewer_groups", permission_codenames=["view_user"])
        request = factory.patch(self.url, {"add_groups": ["Admins"]}, format="json")
        force_authenticate(request, user=user)
        response = get_view({"patch": "groups"}, pk=self.target.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_with_change_permission_succeeds(self):
        user = make_user("changer_groups", permission_codenames=["change_user"])
        request = factory.patch(self.url, {"add_groups": ["Admins"]}, format="json")
        force_authenticate(request, user=user)
        response = get_view({"patch": "groups"}, pk=self.target.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_add_groups_persists_to_database(self):
        user = make_user("changer_groups2", permission_codenames=["change_user"])
        request = factory.patch(self.url, {"add_groups": ["Admins", "Editors"]}, format="json")
        force_authenticate(request, user=user)
        get_view({"patch": "groups"}, pk=self.target.pk)(request)
        self.target.refresh_from_db()
        names = set(self.target.groups.values_list("name", flat=True))
        self.assertIn("Admins", names)
        self.assertIn("Editors", names)

    def test_remove_groups_persists_to_database(self):
        self.target.groups.add(self.admins)
        user = make_user("changer_groups3", permission_codenames=["change_user"])
        request = factory.patch(self.url, {"remove_groups": ["Admins"]}, format="json")
        force_authenticate(request, user=user)
        get_view({"patch": "groups"}, pk=self.target.pk)(request)
        self.target.refresh_from_db()
        names = set(self.target.groups.values_list("name", flat=True))
        self.assertNotIn("Admins", names)

    def test_add_and_remove_combined(self):
        self.target.groups.add(self.admins)
        user = make_user("changer_groups4", permission_codenames=["change_user"])
        request = factory.patch(self.url, {
            "add_groups": ["Editors"],
            "remove_groups": ["Admins"],
        }, format="json")
        force_authenticate(request, user=user)
        response = get_view({"patch": "groups"}, pk=self.target.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.target.refresh_from_db()
        names = set(self.target.groups.values_list("name", flat=True))
        self.assertIn("Editors", names)
        self.assertNotIn("Admins", names)

    def test_response_contains_expected_fields(self):
        user = make_user("changer_groups5", permission_codenames=["change_user"])
        request = factory.patch(self.url, {"add_groups": ["Admins"]}, format="json")
        force_authenticate(request, user=user)
        response = get_view({"patch": "groups"}, pk=self.target.pk)(request)
        response.render()
        for field in USER_LIST_FIELDS:
            self.assertIn(field, response.data, msg=f"Missing field '{field}' in groups response")

    def test_response_reflects_updated_groups(self):
        user = make_user("changer_groups6", permission_codenames=["change_user"])
        request = factory.patch(self.url, {"add_groups": ["Admins", "Editors"]}, format="json")
        force_authenticate(request, user=user)
        response = get_view({"patch": "groups"}, pk=self.target.pk)(request)
        response.render()
        group_names = [g["name"] for g in response.data["groups"]]
        self.assertIn("Admins", group_names)
        self.assertIn("Editors", group_names)

    def test_password_not_exposed_in_response(self):
        user = make_user("changer_groups7", permission_codenames=["change_user"])
        request = factory.patch(self.url, {"add_groups": ["Admins"]}, format="json")
        force_authenticate(request, user=user)
        response = get_view({"patch": "groups"}, pk=self.target.pk)(request)
        response.render()
        self.assertNotIn("password", response.data)

    def test_empty_payload_returns_400(self):
        user = make_user("changer_groups8", permission_codenames=["change_user"])
        request = factory.patch(self.url, {}, format="json")
        force_authenticate(request, user=user)
        response = get_view({"patch": "groups"}, pk=self.target.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_overlapping_add_and_remove_returns_400(self):
        user = make_user("changer_groups9", permission_codenames=["change_user"])
        request = factory.patch(self.url, {
            "add_groups": ["Admins"],
            "remove_groups": ["Admins"],
        }, format="json")
        force_authenticate(request, user=user)
        response = get_view({"patch": "groups"}, pk=self.target.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_nonexistent_group_returns_400(self):
        user = make_user("changer_groups10", permission_codenames=["change_user"])
        request = factory.patch(self.url, {"add_groups": ["NonExistentGroup"]}, format="json")
        force_authenticate(request, user=user)
        response = get_view({"patch": "groups"}, pk=self.target.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_groups_on_non_existent_pk_returns_404(self):
        user = make_user("changer_groups11", permission_codenames=["change_user"])
        request = factory.patch("/users/999999/groups/", {"add_groups": ["Admins"]}, format="json")
        force_authenticate(request, user=user)
        response = get_view({"patch": "groups"}, pk=999999)(request)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
