from .models import URL
import django_filters

class URLFilter(django_filters.FilterSet):
    class Meta:
        model = URL
        fields = {
            "is_active": ["exact"],
        }
