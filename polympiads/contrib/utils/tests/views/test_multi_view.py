
from django.test import TestCase

from polympiads.contrib.utils.serializers.mixins import BrowsableUrlMixin, BROWSABLE_URL_MIXIN_WARNING
from polympiads.contrib.utils.views import MultiSerializerViewSet

class Seri1: pass
class Seri2 (BrowsableUrlMixin): pass

class TestMultiViewSet (TestCase):
    def test_throws (self):
        with self.assertRaises(AssertionError):
            class V1 (MultiSerializerViewSet):
                summary_serializer_class = None
                details_serializer_class = None
        with self.assertRaises(AssertionError):
            class V1 (MultiSerializerViewSet):
                summary_serializer_class = Seri1
                details_serializer_class = None
        with self.assertRaises(AssertionError):
            class V1 (MultiSerializerViewSet):
                summary_serializer_class = None
                details_serializer_class = Seri1
    def test_doc_no_url_mixin (self):
        class V (MultiSerializerViewSet):
            summary_serializer_class = Seri1
            details_serializer_class = Seri1
        self.assertEqual(V.__doc__, None)
    def test_doc_with_url_mixin (self):
        class V (MultiSerializerViewSet):
            summary_serializer_class = Seri2
            details_serializer_class = Seri1
        self.assertEqual(V.__doc__, BROWSABLE_URL_MIXIN_WARNING)
        class V (MultiSerializerViewSet):
            summary_serializer_class = Seri1
            details_serializer_class = Seri2
        self.assertEqual(V.__doc__, BROWSABLE_URL_MIXIN_WARNING)
        class V (MultiSerializerViewSet):
            summary_serializer_class = Seri2
            details_serializer_class = Seri2
        self.assertEqual(V.__doc__, BROWSABLE_URL_MIXIN_WARNING)






from django.test import TestCase, RequestFactory
from rest_framework import serializers, routers
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from polympiads.contrib.utils.views import MultiSerializerViewSet

class SummarySerializer(serializers.Serializer):
    pass

class DetailSerializer(serializers.Serializer):
    pass

class ConcreteViewSet(MultiSerializerViewSet):
    summary_serializer_class = SummarySerializer
    details_serializer_class = DetailSerializer

def make_viewset(action: str) -> ConcreteViewSet:
    request = APIRequestFactory().get("/")
    viewset = ConcreteViewSet()
    viewset.action = action
    viewset.request = Request(request)
    viewset.kwargs = {}
    viewset.format_kwarg = None
    return viewset

class MultiSerializerViewSetTests(TestCase):

    def test_list_returns_summary_serializer(self):
        viewset = make_viewset("list")
        self.assertIs(viewset.get_serializer_class(), SummarySerializer)

    def test_retrieve_returns_detail_serializer(self):
        viewset = make_viewset("retrieve")
        self.assertIs(viewset.get_serializer_class(), DetailSerializer)

    def test_create_returns_detail_serializer(self):
        viewset = make_viewset("create")
        self.assertIs(viewset.get_serializer_class(), DetailSerializer)

    def test_update_returns_detail_serializer(self):
        viewset = make_viewset("update")
        self.assertIs(viewset.get_serializer_class(), DetailSerializer)

    def test_partial_update_returns_detail_serializer(self):
        viewset = make_viewset("partial_update")
        self.assertIs(viewset.get_serializer_class(), DetailSerializer)

    def test_destroy_returns_detail_serializer(self):
        viewset = make_viewset("destroy")
        self.assertIs(viewset.get_serializer_class(), DetailSerializer)

    def test_summary_serializer_class_none_by_default(self):
        viewset = MultiSerializerViewSet()
        self.assertIsNone(viewset.summary_serializer_class)

    def test_details_serializer_class_none_by_default(self):
        viewset = MultiSerializerViewSet()
        self.assertIsNone(viewset.details_serializer_class)
