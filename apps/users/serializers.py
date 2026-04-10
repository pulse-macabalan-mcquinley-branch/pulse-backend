from django.contrib.auth import password_validation
from rest_framework import serializers

from .models import CustomUser


class UserSerializer(serializers.ModelSerializer):
    """Read-only user representation — used in list/detail endpoints."""

    full_name = serializers.SerializerMethodField()

    class Meta:
        model  = CustomUser
        fields = [
            "id", "email", "first_name", "last_name", "full_name",
            "role", "avatar_url", "is_active", "date_joined",
        ]
        read_only_fields = ["id", "email", "date_joined"]

    def get_full_name(self, obj):
        return obj.full_name


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Used by Djoser for registration.
    Password confirmation is handled by Djoser
    when USER_CREATE_PASSWORD_RETYPE=True.
    """

    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model  = CustomUser
        fields = ["email", "first_name", "last_name", "password"]

    def validate_password(self, value):
        password_validation.validate_password(value)
        return value

    def create(self, validated_data):
        return CustomUser.objects.create_user(**validated_data)


class UserUpdateSerializer(serializers.ModelSerializer):
    """Partial profile update — email and role are not changeable here."""

    class Meta:
        model  = CustomUser
        fields = ["first_name", "last_name", "avatar_url"]

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class ChangePasswordSerializer(serializers.Serializer):
    """Change password with old-password verification."""

    old_password     = serializers.CharField(required=True, write_only=True)
    new_password     = serializers.CharField(required=True, write_only=True, min_length=8)
    confirm_password = serializers.CharField(required=True, write_only=True)

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate(self, data):
        if data["new_password"] != data["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "Passwords do not match."}
            )
        password_validation.validate_password(data["new_password"])
        return data

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        return user


class AdminUserRoleSerializer(serializers.ModelSerializer):
    """Admin-only serializer to change a user's role."""

    class Meta:
        model  = CustomUser
        fields = ["role", "is_active", "is_staff"]