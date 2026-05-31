import hashlib
import io
import json
from unittest.mock import patch

import yaml
from django.test import TestCase
from django.core.management import call_command


EXPECTED_EMPTY_SCHEMA = {
    "components": {},
    "info": {
        "description": "Backend of polympiads",
        "title": "Polympiads Backend",
        "version": "1.0.0",
    },
    "openapi": "3.0.3",
    "paths": {},
}

EXPECTED_DRF_SCHEMA = {
    "components": {
        "schemas": {
            "AuthToken": {
                "properties": {
                    "password": {"type": "string", "writeOnly": True},
                    "token": {"readOnly": True, "type": "string"},
                    "username": {"type": "string", "writeOnly": True},
                },
                "required": ["password", "token", "username"],
                "type": "object",
            }
        },
        "securitySchemes": {
            "cookieAuth": {
                "in": "cookie",
                "name": "sessionid",
                "type": "apiKey",
            },
            "tokenAuth": {
                "description": 'Token-based authentication with required prefix "Token"',
                "in": "header",
                "name": "Authorization",
                "type": "apiKey",
            },
        },
    },
    "info": {
        "description": "Backend of polympiads",
        "title": "Polympiads Backend",
        "version": "1.0.0",
    },
    "openapi": "3.0.3",
    "paths": {
        "/api/v1/login/": {
            "post": {
                "operationId": "api_v1_login_create",
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/AuthToken"}
                        },
                        "application/x-www-form-urlencoded": {
                            "schema": {"$ref": "#/components/schemas/AuthToken"}
                        },
                        "multipart/form-data": {
                            "schema": {"$ref": "#/components/schemas/AuthToken"}
                        },
                    },
                    "required": True,
                },
                "responses": {
                    "200": {
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/AuthToken"}
                            }
                        },
                        "description": "",
                    }
                },
                "security": [{"tokenAuth": []}, {"cookieAuth": []}],
                "tags": ["api"],
            }
        }
    },
}

def sha256_of_string(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def run_command(app_label: str, fmt: str = "yaml") -> str:
    """Run the management command and capture stdout."""
    stdout = io.StringIO()
    call_command(
        "export_app_schema",
        app_label,
        format=fmt,
        stdout=stdout,
    )
    return stdout.getvalue()


class TestAppFilteredSchemaGeneratorDirect(TestCase):
    """Tests exercising AppFilteredSchemaGenerator directly."""

    def _get_schema(self, app_label):
        from polympiads.contrib.utils.management.commands.export_app_schema import AppFilteredSchemaGenerator
        generator = AppFilteredSchemaGenerator(app_label=app_label)
        return generator.get_schema(request=None, public=True)

    def test_yes_app_has_no_paths(self):
        schema = self._get_schema("yes")
        self.assertEqual(schema["paths"], {})

    def test_yes_app_has_no_components(self):
        schema = self._get_schema("yes")
        self.assertEqual(schema.get("components", {}), {})

    def test_yes_app_openapi_version(self):
        schema = self._get_schema("yes")
        self.assertEqual(schema["openapi"], "3.0.3")

    def test_drf_app_only_login_path(self):
        schema = self._get_schema("rest_framework")
        self.assertEqual(list(schema["paths"].keys()), ["/api/v1/login/"])

    def test_drf_app_login_has_post(self):
        schema = self._get_schema("rest_framework")
        self.assertIn("post", schema["paths"]["/api/v1/login/"])

    def test_drf_app_login_operation_id(self):
        schema = self._get_schema("rest_framework")
        op = schema["paths"]["/api/v1/login/"]["post"]
        self.assertEqual(op["operationId"], "api_v1_login_create")

    def test_drf_app_auth_token_schema_present(self):
        schema = self._get_schema("rest_framework")
        self.assertIn("AuthToken", schema["components"]["schemas"])

    def test_drf_app_security_schemes(self):
        schema = self._get_schema("rest_framework")
        schemes = schema["components"]["securitySchemes"]
        self.assertIn("cookieAuth", schemes)
        self.assertIn("tokenAuth", schemes)

    def test_drf_app_full_schema_matches(self):
        schema = self._get_schema("rest_framework")
        self.assertEqual(schema, EXPECTED_DRF_SCHEMA)

    def test_no_app_label_returns_full_schema(self):
        from polympiads.contrib.utils.management.commands.export_app_schema import AppFilteredSchemaGenerator
        generator = AppFilteredSchemaGenerator(app_label=None)
        schema = generator.get_schema(request=None, public=True)
        # Full schema must contain at least the login path and auth paths
        self.assertIn("/api/v1/login/", schema["paths"])

    def test_endpoints_filtered_by_module(self):
        """Endpoints from other apps must not bleed into the filtered result."""
        schema = self._get_schema("rest_framework")
        for path in schema["paths"]:
            self.assertTrue(
                path.startswith("/api/v1/login"),
                f"Unexpected path leaked into rest_framework schema: {path}",
            )

class TestExportAppSchemaCommand(TestCase):
    """Tests for the management command (no files written to disk)."""

    # ------------------------------------------------------------------ #
    # yes app – empty schema                                               #
    # ------------------------------------------------------------------ #

    def test_command_yes_yaml_output_paths_empty(self):
        output = run_command("yes", fmt="yaml")
        schema = yaml.safe_load(output)
        self.assertEqual(schema["paths"], {})

    def test_command_yes_yaml_output_components_empty(self):
        output = run_command("yes", fmt="yaml")
        schema = yaml.safe_load(output)
        self.assertEqual(schema.get("components", {}), {})

    def test_command_yes_json_output_paths_empty(self):
        output = run_command("yes", fmt="json")
        schema = json.loads(output)
        self.assertEqual(schema["paths"], {})

    def test_command_yes_yaml_matches_expected(self):
        output = run_command("yes", fmt="yaml")
        schema = yaml.safe_load(output)
        self.assertEqual(schema, EXPECTED_EMPTY_SCHEMA)

    def test_command_yes_json_matches_expected(self):
        output = run_command("yes", fmt="json")
        schema = json.loads(output)
        self.assertEqual(schema, EXPECTED_EMPTY_SCHEMA)

    # ------------------------------------------------------------------ #
    # rest_framework app                                                   #
    # ------------------------------------------------------------------ #

    def test_command_drf_yaml_login_present(self):
        output = run_command("rest_framework", fmt="yaml")
        schema = yaml.safe_load(output)
        self.assertIn("/api/v1/login/", schema["paths"])

    def test_command_drf_yaml_only_login_path(self):
        output = run_command("rest_framework", fmt="yaml")
        schema = yaml.safe_load(output)
        self.assertEqual(list(schema["paths"].keys()), ["/api/v1/login/"])

    def test_command_drf_json_login_present(self):
        output = run_command("rest_framework", fmt="json")
        schema = json.loads(output)
        self.assertIn("/api/v1/login/", schema["paths"])

    def test_command_drf_yaml_matches_expected(self):
        output = run_command("rest_framework", fmt="yaml")
        schema = yaml.safe_load(output)
        self.assertEqual(schema, EXPECTED_DRF_SCHEMA)

    def test_command_drf_json_matches_expected(self):
        output = run_command("rest_framework", fmt="json")
        schema = json.loads(output)
        self.assertEqual(schema, EXPECTED_DRF_SCHEMA)

    # ------------------------------------------------------------------ #
    # --output flag must NOT write files (patched)                        #
    # ------------------------------------------------------------------ #

    def test_command_output_flag_writes_correct_content(self):
        written = {}

        def fake_open(path, mode="r"):
            buf = io.StringIO()
            original_close = buf.close

            def capturing_close():
                written[path] = buf.getvalue()
                original_close()

            buf.close = capturing_close
            return buf

        with patch("builtins.open", side_effect=fake_open):
            stdout = io.StringIO()
            call_command(
                "export_app_schema",
                "yes",
                format="yaml",
                output="/fake/path/schema.yaml",
                stdout=stdout,
            )

        self.assertIn("/fake/path/schema.yaml", written)
        schema = yaml.safe_load(written["/fake/path/schema.yaml"])
        self.assertEqual(schema, EXPECTED_EMPTY_SCHEMA)

    def test_command_output_flag_stdout_message(self):
        with patch("builtins.open", return_value=io.StringIO()):
            stdout = io.StringIO()
            call_command(
                "export_app_schema",
                "yes",
                format="yaml",
                output="/fake/path/schema.yaml",
                stdout=stdout,
            )
        self.assertIn("Schema written to", stdout.getvalue())

    def test_command_no_output_flag_writes_to_stdout_only(self):
        """When --output is omitted, nothing should be written to disk."""
        with patch("builtins.open") as mock_open:
            run_command("yes", fmt="yaml")
            mock_open.assert_not_called()