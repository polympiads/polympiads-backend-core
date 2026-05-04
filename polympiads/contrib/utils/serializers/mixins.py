
from rest_framework import serializers

BROWSABLE_URL_MIXIN_WARNING = """
**Note on URLs:** The `url` fields found in this interface are 
provided for convenience in the browser. Standard JSON 
requests will exclude them for performance.
"""

def is_browsable_url_mixin (obj):
    return obj is not None and issubclass(obj, BrowsableUrlMixin)

class BrowsableUrlMixin:
    """
    Adds a 'url' field to the output only when viewed in the Browsable API.
    """

    def to_representation(self, instance):
        data    = super().to_representation(instance)
        request = self.context.get('request')
        
        if request and 'text/html' in getattr(request.accepted_renderer, 'media_type', ''):
            url_field = serializers.HyperlinkedIdentityField(
                view_name=f"{instance._meta.model_name}-detail"
            )
            
            url_field.bind(field_name='url', parent=self)
            
            attribute = url_field.get_attribute(instance)
            if attribute is not None:
                data['url'] = url_field.to_representation(attribute)
        return data
