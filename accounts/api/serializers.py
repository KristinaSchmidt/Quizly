from django.contrib.auth.models import User
from rest_framework import serializers


class RegistrationSerializer(serializers.ModelSerializer):
    """Validate registration data and create a Django user."""

    confirmed_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "password", "confirmed_password", "email"]
        extra_kwargs = {"password": {"write_only": True}}

    def validate_email(self, email):
        """Reject an email address that is already registered."""
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("Email is already in use.")
        return email

    def validate(self, attrs):
        """Ensure that both entered passwords match."""
        if attrs["password"] != attrs["confirmed_password"]:
            raise serializers.ValidationError(
                {"confirmed_password": "Passwords do not match."}
            )
        return attrs

    def create(self, validated_data):
        """Create the user with a securely hashed password."""
        validated_data.pop("confirmed_password")
        return User.objects.create_user(**validated_data)