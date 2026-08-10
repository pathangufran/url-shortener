from django.urls import path
from .views import URLAnalyticsAPIView,URLClickEventsAPIView

app_name = "analytics"

urlpatterns = [
    path("urls/<uuid:url_id>/analytics/",URLAnalyticsAPIView.as_view(),name="url-analytics",),
    path("urls/<uuid:url_id>/clicks/",URLClickEventsAPIView.as_view(),name="url-click-events",),
]