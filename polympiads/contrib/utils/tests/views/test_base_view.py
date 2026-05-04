
from django.test import TestCase

from polympiads.contrib.utils.serializers.mixins import BROWSABLE_URL_MIXIN_WARNING
from polympiads.contrib.utils.views import ModelViewSet
from polympiads.contrib.utils.serializers import BrowsableUrlMixin

class View1(ModelViewSet):
    """Doc1"""
    
    @classmethod
    def use_url_warning(cls):
        return False
class View2(ModelViewSet):
    """Doc2"""
    
    @classmethod
    def use_url_warning(cls):
        return True
class View3(ModelViewSet):
    @classmethod
    def use_url_warning(cls):
        return True

class Seri1: pass
class Seri2 (BrowsableUrlMixin): pass

class ViewS1(ModelViewSet):
    """DocS1"""
    serializer_class=Seri1
class ViewS2(ModelViewSet):
    """DocS2"""
    serializer_class=Seri2

class TestModelViewSet (TestCase):
    def test_no_warning (self):
        self.assertEqual(View1.__doc__, "Doc1")
        self.assertEqual(ViewS1.__doc__, "DocS1")
    def test_warning (self):
        self.assertEqual(View2.__doc__, "Doc2"+ BROWSABLE_URL_MIXIN_WARNING)
        self.assertEqual(View3.__doc__, BROWSABLE_URL_MIXIN_WARNING)
        self.assertEqual(ViewS2.__doc__, "DocS2"+ BROWSABLE_URL_MIXIN_WARNING)
