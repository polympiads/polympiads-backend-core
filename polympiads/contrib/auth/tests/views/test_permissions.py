
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
        self.assertIsInstance(response.data, dict)
        self.assertIsInstance(response.data["results"], list)

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

# ---------------------------------------------------------------------------
# 7. FILTERING, SEARCHING & ORDERING  (GET /permissions/)
# ---------------------------------------------------------------------------

class TestFilteringSearchingOrdering(TestCase):

    def setUp(self):
        self.viewer = make_user("viewer_f", permission_codenames=["view_permission"])
        self.ct = ContentType.objects.get_for_model(Permission)

    def _list(self, query_params=None):
        request = factory.get("/permissions/", query_params or {})
        force_authenticate(request, user=self.viewer)
        response = get_view({"get": "list"})(request)
        response.render()
        return response

    def _names(self, response):
        return [p["name"] for p in response.data["results"]]

    # ------------------------------------------------------------------ #
    # Pagination structure                                                 #
    # ------------------------------------------------------------------ #

    def test_response_has_pagination_envelope(self):
        response = self._list()
        for key in ("count", "next", "previous", "results"):
            self.assertIn(key, response.data)

    def test_count_reflects_total_not_page_size(self):
        total = Permission.objects.count()
        response = self._list({"page_size": 1})
        self.assertEqual(response.data["count"], total)
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
        response = self._list({"name": "Can view"})
        names = self._names(response)
        self.assertGreater(len(names), 0)
        self.assertTrue(all("view" in n.lower() for n in names))

    def test_filter_name_case_insensitive(self):
        response = self._list({"name": "CAN VIEW"})
        self.assertGreater(response.data["count"], 0)

    def test_filter_name_no_match_returns_empty(self):
        response = self._list({"name": "zzznomatch"})
        self.assertEqual(response.data["count"], 0)
        self.assertEqual(response.data["results"], [])

    def test_filter_name_partial_match(self):
        response = self._list({"name": "permission"})
        self.assertGreater(response.data["count"], 0)
        names = self._names(response)
        self.assertTrue(all("permission" in n.lower() for n in names))

    def test_filter_name_narrows_results(self):
        total    = self._list().data["count"]
        filtered = self._list({"name": "Can view"}).data["count"]
        self.assertLess(filtered, total)

    # ------------------------------------------------------------------ #
    # Search                                                               #
    # ------------------------------------------------------------------ #

    def test_search_matches_name(self):
        response = self._list({"search": "view permission"})
        self.assertGreater(response.data["count"], 0)

    def test_search_is_case_insensitive(self):
        response = self._list({"search": "VIEW PERMISSION"})
        self.assertGreater(response.data["count"], 0)

    def test_search_no_match_returns_empty(self):
        response = self._list({"search": "zzznomatch"})
        self.assertEqual(response.data["count"], 0)

    def test_search_returns_subset_of_unfiltered(self):
        total    = self._list().data["count"]
        filtered = self._list({"search": "view"}).data["count"]
        self.assertLessEqual(filtered, total)

    # ------------------------------------------------------------------ #
    # Ordering                                                             #
    # ------------------------------------------------------------------ #

    def test_default_ordering_is_by_pk_descending(self):
        response = self._list()
        ids = [p["id"] for p in response.data["results"]]
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
        response = self._list({"ordering": "codename"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_ordering_unknown_field_falls_back_to_default(self):
        default   = self._names(self._list())
        with_junk = self._names(self._list({"ordering": "nonexistent_field"}))
        self.assertEqual(default, with_junk)

    # ------------------------------------------------------------------ #
    # Combined                                                             #
    # ------------------------------------------------------------------ #

    def test_filter_and_search_combined(self):
        response = self._list({"name": "Can view", "search": "permission"})
        self.assertGreater(response.data["count"], 0)
        names = self._names(response)
        self.assertTrue(all("view" in n.lower() for n in names))

    def test_filter_ordering_pagination_combined(self):
        response = self._list({
            "name":      "Can",
            "ordering":  "name",
            "page":      1,
            "page_size": 2,
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data["count"], 2)
        names = self._names(response)
        self.assertEqual(len(names), 2)
        self.assertEqual(names, sorted(names))