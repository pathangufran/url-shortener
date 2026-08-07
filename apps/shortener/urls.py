from django.urls import path
from .views import CreateURLAPIView

app_name = "shortener"

urlpatterns = [
    path("",CreateURLAPIView.as_view(),name="create-url",),
]