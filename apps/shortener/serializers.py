from rest_framework import serializers
from .models import URL

class CreateURLSerializer(serializers.Serializer):
    long_url = serializers.URLField()
    expires_at = serializers.DateTimeField(
        required=False,
        allow_null=True,
    )

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