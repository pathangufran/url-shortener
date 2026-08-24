from .models import URL
from django.contrib import admin

@admin.register(URL)
class URLAdmin(admin.ModelAdmin):
    list_display = (
        "short_code",
        "user",
        "is_active",
        "expires_at",
        "created_at",
    )

    search_fields = (
        "short_code",
        "long_url",
        "user__email",
    )

    list_filter = ("is_active",)

    ordering = ("-created_at",)
