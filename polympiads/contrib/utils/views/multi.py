
from polympiads.contrib.utils.views import ModelViewSet
from polympiads.contrib.utils.serializers.mixins  import is_browsable_url_mixin

class MultiSerializerViewSet (ModelViewSet):
    summary_serializer_class = None
    details_serializer_class = None
    
    def get_serializer_class(self):
        if self.action == "list":
            return self.summary_serializer_class
        return self.details_serializer_class

    @classmethod
    def use_url_warning (cls):
        return is_browsable_url_mixin(cls.summary_serializer_class) \
            or is_browsable_url_mixin(cls.details_serializer_class)

    def __init_subclass__(cls):
        assert cls.summary_serializer_class is not None, f"Configuration error on {cls} (missing 'summary_serializer_class')"
        assert cls.details_serializer_class is not None, f"Configuration error on {cls} (missing 'details_serializer_class')"

        super().__init_subclass__()
