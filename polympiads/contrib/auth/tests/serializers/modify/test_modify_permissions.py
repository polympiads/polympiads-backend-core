
from typing import Any

from django.test import TestCase
from django.contrib.auth.models import Permission

from polympiads.contrib.auth.serializers.modify.permissions import ModifyPermissionsSerializer


class TestModifyPermissionsSerializer (TestCase):
    def get_data (self, data: Any):
        ser = ModifyPermissionsSerializer(data = data)
        if not ser.is_valid():
            print(ser.errors)
            raise AssertionError()
        return ser.data
    def get_errors (self, data: Any):
        ser = ModifyPermissionsSerializer(data = data)
        assert not ser.is_valid()
        return ser.errors
    
    def test_serializer_empty_data (self):
        errors = self.get_errors({})
        assert errors.keys() == { 'non_field_errors' }
        assert errors["non_field_errors"][0].code == "invalid"
        assert errors["non_field_errors"][0] == "At least one of add_permissions or remove_permissions must be provided."
    def test_serializer_conflict (self):
        errors = self.get_errors({
            "add_permissions"    : [ "polympiads_auth.access_dashboard" ],
            "remove_permissions" : [ "polympiads_auth.access_dashboard" ]
        })
        assert errors.keys() == { 'non_field_errors' }
        assert errors["non_field_errors"][0].code == "invalid"
        assert errors["non_field_errors"][0] == "Cannot add and remove the same permissions simultaneously."

    def test_serializer_wrong_type (self):
        errors = self.get_errors({
            "add_permissions": [0],
            "remove_permissions": [None],
        })
        assert errors.keys() == { 'add_permissions', "remove_permissions" }
        assert errors["add_permissions"][0].code == "invalid_type"
        assert errors["add_permissions"][0] == "Expected a string, got int."
        assert errors["remove_permissions"][0].code == "invalid_type"
        assert errors["remove_permissions"][0] == "Expected a string, got NoneType."
    def test_serializer_wrong_split (self):
        errors = self.get_errors({
            "add_permissions"    : [ "aaaaaa" ],
            "remove_permissions" : [ "aa.bb.cc"],
        })
        assert errors.keys() == { 'add_permissions', "remove_permissions" }
        assert errors["add_permissions"][0].code == "invalid_format"
        assert errors["add_permissions"][0] == "Expected format: app_label.codename, got \'aaaaaa\'."
        assert errors["remove_permissions"][0].code == "invalid_format"
        assert errors["remove_permissions"][0] == "Expected format: app_label.codename, got \'aa.bb.cc\'."
    def test_serializer_perm_doesnt_exist (self):
        errors = self.get_errors({
            "add_permissions"    : [ "polympiads_auth.access_dashboard1" ],
            "remove_permissions" : [ "polympiads_auth.access_dashboard2"],
        })
        assert errors.keys() == { 'add_permissions', "remove_permissions" }
        assert errors["add_permissions"][0].code == "does_not_exist"
        assert errors["add_permissions"][0] == "Permission with app_label.codename=polympiads_auth.access_dashboard1 does not exist."
        assert errors["remove_permissions"][0].code == "does_not_exist"
        assert errors["remove_permissions"][0] == "Permission with app_label.codename=polympiads_auth.access_dashboard2 does not exist."

    def test_serializer_properly_returns_to_add_and_to_remove (self):
        data = self.get_data({
            "add_permissions" : [ "polympiads_auth.access_dashboard" ],
            "remove_permissions" : [ "polympiads_auth.view_user", "polympiads_auth.change_user" ]
        })
        assert len(data["add_permissions"]) == 1
        assert len(data["remove_permissions"]) == 2
        data = self.get_data({
            "add_permissions" : [ "polympiads_auth.access_dashboard" ],
            "remove_permissions" : []
        })
        assert len(data["add_permissions"]) == 1
        assert len(data["remove_permissions"]) == 0
        data = self.get_data({
            "add_permissions" : [],
            "remove_permissions" : [ "polympiads_auth.view_user", "polympiads_auth.change_user" ]
        })
        assert len(data["add_permissions"]) == 0
        assert len(data["remove_permissions"]) == 2

