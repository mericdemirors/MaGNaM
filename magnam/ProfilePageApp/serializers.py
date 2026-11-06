from rest_framework import serializers
from .models import *
from django.contrib.auth.models import User
from MangaPageApp.models import Manga, Chapter
from PortfolioPageApp.models import Portfolio

from utils.file_checks import image_check
from utils.helper_validators import *
from .globals import *
from magnam.storage import file_storage


def build_image_url(obj, request):
    return (
        request.build_absolute_uri(file_storage.url(obj.image.name))
        if obj.image and request
        else None
    )


class ReturnMangaReferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Manga
        fields = ("id", "title", "image")


class ReturnChapterReferenceSerializer(serializers.ModelSerializer):
    manga_title = serializers.CharField(source="manga.title", read_only=True)

    class Meta:
        model = Chapter
        fields = ("id", "title", "no", "manga", "manga_title")


class ReturnPortfolioReferenceSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Portfolio
        fields = ("id", "title", "image")

    def get_image(self, obj):
        return build_image_url(obj, self.context.get("request"))


class ReturnProfileReferenceSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = ("id", "profile_name", "image")

    def get_image(self, obj):
        return build_image_url(obj, self.context.get("request"))


class ReturnFollowedProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ("id", "profile_name")


class ReturnMessagingProfileSerializer(serializers.ModelSerializer):
    unread_messages = serializers.IntegerField(read_only=True)

    class Meta:
        model = Profile
        fields = ("id", "profile_name", "image", "unread_messages")

    def get_image(self, obj):
        return build_image_url(obj, self.context.get("request"))


class ReturnUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email")


class ReturnProfileSerializer(serializers.ModelSerializer):
    user = ReturnUserSerializer(read_only=True)
    image = serializers.SerializerMethodField()
    mangas_owned = ReturnMangaReferenceSerializer(many=True, read_only=True)
    mangas_collaborated = ReturnMangaReferenceSerializer(many=True, read_only=True)
    chapters_owned = ReturnChapterReferenceSerializer(many=True, read_only=True)
    chapters_collaborated = ReturnChapterReferenceSerializer(many=True, read_only=True)
    portfolios = ReturnPortfolioReferenceSerializer(many=True, read_only=True)
    profiles_following = ReturnProfileReferenceSerializer(many=True, read_only=True)
    profiles_blocked = ReturnProfileReferenceSerializer(many=True, read_only=True)
    mangas_following = ReturnMangaReferenceSerializer(many=True, read_only=True)

    class Meta:
        model = Profile
        fields = (
            "user",
            "id",
            "profile_name",
            "image",
            "wallet",
            "open_date",
            "mangas_owned",
            "mangas_collaborated",
            "chapters_owned",
            "chapters_collaborated",
            "portfolios",
            "profiles_following",
            "profiles_blocked",
            "mangas_following",
        )

    def get_image(self, obj):
        return build_image_url(obj, self.context.get("request"))


class ReturnNonOwnerProfileSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    mangas_owned = ReturnMangaReferenceSerializer(many=True, read_only=True)
    mangas_collaborated = ReturnMangaReferenceSerializer(many=True, read_only=True)
    chapters_owned = ReturnChapterReferenceSerializer(many=True, read_only=True)
    chapters_collaborated = ReturnChapterReferenceSerializer(many=True, read_only=True)
    portfolios = ReturnPortfolioReferenceSerializer(many=True, read_only=True)

    class Meta:
        model = Profile
        fields = (
            "id",
            "profile_name",
            "image",
            "open_date",
            "mangas_owned",
            "mangas_collaborated",
            "chapters_owned",
            "chapters_collaborated",
            "portfolios",
        )

    def get_image(self, obj):
        return build_image_url(obj, self.context.get("request"))


class EditProfileSerializer(serializers.ModelSerializer):
    profile_name = serializers.CharField(
        validators=[
            validate_text(
                "profile_name",
                min_len=PROFILE_MIN_NAME_LEN,
                max_len=PROFILE_MAX_NAME_LEN,
            )
        ]
    )
    image = serializers.ImageField(
        validators=[
            validate_image(
                min_w=PROFILE_IMAGE_MIN_W,
                max_w=PROFILE_IMAGE_MAX_W,
                min_h=PROFILE_IMAGE_MIN_H,
                max_h=PROFILE_IMAGE_MAX_H,
                max_file_size=PROFILE_IMAGE_MAX_SIZE,
            )
        ]
    )
    email = serializers.EmailField(
        validators=[
            validate_text(
                "email", min_len=PROFILE_MIN_EMAIL_LEN, max_len=PROFILE_MAX_EMAIL_LEN
            )
        ]
    )
    password = serializers.CharField(
        write_only=True,
        validators=[
            validate_text(
                "password",
                min_len=PROFILE_MIN_PASSWORD_LEN,
                max_len=PROFILE_MAX_PASSWORD_LEN,
            )
        ],
    )

    class Meta:
        model = Profile
        fields = ("profile_name", "email", "password", "image")

    def validate_profile_name(self, value):
        if Profile.objects.filter(profile_name=value).exists():
            raise serializers.ValidationError("Profile name is already in use")
        return value

    def validate_email(self, value):
        if "@" not in value:
            raise serializers.ValidationError("Email must contain '@'")
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email is already in use")
        return value


class ReturnProfileMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfileMessage
        fields = ("id", "sender", "receiver", "message", "timestamp", "is_read")


class CreateProfileMessageSerializer(serializers.ModelSerializer):
    message = serializers.CharField(
        validators=[
            validate_text(
                "message",
                min_len=PROFILE_MESSAGE_MIN_LEN,
                max_len=PROFILE_MESSAGE_MAX_LEN,
            )
        ]
    )

    class Meta:
        model = ProfileMessage
        fields = ["message"]

    def validate(self, data):
        sender = self.context["sender"]
        receiver = self.context["receiver"]

        if sender == receiver:
            raise serializers.ValidationError(
                {"message": "Sender and receiver cannot be the same."}
            )

        # Check following relationships:
        # sender must follow receiver
        # sender must not be blocked by receiver
        # receiver must not be blocked by sender (should be covered by the toggling logic, still double check)
        if not sender.profiles_following.filter(id=receiver.id).exists():
            raise serializers.ValidationError(
                {
                    "message": "You cannot send messages to profiles you are not following."
                }
            )
        if sender.profiles_blocked.filter(id=receiver.id).exists():
            raise serializers.ValidationError(
                {"message": "You cannot send messages to profiles you blocked."}
            )
        if sender.blocked_by.filter(id=receiver.id).exists():
            raise serializers.ValidationError(
                {"message": "You cannot send messages to profiles you are blocked by."}
            )

        return data

    def create(self, validated_data):
        sender = self.context["sender"]
        receiver = self.context["receiver"]

        return ProfileMessage.objects.create(
            sender=sender, receiver=receiver, **validated_data
        )
