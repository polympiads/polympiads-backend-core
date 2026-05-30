from django.test import TestCase
from rest_framework.permissions import BasePermission

from polympiads.contrib.utils.permissions.never import NeverAllow
from polympiads.contrib.utils.permissions import ActionPermissionMixin

# ---------------------------------------------------------------------------
# Dummy permission classes used as distinct markers in assertions
# ---------------------------------------------------------------------------

class PermissionA(BasePermission):
    pass

class PermissionB(BasePermission):
    pass

class PermissionC(BasePermission):
    pass


# ---------------------------------------------------------------------------
# Concrete subclasses covering the different configuration scenarios
# ---------------------------------------------------------------------------

class DefaultOnlyMixin(ActionPermissionMixin):
    """No by-action overrides — everything falls back to the default."""
    permission_classes_default = [PermissionA]
    permission_classes_by_action = {}


class ExplicitActionsMixin(ActionPermissionMixin):
    """Every action is mapped explicitly — no aliases needed."""
    permission_classes_default = [NeverAllow]
    permission_classes_by_action = {
        'list':           [PermissionA],
        'retrieve':       [PermissionA],
        'create':         [PermissionB],
        'update':         [PermissionB],
        'partial_update': [PermissionB],
        'destroy':        [PermissionC],
    }


class AliasMixin(ActionPermissionMixin):
    """Uses the 'get' and 'edit' aliases instead of individual actions."""
    permission_classes_default = [NeverAllow]
    permission_classes_by_action = {
        'get':  [PermissionA],
        'edit': [PermissionB],
    }


class MixedMixin(ActionPermissionMixin):
    """Some actions explicit, some resolved via alias, some fall back to default."""
    permission_classes_default = [PermissionC]
    permission_classes_by_action = {
        'get':    [PermissionA],  # alias — covers list + retrieve
        'create': [PermissionB],  # explicit — no alias for create
        # update / partial_update / destroy not configured → default
    }


class MultiplePermissionsMixin(ActionPermissionMixin):
    """Verifies that multiple permission classes are all instantiated."""
    permission_classes_default = [NeverAllow]
    permission_classes_by_action = {
        'get': [PermissionA, PermissionB],
    }


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def make_view(mixin_class, action):
    view = mixin_class()
    view.action = action
    return view


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestDefaultFallback(TestCase):
    """When permission_classes_by_action is empty, every action uses the default."""

    def _perms(self, action):
        return make_view(DefaultOnlyMixin, action).get_permissions()

    def test_list_uses_default(self):
        self.assertIsInstance(self._perms('list')[0], PermissionA)

    def test_retrieve_uses_default(self):
        self.assertIsInstance(self._perms('retrieve')[0], PermissionA)

    def test_create_uses_default(self):
        self.assertIsInstance(self._perms('create')[0], PermissionA)

    def test_update_uses_default(self):
        self.assertIsInstance(self._perms('update')[0], PermissionA)

    def test_partial_update_uses_default(self):
        self.assertIsInstance(self._perms('partial_update')[0], PermissionA)

    def test_destroy_uses_default(self):
        self.assertIsInstance(self._perms('destroy')[0], PermissionA)

    def test_unknown_action_uses_default(self):
        self.assertIsInstance(self._perms('unknown')[0], PermissionA)


class TestExplicitActionMapping(TestCase):
    """When every action is mapped explicitly the alias logic is never reached."""

    def _perms(self, action):
        return make_view(ExplicitActionsMixin, action).get_permissions()

    def test_list_returns_permission_a(self):
        self.assertIsInstance(self._perms('list')[0], PermissionA)

    def test_retrieve_returns_permission_a(self):
        self.assertIsInstance(self._perms('retrieve')[0], PermissionA)

    def test_create_returns_permission_b(self):
        self.assertIsInstance(self._perms('create')[0], PermissionB)

    def test_update_returns_permission_b(self):
        self.assertIsInstance(self._perms('update')[0], PermissionB)

    def test_partial_update_returns_permission_b(self):
        self.assertIsInstance(self._perms('partial_update')[0], PermissionB)

    def test_destroy_returns_permission_c(self):
        self.assertIsInstance(self._perms('destroy')[0], PermissionC)

    def test_unmapped_action_falls_back_to_default(self):
        self.assertIsInstance(self._perms('unknown')[0], NeverAllow)


class TestAliasResolution(TestCase):
    """'list' and 'retrieve' resolve via the 'get' alias;
       'update' and 'partial_update' resolve via the 'edit' alias."""

    def _perms(self, action):
        return make_view(AliasMixin, action).get_permissions()

    def test_list_resolves_via_get_alias(self):
        self.assertIsInstance(self._perms('list')[0], PermissionA)

    def test_retrieve_resolves_via_get_alias(self):
        self.assertIsInstance(self._perms('retrieve')[0], PermissionA)

    def test_update_resolves_via_edit_alias(self):
        self.assertIsInstance(self._perms('update')[0], PermissionB)

    def test_partial_update_resolves_via_edit_alias(self):
        self.assertIsInstance(self._perms('partial_update')[0], PermissionB)

    def test_create_not_aliased_falls_back_to_default(self):
        self.assertIsInstance(self._perms('create')[0], NeverAllow)

    def test_destroy_not_aliased_falls_back_to_default(self):
        self.assertIsInstance(self._perms('destroy')[0], NeverAllow)


class TestExplicitOverridesAlias(TestCase):
    """An explicit entry for an action takes precedence over its alias."""

    def _perms(self, action):
        # 'list' is explicit AND covered by the 'get' alias — explicit wins
        mixin = ActionPermissionMixin()
        mixin.permission_classes_default = [NeverAllow]
        mixin.permission_classes_by_action = {
            'get':  [PermissionA],   # alias
            'list': [PermissionB],   # explicit — should win over alias
        }
        mixin.action = action
        return mixin.get_permissions()

    def test_explicit_list_overrides_get_alias(self):
        self.assertIsInstance(self._perms('list')[0], PermissionB)

    def test_retrieve_still_resolves_via_get_alias(self):
        self.assertIsInstance(self._perms('retrieve')[0], PermissionA)


class TestMixedConfiguration(TestCase):
    """Realistic scenario: some actions explicit, some aliased, some default."""

    def _perms(self, action):
        return make_view(MixedMixin, action).get_permissions()

    def test_list_resolves_via_get_alias(self):
        self.assertIsInstance(self._perms('list')[0], PermissionA)

    def test_retrieve_resolves_via_get_alias(self):
        self.assertIsInstance(self._perms('retrieve')[0], PermissionA)

    def test_create_uses_explicit_mapping(self):
        self.assertIsInstance(self._perms('create')[0], PermissionB)

    def test_update_falls_back_to_default(self):
        self.assertIsInstance(self._perms('update')[0], PermissionC)

    def test_partial_update_falls_back_to_default(self):
        self.assertIsInstance(self._perms('partial_update')[0], PermissionC)

    def test_destroy_falls_back_to_default(self):
        self.assertIsInstance(self._perms('destroy')[0], PermissionC)


class TestMultiplePermissionClasses(TestCase):
    """All permission classes in a list are instantiated and returned."""

    def test_get_returns_all_permission_instances(self):
        perms = make_view(MultiplePermissionsMixin, 'get').get_permissions()
        self.assertEqual(len(perms), 2)
        self.assertIsInstance(perms[0], PermissionA)
        self.assertIsInstance(perms[1], PermissionB)

    def test_list_resolves_alias_and_returns_all_instances(self):
        perms = make_view(MultiplePermissionsMixin, 'list').get_permissions()
        self.assertEqual(len(perms), 2)
        self.assertIsInstance(perms[0], PermissionA)
        self.assertIsInstance(perms[1], PermissionB)


class TestFreshInstancesPerCall(TestCase):
    """Each call to get_permissions() must return new instances, not cached ones."""

    def test_repeated_calls_return_different_instances(self):
        view = make_view(AliasMixin, 'list')
        perms_a = view.get_permissions()
        perms_b = view.get_permissions()
        self.assertIsNot(perms_a[0], perms_b[0])