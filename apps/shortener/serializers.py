from django.utils import timezone
from rest_framework import serializers
from .models import URL

class CreateURLSerializer(serializers.Serializer):
    long_url = serializers.URLField()
    expires_at = serializers.DateTimeField(
        required=False,
        allow_null=True,
    )

    def validate_expires_at(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError(
                "Expiration time must be in the future."
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