from django.urls import path
from .views import CreateURLAPIView,URLListAPIView,URLRetrieveAPIView

app_name = "shortener"

urlpatterns = [
    path("",CreateURLAPIView.as_view(),name="create-url",),
    path("list/",URLListAPIView.as_view(),name="url-list",),
    path("<uuid:url_id>/",URLRetrieveAPIView.as_view(),name="url-retrieve",),
]