from django.test import TestCase, RequestFactory, override_settings
from django.test.utils import isolate_apps
from django.db import models, connection
from django.urls import path, include, reverse

from rest_framework import serializers, viewsets, routers
from rest_framework.renderers import BrowsableAPIRenderer, JSONRenderer
from rest_framework.request import Request

from polympiads.contrib.utils.serializers import BrowsableUrlMixin

class Widget(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        app_label = "tests"

class WidgetSerializer(BrowsableUrlMixin, serializers.ModelSerializer):
    class Meta:
        model = Widget
        fields = ["id", "name"]

class WidgetViewSet(viewsets.ModelViewSet):
    queryset = Widget.objects.all()
    serializer_class = WidgetSerializer

router = routers.DefaultRouter()
router.register(r"widgets", WidgetViewSet, basename="widget")

urlpatterns = [
    path("api/", include(router.urls)),
]

def make_request(factory: RequestFactory, accept_html: bool) -> Request:
    """Wrap a Django request in a DRF Request with the right renderer."""
    django_request = factory.get("/api/widgets/")
    renderer = BrowsableAPIRenderer() if accept_html else JSONRenderer()
    drf_request = Request(django_request)
    drf_request.accepted_renderer = renderer
    return drf_request

@isolate_apps("tests")
@override_settings(ROOT_URLCONF=__name__)
class BrowsableUrlMixinTests(TestCase):
    @classmethod
    def setUpClass(cls):
        with connection.cursor() as cursor:
            cursor.execute("PRAGMA foreign_keys = OFF")
        super().setUpClass()
        with connection.schema_editor() as schema:
            schema.create_model(Widget)

    @classmethod
    def tearDownClass(cls):
        with connection.schema_editor() as schema:
            schema.delete_model(Widget)
        super().tearDownClass()
        with connection.cursor() as cursor:
            cursor.execute("PRAGMA foreign_keys = ON")

    def setUp(self):
        self.factory = RequestFactory()
        self.widget = Widget.objects.create(name="sprocket")

    def _serialize(self, accept_html: bool) -> dict:
        request = make_request(self.factory, accept_html)
        serializer = WidgetSerializer(
            self.widget,
            context={"request": request},
        )
        return serializer.data

    def test_url_absent_for_json_requests(self):
        data = self._serialize(accept_html=False)
        self.assertNotIn("url", data)

    def test_url_present_for_html_requests(self):
        data = self._serialize(accept_html=True)
        self.assertIn("url", data)

    def test_url_points_to_correct_instance(self):
        data = self._serialize(accept_html=True)
        expected = f"/api/widgets/{self.widget.pk}/"
        self.assertTrue(
            data["url"].endswith(expected),
            f"Expected URL ending with {expected!r}, got {data['url']!r}",
        )

    def test_base_fields_always_present(self):
        for accept_html in (True, False):
            with self.subTest(accept_html=accept_html):
                data = self._serialize(accept_html)
                self.assertEqual(data["id"], self.widget.pk)
                self.assertEqual(data["name"], self.widget.name)

    def test_no_url_when_request_missing_from_context(self):
        serializer = WidgetSerializer(self.widget, context={})
        data = serializer.data
        self.assertNotIn("url", data)