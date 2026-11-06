from pathlib import PurePosixPath
import uuid
from rest_framework import serializers
from .models import News

from utils.helper_validators import *

from .globals import *
from magnam.storage import file_storage


class ReturnNewsSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = News
        fields = ("id", "title", "description", "image", "links")

    def get_image(self, obj):
        request = self.context.get("request")
        if obj.image and request:
            return request.build_absolute_uri(file_storage.url(obj.image.name))
        return None


class CreateEditNewsSerializer(serializers.ModelSerializer):
    title = serializers.CharField(
        validators=[
            validate_text(
                "title", min_len=NEWS_MIN_TITLE_LEN, max_len=NEWS_MAX_TITLE_LEN
            )
        ]
    )

    description = serializers.CharField(
        allow_blank=True,
        validators=[
            validate_text(
                "description",
                min_len=NEWS_MIN_DESCRIPTION_LEN,
                max_len=NEWS_MAX_DESCRIPTION_LEN,
            )
        ],
    )

    image = serializers.ImageField(
        validators=[
            validate_image(
                min_w=NEWS_IMAGE_MIN_W,
                max_w=NEWS_IMAGE_MAX_W,
                min_h=NEWS_IMAGE_MIN_H,
                max_h=NEWS_IMAGE_MAX_H,
                max_file_size=NEWS_IMAGE_MAX_SIZE,
            )
        ]
    )

    links = serializers.JSONField(
        validators=[
            validate_links(
                "links", min_len=NEWS_MIN_LINKS_LEN, max_len=NEWS_MAX_LINKS_LEN
            )
        ]
    )

    class Meta:
        model = News
        fields = ("title", "description", "image", "links")

    def validate_links(self, value):
        return [link.strip() for link in value if len(link.strip())]

    def create(self, validated_data):
        img = validated_data["image"]
        img.name = f"{uuid.uuid4().hex}{PurePosixPath(img.name).suffix}"

        news = News.objects.create(**validated_data)
        return news

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            if attr == "image":
                value.name = f"{uuid.uuid4().hex}{PurePosixPath(value.name).suffix}"
                instance.image.delete(save=False)
            setattr(instance, attr, value)
        instance.save()
        return instance
