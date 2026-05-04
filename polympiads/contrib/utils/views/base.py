
from rest_framework import viewsets

from polympiads.contrib.utils.serializers.mixins import is_browsable_url_mixin, BROWSABLE_URL_MIXIN_WARNING

class ModelViewSet (viewsets.ModelViewSet):
    @classmethod
    def use_url_warning (cls):
        return is_browsable_url_mixin(cls.serializer_class)

    def __init_subclass__(cls):
        if cls.use_url_warning():
            base_doc = cls.__doc__
            if base_doc is None:
                base_doc = ""
            
            base_doc = base_doc + BROWSABLE_URL_MIXIN_WARNING
            cls.__doc__ = base_doc

        return super().__init_subclass__()
