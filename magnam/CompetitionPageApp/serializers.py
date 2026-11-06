from pathlib import PurePosixPath
import uuid

from rest_framework import serializers
from .models import *
from django.utils import timezone
from MangaPageApp.models import Chapter
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


# === CHAPTER REFERENCE === #


class ReturnCompetitionChapterSerializer(serializers.ModelSerializer):
    manga_id = serializers.IntegerField(source="manga.id")
    manga_image = serializers.ImageField(source="manga.image")
    manga_title = serializers.CharField(source="manga.title")

    class Meta:
        model = Chapter
        fields = ["id", "title", "no", "manga_id", "manga_title", "manga_image"]

    def get_manga_image(self, obj):
        return build_image_url(obj.manga, self.context.get("request"))


# === PORTFOLIO REFERENCE === #


class ReturnCompetitionPortfolioSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Portfolio
        fields = ("id", "title", "image")

    def get_image(self, obj):
        return build_image_url(obj, self.context.get("request"))


# === TAGS === #


class ReturnCompetitionTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompetitionTag
        fields = ("id", "label")


# === COMPETITION === #


class ReturnCompetitionSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    tags = ReturnCompetitionTagSerializer(many=True, read_only=True)

    chapter_submits = ReturnCompetitionChapterSerializer(many=True, read_only=True)
    portfolio_submits = ReturnCompetitionPortfolioSerializer(many=True, read_only=True)

    chapter_wins = ReturnCompetitionChapterSerializer(many=True, read_only=True)
    portfolio_wins = ReturnCompetitionPortfolioSerializer(many=True, read_only=True)

    class Meta:
        model = Competition
        fields = (
            "id",
            "title",
            "description",
            "image",
            "links",
            "start_date",
            "price",
            "end_date",
            "tags",
            "chapter_submits",
            "portfolio_submits",
            "chapter_wins",
            "portfolio_wins",
        )

    def get_image(self, obj):
        return build_image_url(obj, self.context.get("request"))


class CreateEditCompetitionSerializer(serializers.ModelSerializer):
    title = serializers.CharField(
        validators=[
            validate_text(
                "title",
                min_len=COMPETITION_MIN_TITLE_LEN,
                max_len=COMPETITION_MAX_TITLE_LEN,
            )
        ]
    )
    description = serializers.CharField(
        validators=[
            validate_text(
                "description",
                min_len=COMPETITION_MIN_DESCRIPTION_LEN,
                max_len=COMPETITION_MAX_DESCRIPTION_LEN,
            )
        ]
    )
    image = serializers.ImageField(
        validators=[
            validate_image(
                min_w=COMPETITION_IMAGE_MIN_W,
                max_w=COMPETITION_IMAGE_MAX_W,
                min_h=COMPETITION_IMAGE_MIN_H,
                max_h=COMPETITION_IMAGE_MAX_H,
                max_file_size=COMPETITION_IMAGE_MAX_SIZE,
            )
        ]
    )
    links = serializers.JSONField(
        validators=[
            validate_links(
                "links",
                min_len=COMPETITION_MIN_LINKS_LEN,
                max_len=COMPETITION_MAX_LINKS_LEN,
            )
        ]
    )
    price = serializers.IntegerField(min_value=0)
    start_date = serializers.DateField()
    end_date = serializers.DateField(
        validators=[validate_date(field_name="end date", min_date=timezone.localdate)]
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=CompetitionTag.objects.all(),
        many=True,
        allow_empty=True,
        validators=[
            validate_pk_relation(
                "tags",
                min_count=COMPETITION_MIN_TAG_COUNT,
                max_count=COMPETITION_MAX_TAG_COUNT,
            )
        ],
    )

    class Meta:
        model = Competition
        fields = [
            "title",
            "description",
            "image",
            "links",
            "price",
            "start_date",
            "end_date",
            "tags",
        ]

    def validate_links(self, value):
        return [link.strip() for link in value if len(link.strip())]

    def validate(self, data):
        # Call the parent validation first to ensure field-level validation runs smoothly
        data = super().validate(data)

        # 2. Handle cross-field validation here
        # Using data.get() for incoming data, falling back to self.instance for partial updates (PATCH)
        start_date = data.get("start_date", getattr(self.instance, "start_date", None))
        end_date = data.get("end_date", getattr(self.instance, "end_date", None))

        if start_date and end_date and end_date <= start_date:
            raise serializers.ValidationError(
                {"end_date": "End date must be after the start date."}
            )

        return data

    def create(self, validated_data):
        tags = validated_data.pop("tags", [])

        img = validated_data["image"]
        img.name = f"{uuid.uuid4().hex}{PurePosixPath(img.name).suffix}"

        competition = Competition.objects.create(**validated_data)
        competition.tags.set(tags)
        return competition

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


class ReturnCompetitionGallerySerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    tags = ReturnCompetitionTagSerializer(many=True, read_only=True)
    num_of_portfolio_submits = serializers.IntegerField(read_only=True)
    num_of_chapter_submits = serializers.IntegerField(read_only=True)

    class Meta:
        model = Competition
        fields = [
            "id",
            "image",
            "tags",
            "title",
            "start_date",
            "end_date",
            "price",
            "num_of_portfolio_submits",
            "num_of_chapter_submits",
        ]

    def get_image(self, obj):
        return build_image_url(obj, self.context.get("request"))
