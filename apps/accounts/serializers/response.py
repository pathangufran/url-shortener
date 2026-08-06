from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class UserResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = User

        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "created_at",
        )

        read_only_fields = fields