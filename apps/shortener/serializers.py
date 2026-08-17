from django.utils import timezone
from rest_framework import serializers
from .models import URL
import re

class CreateURLSerializer(serializers.ModelSerializer):
    """
    Serializer for creating shortened URLs.
    """
    custom_alias = serializers.CharField(
        required=False,
        allow_blank=False,
        trim_whitespace=True,
        write_only=True,
    )
    class Meta:
        model = URL
        fields = ["long_url","expires_at","custom_alias",]

    def validate_expires_at(self,value):
        if value <= timezone.now():
            raise serializers.ValidationError(
                "Expiration time must be in the future."
            )

        return value

    def validate_custom_alias(self,value):
        value = value.strip().lower()
        if not re.fullmatch(r"[a-z0-9_-]{3,50}",value,):
            raise serializers.ValidationError(
                "Custom alias must contain only "
                "letters, numbers, hyphens, or underscores "
                "and must be between 3 and 50 characters."
            )
        reserved_aliases = {
            "admin",
            "api",
            "login",
            "logout",
            "register",
            "refresh",
            "health",
            "swagger",
            "docs",
            "static",
            "media",
            "favicon",
        }
        if value in reserved_aliases:
            raise serializers.ValidationError(
                "This alias is reserved and cannot be used."
            )
        if URL.objects.filter(short_code=value).exists():
            raise serializers.ValidationError(
                "This custom alias is already in use."
            )
        return value


class UpdateURLSerializer(serializers.Serializer):
    long_url = serializers.URLField()
    expires_at = serializers.DateTimeField(
        required=False,
        allow_null=True,
    )
    is_active = serializers.BooleanField(required=False,)

    def validate(self,attrs):
        if not attrs:
            raise serializers.ValidationError(
                "At least one field is required for update."
            )

        return attrs
    

class URLResponseSerializer(serializers.ModelSerializer):
    short_url = serializers.SerializerMethodField()

    class Meta:
        model = URL
        fields = (
            "id",
            "long_url",
            "short_code",
            "short_url",
            "is_active",
            "expires_at",
            "created_at",
        )

    def get_short_url(self,obj):
        request = self.context.get("request")

        if request:
            return request.build_absolute_uri(f"/{obj.short_code}")

        return obj.short_code