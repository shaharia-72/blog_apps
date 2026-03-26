from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class AdminTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        user: User = self.user
        if not user.is_staff:
            raise serializers.ValidationError("Admin access required.")

        data["user"] = {
            "id": user.id,
            "name": user.get_full_name() or user.username,
            "email": user.email,
        }

        return data


class AuthorSerializer(serializers.ModelSerializer):
    """
    Lightweight public author info shown on blog cards and post pages.
    Never exposes password, email, or internal fields.
    """

    full_name = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    github_url = serializers.CharField(read_only=True)
    linkedin_url = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            "full_name",
            "bio",
            "avatar_url",
            "website",
            "github_url",
            "linkedin_url",
            "skills",
        ]

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username

    def get_avatar_url(self, obj):
        request = self.context.get("request")
        if obj.avatar and request:
            return request.build_absolute_uri(obj.avatar.url)
        return None


class AdminProfileSerializer(serializers.ModelSerializer):
    """Admin profile — includes editable private fields."""

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "bio",
            "avatar",
            "website",
            "twitter_username",
            "linkedin_username",
            "github_username",
            "skills",
        ]
        read_only_fields = ["id", "username", "email"]
