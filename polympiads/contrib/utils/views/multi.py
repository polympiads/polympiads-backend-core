
from drf_spectacular.utils import extend_schema

from polympiads.contrib.utils.views import ModelViewSet
from polympiads.contrib.utils.serializers.mixins  import is_browsable_url_mixin

def extra_serializer (request = None, response = None):
    """
    Decorator to setup the extra action for the browsable api, as well as serializers
    and finally setup the DRF spectacular bindings for that action. 
    """
    def decorator (func):
        func.request_serializer_class  = request
        func.response_serializer_class = response
        return extend_schema(request=request, responses=response)(func)

    return decorator

class MultiSerializerViewSet (ModelViewSet):
    summary_serializer_class = None
    details_serializer_class = None
    
    def _get_primary_serializer_class (self):
        if self.action == "list":
            return self.summary_serializer_class
        return self.details_serializer_class

    def get_response_serializer (self, *args, **kwargs):
        """
        Return the serializer instance that should be used for serializing output.
        """
        serializer_class = self.get_response_serializer_class()
        kwargs.setdefault('context', self.get_serializer_context())
        return serializer_class(*args, **kwargs)

    def get_response_serializer_class (self):
        handler = getattr(self, self.action, None)
        if handler is not None:
            response_serializer_class = getattr(handler, "response_serializer_class", None)
            if response_serializer_class is not None:
                return response_serializer_class
        
        return self._get_primary_serializer_class()

    def get_serializer_class(self):
        handler = getattr(self, self.action, None)
        if handler is not None:
            request_serializer_class = getattr(handler, "request_serializer_class", None)
            if request_serializer_class is not None:
                return request_serializer_class

        return self._get_primary_serializer_class()

    @classmethod
    def use_url_warning (cls):
        return is_browsable_url_mixin(cls.summary_serializer_class) \
            or is_browsable_url_mixin(cls.details_serializer_class)

    def __init_subclass__(cls):
        assert cls.summary_serializer_class is not None, f"Configuration error on {cls} (missing 'summary_serializer_class')"
        assert cls.details_serializer_class is not None, f"Configuration error on {cls} (missing 'details_serializer_class')"

        super().__init_subclass__()
