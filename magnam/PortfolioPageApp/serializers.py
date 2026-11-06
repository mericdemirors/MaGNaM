from pathlib import Path, PurePosixPath

from ProfilePageApp.models import Profile
from rest_framework import serializers
from .models import *

from utils.file_checks import *
from utils.helper_validators import *
from magnam.storage import file_storage


def build_image_url(obj, request):
    return (
        request.build_absolute_uri(file_storage.url(obj.image.name))
        if obj.image and request
        else None
    )


def build_file_url(obj, request):
    return (
        request.build_absolute_uri(file_storage.url(obj.work_file.name))
        if obj.work_file and request
        else None
    )


def build_work_pages_base_url(work, request):
    url = directory_storage.url(
        PurePosixPath(get_work_upload_folder_path(work), "pages").as_posix()
    )
    return request.build_absolute_uri(url) if request else None


# === Profile === # === Profile === # === Profile === # === Profile === #


class ReturnPortfolioOwnerReferenceSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = ("id", "profile_name", "image")

    def get_image(self, obj):
        return build_image_url(obj, self.context.get("request"))


# === Work === # === Work === # === Work === # === Work === #


class ReturnWorkSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    pages_base_url = (
        serializers.SerializerMethodField()
    )  # only meaningfull if work is a pdf

    class Meta:
        model = Work
        fields = (
            "id",
            "portfolio",
            "title",
            "file_url",
            "folder_name",  # only meaningfull if work is a pdf
            "num_of_images",  # only meaningfull if work is a pdf
            "pages_base_url",  # only meaningfull if work is a pdf
            "is_pdf",
        )

    def get_file_url(self, obj):
        request = self.context.get("request")
        return build_file_url(obj, request)

    def get_folder_name(self, obj):
        return obj.folder_name if self.is_pdf else None

    def get_pages_base_url(self, obj):
        request = self.context.get("request")
        return build_work_pages_base_url(obj, request) if obj.is_pdf else None


class CreateWorkSerializer(serializers.ModelSerializer):
    title = serializers.CharField(
        allow_blank=True,
        validators=[
            validate_text(
                "title", min_len=WORK_MIN_TITLE_LEN, max_len=WORK_MAX_TITLE_LEN
            )
        ],
    )

    # no validator for this, we do work_files validation in the view
    work_files = serializers.ListField(child=serializers.FileField(), allow_empty=False)
    # We allow multiple work submits at once so we cant actually validate them here and return error preliminary
    # we want to process the files and see if there are few of them that we can process, and we throw errors only to failing ones

    class Meta:
        model = Work
        fields = ("title", "work_files")


# === Portfolio === # === Portfolio === # === Portfolio === # === Portfolio === #


class ReturnPortfolioTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortfolioTag
        fields = ("id", "label")


class ReturnPortfolioLikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortfolioLike
        fields = ("id", "portfolio", "profile")


class ReturnPortfolioCommentSerializer(serializers.ModelSerializer):
    profile_name = serializers.ReadOnlyField(source="profile.profile_name")
    parent_comment_id = serializers.PrimaryKeyRelatedField(
        source="parent_comment", read_only=True, allow_null=True
    )

    class Meta:
        model = PortfolioComment
        fields = ("id", "profile_name", "comment", "parent_comment_id")


class ReturnPortfolioSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    works = ReturnWorkSerializer(many=True, read_only=True)
    tags = ReturnPortfolioTagSerializer(many=True, read_only=True)
    owner = ReturnPortfolioOwnerReferenceSerializer(many=False, read_only=True)

    class Meta:
        model = Portfolio
        fields = (
            "id",
            "title",
            "description",
            "image",
            "owner",
            "date",
            "folder_name",
            "tags",
            "works",
        )

    def get_image(self, obj):
        return build_image_url(obj, self.context.get("request"))


class ReturnPortfolioGallerySerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    tags = ReturnPortfolioTagSerializer(many=True, read_only=True)
    num_of_likes = serializers.IntegerField(read_only=True)
    num_of_works = serializers.IntegerField(read_only=True)

    class Meta:
        model = Portfolio
        fields = (
            "id",
            "title",
            "image",
            "date",
            "tags",
            "num_of_likes",
            "num_of_works",
        )

    def get_image(self, obj):
        return build_image_url(obj, self.context.get("request"))


class CreateEditPortfolioSerializer(serializers.ModelSerializer):
    title = serializers.CharField(
        validators=[
            validate_text(
                "title",
                min_len=PORTFOLIO_MIN_TITLE_LEN,
                max_len=PORTFOLIO_MAX_TITLE_LEN,
            )
        ]
    )

    description = serializers.CharField(
        allow_blank=True,
        validators=[
            validate_text(
                "description",
                min_len=PORTFOLIO_MIN_DESCRIPTION_LEN,
                max_len=PORTFOLIO_MAX_DESCRIPTION_LEN,
            )
        ],
    )

    image = serializers.ImageField(
        validators=[
            validate_image(
                min_w=PORTFOLIO_IMAGE_MIN_W,
                max_w=PORTFOLIO_IMAGE_MAX_W,
                min_h=PORTFOLIO_IMAGE_MIN_H,
                max_h=PORTFOLIO_IMAGE_MAX_H,
                max_file_size=PORTFOLIO_IMAGE_MAX_SIZE,
            )
        ]
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=PortfolioTag.objects.all(),
        many=True,
        allow_empty=True,
        validators=[
            validate_pk_relation(
                "tags",
                min_count=PORTFOLIO_MIN_TAG_COUNT,
                max_count=PORTFOLIO_MAX_TAG_COUNT,
            )
        ],
    )

    class Meta:
        model = Portfolio
        fields = ("title", "description", "image", "tags")

    def validate(self, data):
        if self.instance is None:
            profile = self.context.get("request").user.profile
            if profile.portfolios.count() >= MAX_PORTFOLIO_COUNT_PER_PROFILE:
                raise serializers.ValidationError(
                    {
                        "limit": f"Each user can have at most {MAX_PORTFOLIO_COUNT_PER_PROFILE} portfolios."
                    }
                )

        return data

    def create(self, validated_data):
        tags = validated_data.pop("tags", [])

        img = validated_data["image"]
        img.name = f"{uuid.uuid4().hex}{PurePosixPath(img.name).suffix}"

        portfolio = Portfolio.objects.create(**validated_data)
        portfolio.tags.set(tags)
        return portfolio

    def update(self, instance, validated_data):
        tags = validated_data.pop("tags", None)

        for attr, value in validated_data.items():
            if attr == "image":
                value.name = f"{uuid.uuid4().hex}{PurePosixPath(value.name).suffix}"
                instance.image.delete(save=False)
            setattr(instance, attr, value)

        if tags:
            instance.tags.set(tags)

        instance.save()
        return instance


class CreatePortfolioCommentSerializer(serializers.ModelSerializer):
    comment = serializers.CharField(
        validators=[
            validate_text(
                "comment",
                min_len=PORTFOLIO_MIN_COMMENT_LEN,
                max_len=PORTFOLIO_MAX_COMMENT_LEN,
            )
        ]
    )
    parent_comment_id = serializers.IntegerField()

    class Meta:
        model = PortfolioComment
        fields = ("parent_comment_id", "comment")

    def validate(self, data):
        # -1 means no parent comment
        parent_comment_id = data.get("parent_comment_id", -1)
        if parent_comment_id != -1:
            parent_comment = PortfolioComment.objects.filter(
                id=parent_comment_id
            ).first()

            if not parent_comment:
                raise serializers.ValidationError(
                    {"parent_comment_id": "Parent comment not found."}
                )

            current_portfolio = self.context.get("portfolio")
            if parent_comment.portfolio != current_portfolio:
                raise serializers.ValidationError(
                    {
                        "parent_comment_id": "You cant reply to to a comment from another portfolio."
                    }
                )

            # put it into validated_data
            data["parent_comment"] = parent_comment

        return data

    def create(self, validated_data):
        portfolio = self.context["portfolio"]
        profile = self.context["profile"]

        # Pop the object directly (will be None if not passed/doesn't exist)
        parent_comment = validated_data.get("parent_comment", None)
        comment = validated_data.get("comment")

        return PortfolioComment.objects.create(
            portfolio=portfolio,
            profile=profile,
            parent_comment=parent_comment,
            comment=comment,
        )
