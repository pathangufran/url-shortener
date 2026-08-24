from django.urls import path

from .views import (
    CreateURLAPIView,
    URLDeleteAPIView,
    URLListAPIView,
    URLQRCodeAPIView,
    URLRetrieveAPIView,
    URLUpdateAPIView,
)

app_name = "shortener"

urlpatterns = [
    path(
        "",
        CreateURLAPIView.as_view(),
        name="create-url",
    ),
    path(
        "list/",
        URLListAPIView.as_view(),
        name="url-list",
    ),
    path(
        "<uuid:url_id>/",
        URLRetrieveAPIView.as_view(),
        name="url-retrieve",
    ),
    path(
        "<uuid:url_id>/update/",
        URLUpdateAPIView.as_view(),
        name="url-update",
    ),
    path(
        "<uuid:url_id>/delete/",
        URLDeleteAPIView.as_view(),
        name="url-delete",
    ),
    path(
        "<uuid:url_id>/qr-code/",
        URLQRCodeAPIView.as_view(),
        name="url-qr-code",
    ),
]
