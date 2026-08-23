import django_filters

from .models import URL


class URLFilter(django_filters.FilterSet):
    class Meta:
        model = URL
        fields = {
            "is_active": ["exact"],
        }
