from polympiads.contrib.auth.models import User
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from polympiads.contrib.auth.views.groups import GroupViewSet

# from polympiads.contrib.auth.views import GroupViewSet

factory = APIRequestFactory()


def make_user(username, permission_codenames=()):
    """Create a plain user and optionally assign Group model permissions."""
    user = User.objects.create_user(username=username, password="pw")
    ct = ContentType.objects.get_for_model(Group)
    for codename in permission_codenames:
        perm = Permission.objects.get(codename=codename, content_type=ct)
        user.user_permissions.add(perm)
    return user


def get_view(action_method_map, pk=None):
    view = GroupViewSet.as_view(action_method_map)

    def dispatch(request):
        return view(request, pk=pk) if pk is not None else view(request)

    return dispatch


# ---------------------------------------------------------------------------
# 1. LIST  (GET /groups/)  —  requires view_group
# ---------------------------------------------------------------------------

class TestListAction(TestCase):

    def test_unauthenticated_returns_401(self):
        request = factory.get("/groups/")
        response = get_view({"get": "list"})(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_without_permissions_is_denied(self):
        user = make_user("no_perms_l")
        request = factory.get("/groups/")
        force_authenticate(request, user=user)
        response = get_view({"get": "list"})(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_with_view_permission_succeeds(self):
        user = make_user("viewer_l", permission_codenames=["view_group"])
        request = factory.get("/groups/")
        force_authenticate(request, user=user)
        response = get_view({"get": "list"})(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_response_is_a_list(self):
        user = make_user("viewer_l2", permission_codenames=["view_group"])
        request = factory.get("/groups/")
        force_authenticate(request, user=user)
        response = get_view({"get": "list"})(request)
        response.render()
        self.assertIsInstance(response.data, dict)
        self.assertIsInstance(response.data["results"], list)

    def test_response_items_contain_expected_fields(self):
        Group.objects.create(name="Test Group")
        user = make_user("viewer_l3", permission_codenames=["view_group"])
        request = factory.get("/groups/")
        force_authenticate(request, user=user)
        response = get_view({"get": "list"})(request)
        response.render()
        self.assertTrue(len(response.data["results"]) > 0)
        item = response.data["results"][0]
        for field in ("id", "name", "permissions"):
            self.assertIn(field, item)

    def test_authenticated_with_only_add_permission_is_denied(self):
        user = make_user("adder_l", permission_codenames=["add_group"])
        request = factory.get("/groups/")
        force_authenticate(request, user=user)
        response = get_view({"get": "list"})(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_with_only_change_permission_is_denied(self):
        user = make_user("changer_l", permission_codenames=["change_group"])
        request = factory.get("/groups/")
        force_authenticate(request, user=user)
        response = get_view({"get": "list"})(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_with_only_delete_permission_is_denied(self):
        user = make_user("deleter_l", permission_codenames=["delete_group"])
        request = factory.get("/groups/")
        force_authenticate(request, user=user)
        response = get_view({"get": "list"})(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


# ---------------------------------------------------------------------------
# 2. RETRIEVE  (GET /groups/<pk>/)  —  requires view_group
# ---------------------------------------------------------------------------

class TestRetrieveAction(TestCase):

    def setUp(self):
        self.group = Group.objects.create(name="Retrieve Test Group")

    def test_unauthenticated_returns_401(self):
        request = factory.get(f"/groups/{self.group.pk}/")
        response = get_view({"get": "retrieve"}, pk=self.group.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_without_permissions_is_denied(self):
        user = make_user("no_perms_r")
        request = factory.get(f"/groups/{self.group.pk}/")
        force_authenticate(request, user=user)
        response = get_view({"get": "retrieve"}, pk=self.group.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_with_view_permission_succeeds(self):
        user = make_user("viewer_r", permission_codenames=["view_group"])
        request = factory.get(f"/groups/{self.group.pk}/")
        force_authenticate(request, user=user)
        response = get_view({"get": "retrieve"}, pk=self.group.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_response_contains_expected_fields(self):
        user = make_user("viewer_r2", permission_codenames=["view_group"])
        request = factory.get(f"/groups/{self.group.pk}/")
        force_authenticate(request, user=user)
        response = get_view({"get": "retrieve"}, pk=self.group.pk)(request)
        response.render()
        for field in ("id", "name", "permissions"):
            self.assertIn(field, response.data)

    def test_retrieve_non_existent_pk_returns_404(self):
        user = make_user("viewer_r3", permission_codenames=["view_group"])
        request = factory.get("/groups/999999/")
        force_authenticate(request, user=user)
        response = get_view({"get": "retrieve"}, pk=999999)(request)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_authenticated_with_only_change_permission_is_denied(self):
        user = make_user("changer_r", permission_codenames=["change_group"])
        request = factory.get(f"/groups/{self.group.pk}/")
        force_authenticate(request, user=user)
        response = get_view({"get": "retrieve"}, pk=self.group.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


# ---------------------------------------------------------------------------
# 3. CREATE  (POST /groups/)  —  requires add_group
# ---------------------------------------------------------------------------

class TestCreateAction(TestCase):

    payload = {"name": "New Group"}

    def test_unauthenticated_returns_401(self):
        request = factory.post("/groups/", self.payload)
        response = get_view({"post": "create"})(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_without_permissions_is_denied(self):
        user = make_user("no_perms_c")
        request = factory.post("/groups/", self.payload)
        force_authenticate(request, user=user)
        response = get_view({"post": "create"})(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_with_only_view_permission_is_denied(self):
        user = make_user("viewer_c", permission_codenames=["view_group"])
        request = factory.post("/groups/", self.payload)
        force_authenticate(request, user=user)
        response = get_view({"post": "create"})(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_with_only_change_permission_is_denied(self):
        user = make_user("changer_c", permission_codenames=["change_group"])
        request = factory.post("/groups/", self.payload)
        force_authenticate(request, user=user)
        response = get_view({"post": "create"})(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_with_add_permission_succeeds(self):
        user = make_user("adder_c", permission_codenames=["add_group"])
        request = factory.post("/groups/", self.payload)
        force_authenticate(request, user=user)
        response = get_view({"post": "create"})(request)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_persists_to_database(self):
        user = make_user("adder_c2", permission_codenames=["add_group"])
        request = factory.post("/groups/", {"name": "Persisted Group"})
        force_authenticate(request, user=user)
        get_view({"post": "create"})(request)
        self.assertTrue(Group.objects.filter(name="Persisted Group").exists())

    def test_create_with_duplicate_name_returns_400(self):
        Group.objects.create(name="Duplicate Group")
        user = make_user("adder_c3", permission_codenames=["add_group"])
        request = factory.post("/groups/", {"name": "Duplicate Group"})
        force_authenticate(request, user=user)
        response = get_view({"post": "create"})(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ---------------------------------------------------------------------------
# 4. UPDATE  (PUT /groups/<pk>/)  —  requires change_group
# ---------------------------------------------------------------------------

class TestUpdateAction(TestCase):

    def setUp(self):
        self.group = Group.objects.create(name="Update Test Group")
        self.url = f"/groups/{self.group.pk}/"
        self.payload = {"name": "Updated Group"}

    def test_unauthenticated_returns_401(self):
        request = factory.put(self.url, self.payload)
        response = get_view({"put": "update"}, pk=self.group.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_without_permissions_is_denied(self):
        user = make_user("no_perms_u")
        request = factory.put(self.url, self.payload)
        force_authenticate(request, user=user)
        response = get_view({"put": "update"}, pk=self.group.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_with_only_view_permission_is_denied(self):
        user = make_user("viewer_u", permission_codenames=["view_group"])
        request = factory.put(self.url, self.payload)
        force_authenticate(request, user=user)
        response = get_view({"put": "update"}, pk=self.group.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_with_only_add_permission_is_denied(self):
        user = make_user("adder_u", permission_codenames=["add_group"])
        request = factory.put(self.url, self.payload)
        force_authenticate(request, user=user)
        response = get_view({"put": "update"}, pk=self.group.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_with_change_permission_succeeds(self):
        user = make_user("changer_u", permission_codenames=["change_group"])
        request = factory.put(self.url, self.payload)
        force_authenticate(request, user=user)
        response = get_view({"put": "update"}, pk=self.group.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_persists_to_database(self):
        user = make_user("changer_u2", permission_codenames=["change_group"])
        request = factory.put(self.url, {"name": "Renamed Group"})
        force_authenticate(request, user=user)
        get_view({"put": "update"}, pk=self.group.pk)(request)
        self.group.refresh_from_db()
        self.assertEqual(self.group.name, "Renamed Group")


# ---------------------------------------------------------------------------
# 5. PARTIAL UPDATE  (PATCH /groups/<pk>/)  —  requires change_group
# ---------------------------------------------------------------------------

class TestPartialUpdateAction(TestCase):

    def setUp(self):
        self.group = Group.objects.create(name="Patch Test Group")
        self.url = f"/groups/{self.group.pk}/"

    def test_unauthenticated_returns_401(self):
        request = factory.patch(self.url, {"name": "Patched"})
        response = get_view({"patch": "partial_update"}, pk=self.group.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_without_permissions_is_denied(self):
        user = make_user("no_perms_p")
        request = factory.patch(self.url, {"name": "Patched"})
        force_authenticate(request, user=user)
        response = get_view({"patch": "partial_update"}, pk=self.group.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_with_only_view_permission_is_denied(self):
        user = make_user("viewer_p", permission_codenames=["view_group"])
        request = factory.patch(self.url, {"name": "Patched"})
        force_authenticate(request, user=user)
        response = get_view({"patch": "partial_update"}, pk=self.group.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_with_only_add_permission_is_denied(self):
        user = make_user("adder_p", permission_codenames=["add_group"])
        request = factory.patch(self.url, {"name": "Patched"})
        force_authenticate(request, user=user)
        response = get_view({"patch": "partial_update"}, pk=self.group.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_with_change_permission_succeeds(self):
        user = make_user("changer_p", permission_codenames=["change_group"])
        request = factory.patch(self.url, {"name": "Patched"})
        force_authenticate(request, user=user)
        response = get_view({"patch": "partial_update"}, pk=self.group.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_partial_update_persists_to_database(self):
        user = make_user("changer_p2", permission_codenames=["change_group"])
        request = factory.patch(self.url, {"name": "Partially Renamed"})
        force_authenticate(request, user=user)
        get_view({"patch": "partial_update"}, pk=self.group.pk)(request)
        self.group.refresh_from_db()
        self.assertEqual(self.group.name, "Partially Renamed")


# ---------------------------------------------------------------------------
# 6. DESTROY  (DELETE /groups/<pk>/)  —  requires delete_group
# ---------------------------------------------------------------------------

class TestDestroyAction(TestCase):

    def setUp(self):
        self.group = Group.objects.create(name="Delete Test Group")
        self.url = f"/groups/{self.group.pk}/"

    def test_unauthenticated_returns_401(self):
        request = factory.delete(self.url)
        response = get_view({"delete": "destroy"}, pk=self.group.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_without_permissions_is_denied(self):
        user = make_user("no_perms_d")
        request = factory.delete(self.url)
        force_authenticate(request, user=user)
        response = get_view({"delete": "destroy"}, pk=self.group.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_with_only_view_permission_is_denied(self):
        user = make_user("viewer_d", permission_codenames=["view_group"])
        request = factory.delete(self.url)
        force_authenticate(request, user=user)
        response = get_view({"delete": "destroy"}, pk=self.group.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_with_only_change_permission_is_denied(self):
        user = make_user("changer_d", permission_codenames=["change_group"])
        request = factory.delete(self.url)
        force_authenticate(request, user=user)
        response = get_view({"delete": "destroy"}, pk=self.group.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_with_delete_permission_succeeds(self):
        user = make_user("deleter_d", permission_codenames=["delete_group"])
        request = factory.delete(self.url)
        force_authenticate(request, user=user)
        response = get_view({"delete": "destroy"}, pk=self.group.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_removes_from_database(self):
        user = make_user("deleter_d2", permission_codenames=["delete_group"])
        pk = self.group.pk
        request = factory.delete(self.url)
        force_authenticate(request, user=user)
        get_view({"delete": "destroy"}, pk=pk)(request)
        self.assertFalse(Group.objects.filter(pk=pk).exists())

    def test_delete_non_existent_pk_returns_404(self):
        user = make_user("deleter_d3", permission_codenames=["delete_group"])
        request = factory.delete("/groups/999999/")
        force_authenticate(request, user=user)
        response = get_view({"delete": "destroy"}, pk=999999)(request)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

# ---------------------------------------------------------------------------
# 7. FILTERING, SEARCHING & ORDERING  (GET /groups/)
# ---------------------------------------------------------------------------

class TestFilteringSearchingOrdering(TestCase):

    def setUp(self):
        self.viewer = make_user("viewer_f", permission_codenames=["view_group"])

        self.admins      = Group.objects.create(name="Admins")
        self.editors     = Group.objects.create(name="Editors")
        self.viewers     = Group.objects.create(name="Viewers")
        self.superadmins = Group.objects.create(name="Superadmins")

    def _list(self, query_params=None):
        request = factory.get("/groups/", query_params or {})
        force_authenticate(request, user=self.viewer)
        response = get_view({"get": "list"})(request)
        response.render()
        return response

    def _names(self, response):
        return [g["name"] for g in response.data["results"]]

    # ------------------------------------------------------------------ #
    # Pagination structure                                                 #
    # ------------------------------------------------------------------ #

    def test_response_has_pagination_envelope(self):
        response = self._list()
        for key in ("count", "next", "previous", "results"):
            self.assertIn(key, response.data)

    def test_count_reflects_total_not_page_size(self):
        response = self._list({"page_size": 1})
        self.assertEqual(response.data["count"], 4)
        self.assertEqual(len(response.data["results"]), 1)

    def test_next_is_present_when_results_exceed_page_size(self):
        response = self._list({"page_size": 1})
        self.assertIsNotNone(response.data["next"])

    def test_previous_is_none_on_first_page(self):
        response = self._list({"page_size": 1})
        self.assertIsNone(response.data["previous"])

    def test_page_2_returns_different_results(self):
        page1 = self._names(self._list({"page_size": 2, "page": 1}))
        page2 = self._names(self._list({"page_size": 2, "page": 2}))
        self.assertEqual(len(set(page1) & set(page2)), 0)

    # ------------------------------------------------------------------ #
    # Filtering — name                                                     #
    # ------------------------------------------------------------------ #

    def test_filter_name_icontains_matches(self):
        response = self._list({"name": "admin"})
        names = self._names(response)
        self.assertIn("Admins", names)
        self.assertIn("Superadmins", names)
        self.assertNotIn("Editors", names)
        self.assertNotIn("Viewers", names)

    def test_filter_name_case_insensitive(self):
        response = self._list({"name": "ADMIN"})
        names = self._names(response)
        self.assertIn("Admins", names)
        self.assertIn("Superadmins", names)

    def test_filter_name_exact_substring(self):
        response = self._list({"name": "Editors"})
        names = self._names(response)
        self.assertIn("Editors", names)
        self.assertNotIn("Admins", names)

    def test_filter_name_no_match_returns_empty(self):
        response = self._list({"name": "zzznomatch"})
        self.assertEqual(response.data["count"], 0)
        self.assertEqual(response.data["results"], [])

    def test_filter_name_partial_match(self):
        response = self._list({"name": "er"})
        names = self._names(response)
        self.assertIn("Viewers", names)
        self.assertNotIn("Admins", names)

    # ------------------------------------------------------------------ #
    # Search                                                               #
    # ------------------------------------------------------------------ #

    def test_search_matches_name(self):
        response = self._list({"search": "Editors"})
        names = self._names(response)
        self.assertIn("Editors", names)
        self.assertNotIn("Admins", names)

    def test_search_is_case_insensitive(self):
        response = self._list({"search": "editors"})
        self.assertIn("Editors", self._names(response))

    def test_search_partial_match(self):
        response = self._list({"search": "admin"})
        names = self._names(response)
        self.assertIn("Admins", names)
        self.assertIn("Superadmins", names)

    def test_search_no_match_returns_empty(self):
        response = self._list({"search": "zzznomatch"})
        self.assertEqual(response.data["count"], 0)

    def test_search_count_reflects_matches(self):
        response = self._list({"search": "admin"})
        self.assertEqual(response.data["count"], 2)

    # ------------------------------------------------------------------ #
    # Ordering                                                             #
    # ------------------------------------------------------------------ #

    def test_default_ordering_is_by_pk_descending(self):
        response = self._list()
        ids = [g["id"] for g in response.data["results"]]
        self.assertEqual(ids, sorted(ids, reverse=True))

    def test_ordering_name_ascending(self):
        response = self._list({"ordering": "name"})
        names = self._names(response)
        self.assertEqual(names, sorted(names))

    def test_ordering_name_descending(self):
        response = self._list({"ordering": "-name"})
        names = self._names(response)
        self.assertEqual(names, sorted(names, reverse=True))

    def test_ordering_non_whitelisted_field_is_ignored(self):
        response = self._list({"ordering": "permissions"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_ordering_unknown_field_falls_back_to_default(self):
        default   = self._names(self._list())
        with_junk = self._names(self._list({"ordering": "nonexistent_field"}))
        self.assertEqual(default, with_junk)

    # ------------------------------------------------------------------ #
    # Combined filter + search + ordering + pagination                     #
    # ------------------------------------------------------------------ #

    def test_filter_and_search_combined(self):
        response = self._list({"name": "admin", "search": "super"})
        names = self._names(response)
        self.assertIn("Superadmins", names)
        self.assertNotIn("Admins", names)
        self.assertNotIn("Editors", names)

    def test_filter_ordering_pagination_combined(self):
        response = self._list({
            "search":    "admin",
            "ordering":  "name",
            "page":      1,
            "page_size": 1,
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(len(response.data["results"]), 1)
        # With name ascending, "Admins" comes before "Superadmins"
        self.assertEqual(response.data["results"][0]["name"], "Admins")

    def test_filter_ordering_pagination_page2(self):
        response = self._list({
            "search":    "admin",
            "ordering":  "name",
            "page":      2,
            "page_size": 1,
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"][0]["name"], "Superadmins")

# ---------------------------------------------------------------------------
# 8. PERMISSIONS  (PATCH /groups/<pk>/permissions/)  —  requires change_group
# ---------------------------------------------------------------------------

class TestPermissionsAction(TestCase):

    def setUp(self):
        self.group = Group.objects.create(name="Permissions Test Group")
        self.url = f"/groups/{self.group.pk}/permissions/"

        self.content_type = ContentType.objects.get_for_model(Group)
        app_label = self.content_type.app_label

        self.view_permission   = self._permission("view_group")
        self.add_permission    = self._permission("add_group")
        self.change_permission = self._permission("change_group")

        self.view_perm   = self.view_permission.pk
        self.add_perm    = self.add_permission.pk
        self.change_perm = self.change_permission.pk

        # Codename strings, kept for asserting against response payloads
        # (the group-permissions output format is unrelated to this change).
        self.view_perm_code = f"{app_label}.view_group"
        self.add_perm_code  = f"{app_label}.add_group"

    def _permission(self, codename):
        return Permission.objects.get(codename=codename, content_type=self.content_type)

    def test_unauthenticated_returns_401(self):
        request = factory.patch(self.url, {"add_permissions": [self.view_perm]}, format="json")
        response = get_view({"patch": "permissions"}, pk=self.group.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_without_permissions_is_denied(self):
        user = make_user("no_perms_perm")
        request = factory.patch(self.url, {"add_permissions": [self.view_perm]}, format="json")
        force_authenticate(request, user=user)
        response = get_view({"patch": "permissions"}, pk=self.group.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_with_only_view_permission_is_denied(self):
        user = make_user("viewer_perm", permission_codenames=["view_group"])
        request = factory.patch(self.url, {"add_permissions": [self.view_perm]}, format="json")
        force_authenticate(request, user=user)
        response = get_view({"patch": "permissions"}, pk=self.group.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_with_change_permission_succeeds(self):
        user = make_user("changer_perm", permission_codenames=["change_group"])
        request = factory.patch(self.url, {"add_permissions": [self.view_perm]}, format="json")
        force_authenticate(request, user=user)
        response = get_view({"patch": "permissions"}, pk=self.group.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_add_permissions_persists_to_database(self):
        user = make_user("changer_perm2", permission_codenames=["change_group"])
        request = factory.patch(self.url, {"add_permissions": [self.view_perm, self.add_perm]}, format="json")
        force_authenticate(request, user=user)
        get_view({"patch": "permissions"}, pk=self.group.pk)(request)
        self.group.refresh_from_db()
        codenames = set(self.group.permissions.values_list("codename", flat=True))
        self.assertIn("view_group", codenames)
        self.assertIn("add_group", codenames)

    def test_remove_permissions_persists_to_database(self):
        self.group.permissions.add(self.view_permission)
        user = make_user("changer_perm3", permission_codenames=["change_group"])
        request = factory.patch(self.url, {"remove_permissions": [self.view_perm]}, format="json")
        force_authenticate(request, user=user)
        get_view({"patch": "permissions"}, pk=self.group.pk)(request)
        self.group.refresh_from_db()
        codenames = set(self.group.permissions.values_list("codename", flat=True))
        self.assertNotIn("view_group", codenames)

    def test_add_and_remove_combined(self):
        self.group.permissions.add(self.view_permission)
        user = make_user("changer_perm4", permission_codenames=["change_group"])
        request = factory.patch(self.url, {
            "add_permissions": [self.add_perm],
            "remove_permissions": [self.view_perm],
        }, format="json")
        force_authenticate(request, user=user)
        response = get_view({"patch": "permissions"}, pk=self.group.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.group.refresh_from_db()
        codenames = set(self.group.permissions.values_list("codename", flat=True))
        self.assertIn("add_group", codenames)
        self.assertNotIn("view_group", codenames)

    def test_response_contains_expected_fields(self):
        user = make_user("changer_perm5", permission_codenames=["change_group"])
        request = factory.patch(self.url, {"add_permissions": [self.view_perm]}, format="json")
        force_authenticate(request, user=user)
        response = get_view({"patch": "permissions"}, pk=self.group.pk)(request)
        response.render()
        for field in ("id", "name", "permissions"):
            self.assertIn(field, response.data, msg=f"Missing field '{field}' in permissions response")

    def test_response_reflects_updated_permissions(self):
        user = make_user("changer_perm6", permission_codenames=["change_group"])
        request = factory.patch(self.url, {"add_permissions": [self.view_perm, self.add_perm]}, format="json")
        force_authenticate(request, user=user)
        response = get_view({"patch": "permissions"}, pk=self.group.pk)(request)
        response.render()
        permission_codes = [p["permission"] for p in response.data["permissions"]]
        self.assertIn(self.view_perm_code, permission_codes)
        self.assertIn(self.add_perm_code, permission_codes)

    def test_empty_payload_returns_400(self):
        user = make_user("changer_perm7", permission_codenames=["change_group"])
        request = factory.patch(self.url, {}, format="json")
        force_authenticate(request, user=user)
        response = get_view({"patch": "permissions"}, pk=self.group.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_overlapping_add_and_remove_returns_400(self):
        user = make_user("changer_perm8", permission_codenames=["change_group"])
        request = factory.patch(self.url, {
            "add_permissions": [self.view_perm],
            "remove_permissions": [self.view_perm],
        }, format="json")
        force_authenticate(request, user=user)
        response = get_view({"patch": "permissions"}, pk=self.group.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_permission_format_returns_400(self):
        user = make_user("changer_perm9", permission_codenames=["change_group"])
        request = factory.patch(self.url, {"add_permissions": ["not_a_valid_format"]}, format="json")
        force_authenticate(request, user=user)
        response = get_view({"patch": "permissions"}, pk=self.group.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_nonexistent_permission_returns_400(self):
        user = make_user("changer_perm10", permission_codenames=["change_group"])
        non_existent_pk = Permission.objects.order_by("-pk").first().pk + 1
        request = factory.patch(self.url, {"add_permissions": [non_existent_pk]}, format="json")
        force_authenticate(request, user=user)
        response = get_view({"patch": "permissions"}, pk=self.group.pk)(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_permissions_on_non_existent_pk_returns_404(self):
        user = make_user("changer_perm11", permission_codenames=["change_group"])
        request = factory.patch("/groups/999999/permissions/", {"add_permissions": [self.view_perm]}, format="json")
        force_authenticate(request, user=user)
        response = get_view({"patch": "permissions"}, pk=999999)(request)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)