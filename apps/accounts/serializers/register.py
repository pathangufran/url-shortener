from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()

class RegisterSerializer(serializers.Serializer):

    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        style={"input_type": "password"},
    )

    def validate_email(self,value):
        email = value.lower().strip()

        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                "A user with this email already exists."
            )

        return email

