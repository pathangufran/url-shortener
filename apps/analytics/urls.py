from django.urls import path
from .views import URLAnalyticsAPIView

app_name = "analytics"

urlpatterns = [
    path("urls/<uuid:url_id>/analytics/",URLAnalyticsAPIView.as_view(),name="url-analytics",),
]