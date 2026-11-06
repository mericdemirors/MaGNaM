import uuid
from natsort import natsorted
from pathlib import Path, PurePosixPath

from ProfilePageApp.models import Profile
from rest_framework import serializers
from .models import *

from utils.file_checks import *
from utils.helper_validators import *
from utils.permission import has_permission

from .globals import *
from magnam.storage import file_storage


def build_image_url(obj, request):
    return (
        request.build_absolute_uri(file_storage.url(obj.image.name))
        if obj.image and request
        else None
    )


def build_chapter_pdf_url(obj, request):
    return (
        request.build_absolute_uri(file_storage.url(obj.pdf.name))
        if obj.pdf and request
        else None
    )


def build_chapter_pages_base_url(chapter, request):
    url = directory_storage.url(
        PurePosixPath(get_chapter_upload_folder_path(chapter), "pages").as_posix()
    )
    return request.build_absolute_uri(url) if request else None


def get_manga_bookmark(manga, request):
    if not has_permission(request.user, "logged_in"):
        return None

    bookmark = (
        MangaBookmark.objects.select_related("chapter")
        .filter(manga=manga, profile=request.user.profile)
        .first()
    )

    if not bookmark:
        return None

    return {"chapter_id": bookmark.chapter.id, "page": bookmark.page}


# === Profile === # === Profile === # === Profile === # === Profile === #


class ReturnChapterMangaOwnerCollaboratorsReferenceSerializer(
    serializers.ModelSerializer
):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = ("id", "profile_name", "image")

    def get_image(self, obj):
        return build_image_url(obj, self.context.get("request"))


# === Chapter === # === Chapter === # === Chapter === # === Chapter === #


class ReturnChapterSerializer(serializers.ModelSerializer):
    owner = ReturnChapterMangaOwnerCollaboratorsReferenceSerializer(
        many=False, read_only=True
    )
    collaborators = ReturnChapterMangaOwnerCollaboratorsReferenceSerializer(
        many=True, read_only=True
    )
    pdf = serializers.SerializerMethodField()
    folder_name = serializers.SerializerMethodField()
    is_user_bought = serializers.SerializerMethodField()
    is_user_read = serializers.SerializerMethodField()
    pages_base_url = serializers.SerializerMethodField()

    class Meta:
        model = Chapter
        fields = (
            "id",
            "title",
            "no",
            "manga",
            "owner",
            "collaborators",
            "publish_date",
            "price",
            "pdf",
            "folder_name",
            "num_of_images",
            "pages_base_url",
            "is_user_bought",
            "is_user_read",
        )

    def get_is_user_read(self, obj):
        request = self.context.get("request")
        is_read = (
            has_permission(request.user, "logged_in")
            and ReadChapter.objects.filter(
                chapter=obj, profile=request.user.profile
            ).exists()
        )

        return is_read

    def get_is_user_bought(self, obj):
        if hasattr(obj, "_is_bought"):
            return obj._is_bought

        request = self.context.get("request")
        is_bought = False

        is_bought = (
            has_permission(request.user, "logged_in")
            and BoughtChapter.objects.filter(
                chapter=obj, profile=request.user.profile
            ).exists()
        )

        obj._is_bought = is_bought
        return is_bought

    def get_folder_name(self, obj):
        return obj.folder_name if self.get_is_user_bought(obj) else None

    def get_pages_base_url(self, obj):
        request = self.context.get("request")
        return (
            build_chapter_pages_base_url(obj, request)
            if self.get_is_user_bought(obj)
            else None
        )

    def get_pdf(self, obj):
        request = self.context.get("request")
        return (
            build_chapter_pdf_url(obj, request)
            if self.get_is_user_bought(obj)
            else None
        )


class CreateEditChapterSerializer(serializers.ModelSerializer):
    title = serializers.CharField(
        validators=[
            validate_text(
                "title", min_len=CHAPTER_MIN_TITLE_LEN, max_len=CHAPTER_MAX_TITLE_LEN
            )
        ]
    )
    no = serializers.CharField(
        validators=[
            validate_text("no", min_len=CHAPTER_MIN_NO_LEN, max_len=CHAPTER_MAX_NO_LEN)
        ]
    )
    collaborators = serializers.PrimaryKeyRelatedField(
        queryset=Profile.objects.all(),
        many=True,
        allow_empty=True,
        validators=[
            validate_pk_relation(
                "collaborators",
                min_count=CHAPTER_MIN_COLLABORATOR_COUNT,
                max_count=CHAPTER_MAX_COLLABORATOR_COUNT,
            )
        ],
    )

    price = serializers.IntegerField(min_value=0)
    pdf = serializers.FileField(
        validators=[
            validate_pdf(
                max_file_size=CHAPTER_PDF_MAX_SIZE, max_pages=CHAPTER_PDF_MAX_PAGE
            )
        ]
    )

    class Meta:
        model = Chapter
        fields = ("title", "no", "collaborators", "price", "pdf")

    def validate(self, data):
        if self.instance is None:
            manga = self.context.get("manga")
            if manga.chapters.count() >= MAX_CHAPTER_COUNT_PER_MANGA:
                raise serializers.ValidationError(
                    {
                        "limit": f"Each manga can have at most {MAX_CHAPTER_COUNT_PER_MANGA} chapters."
                    }
                )

        unique_manga_no_pair_check = Chapter.objects.filter(
            manga=self.context["manga"], no=data.get("no")
        )
        if self.instance:
            unique_manga_no_pair_check = unique_manga_no_pair_check.exclude(
                id=self.instance.id
            )
        if unique_manga_no_pair_check.exists():
            raise serializers.ValidationError(
                {"no": "Chapter no {no} already exists for this manga."}
            )

        collaborators = data.get("collaborators", [])
        owner = self.context["owner"]
        if owner in collaborators:
            raise serializers.ValidationError(
                {"collaborators": "Owner cant be collaborator."}
            )
        return data

    def create(self, validated_data):
        collaborators = validated_data.pop("collaborators", [])

        validated_data["manga"] = self.context["manga"]
        validated_data["owner"] = self.context["owner"]

        chapter = Chapter.objects.create(**validated_data)
        chapter.collaborators.set(collaborators)
        return chapter

    def update(self, instance, validated_data):
        collaborators = validated_data.pop("collaborators", [])

        for attr, value in validated_data.items():
            if attr == "pdf":
                instance.pdf.delete(save=False)
                # this delete will trigger ._pdf_changed check
                # that will trigger process_pdf_task
                # that will handle the clearing and creating pdf folder
            setattr(instance, attr, value)

        if collaborators:
            instance.collaborators.set(collaborators)

        instance.save()
        return instance


# === Manga === # === Manga === # === Manga === # === Manga === #


class ReturnMangaTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = MangaTag
        fields = ("id", "label")


class ReturnMangaRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = MangaRating
        fields = ("id", "manga", "profile", "score")


class ReturnMangaCommentSerializer(serializers.ModelSerializer):
    profile_name = serializers.ReadOnlyField(source="profile.profile_name")
    parent_comment_id = serializers.PrimaryKeyRelatedField(
        source="parent_comment", read_only=True, allow_null=True
    )

    class Meta:
        model = MangaComment
        fields = ("id", "profile_name", "comment", "parent_comment_id")


class ReturnMangaSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    chapters = ReturnChapterSerializer(many=True, read_only=True)
    tags = ReturnMangaTagSerializer(many=True, read_only=True)
    owner = ReturnChapterMangaOwnerCollaboratorsReferenceSerializer(
        many=False, read_only=True
    )
    collaborators = ReturnChapterMangaOwnerCollaboratorsReferenceSerializer(
        many=True, read_only=True
    )
    bookmark = serializers.SerializerMethodField()

    class Meta:
        model = Manga
        fields = (
            "id",
            "title",
            "description",
            "image",
            "owner",
            "collaborators",
            "folder_name",
            "start_date",
            "last_update_date",
            "tags",
            "chapters",
            "bookmark",
        )

    def get_bookmark(self, obj):
        request = self.context.get("request")
        return get_manga_bookmark(obj, request)

    def get_image(self, obj):
        return build_image_url(obj, self.context.get("request"))

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["chapters"] = natsorted(
            data["chapters"], key=lambda c: c["no"], reverse=True
        )
        return data


class ReturnTextSearchMangaSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    owner = ReturnChapterMangaOwnerCollaboratorsReferenceSerializer(
        many=False, read_only=True
    )
    tags = ReturnMangaTagSerializer(many=True, read_only=True)

    # Fields to be added during view annotation
    rating = serializers.FloatField(read_only=True)
    num_of_chapters = serializers.IntegerField(read_only=True)

    class Meta:
        model = Manga
        fields = ("id", "title", "image", "owner", "tags", "rating", "num_of_chapters")

    def get_image(self, obj):
        return build_image_url(obj, self.context.get("request"))


class ReturnReadMangaSerializer(serializers.ModelSerializer):
    chapters = ReturnChapterSerializer(many=True, read_only=True)
    bookmark = serializers.SerializerMethodField()

    class Meta:
        model = Manga
        fields = ("id", "folder_name", "chapters", "bookmark")

    def get_bookmark(self, obj):
        request = self.context.get("request")
        return get_manga_bookmark(obj, request)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["chapters"] = natsorted(
            data["chapters"], key=lambda c: c["no"], reverse=True
        )
        return data


class ReturnMangaGallerySerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    tags = ReturnMangaTagSerializer(many=True, read_only=True)
    rating = serializers.FloatField(read_only=True)
    num_of_ratings = serializers.IntegerField(read_only=True)
    num_of_chapters = serializers.IntegerField(read_only=True)
    num_of_collaborators = serializers.IntegerField(read_only=True)
    num_of_followers = serializers.IntegerField(read_only=True)
    total_price_of_all_chapters = serializers.IntegerField(read_only=True)

    class Meta:
        model = Manga
        fields = (
            "id",
            "title",
            "image",
            "start_date",
            "last_update_date",
            "tags",
            "rating",
            "num_of_ratings",
            "num_of_chapters",
            "num_of_collaborators",
            "num_of_followers",
            "total_price_of_all_chapters",
        )

    def get_image(self, obj):
        return build_image_url(obj, self.context.get("request"))


class CreateEditMangaSerializer(serializers.ModelSerializer):
    title = serializers.CharField(
        validators=[
            validate_text(
                "title", min_len=MANGA_MIN_TITLE_LEN, max_len=MANGA_MAX_TITLE_LEN
            )
        ]
    )

    description = serializers.CharField(
        validators=[
            validate_text(
                "description",
                min_len=MANGA_MIN_DESCRIPTION_LEN,
                max_len=MANGA_MAX_DESCRIPTION_LEN,
            )
        ]
    )

    image = serializers.ImageField(
        validators=[
            validate_image(
                min_w=MANGA_IMAGE_MIN_W,
                max_w=MANGA_IMAGE_MAX_W,
                min_h=MANGA_IMAGE_MIN_H,
                max_h=MANGA_IMAGE_MAX_H,
                max_file_size=MANGA_IMAGE_MAX_SIZE,
            )
        ]
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=MangaTag.objects.all(),
        many=True,
        allow_empty=False,
        validators=[
            validate_pk_relation(
                "tags", min_count=MANGA_MIN_TAG_COUNT, max_count=MANGA_MAX_TAG_COUNT
            )
        ],
    )
    collaborators = serializers.PrimaryKeyRelatedField(
        queryset=Profile.objects.all(),
        many=True,
        allow_empty=True,
        validators=[
            validate_pk_relation(
                "collaborators",
                min_count=MANGA_MIN_COLLABORATOR_COUNT,
                max_count=MANGA_MAX_COLLABORATOR_COUNT,
            )
        ],
    )

    class Meta:
        model = Manga
        fields = ("title", "description", "image", "tags", "collaborators")

    def validate(self, data):
        if self.instance is None:
            profile = self.context.get("request").user.profile
            if profile.mangas_owned.count() >= MAX_MANGA_COUNT_PER_PROFILE:
                raise serializers.ValidationError(
                    {
                        "limit": f"Each user can have at most {MAX_MANGA_COUNT_PER_PROFILE} mangas."
                    }
                )

        # these checks need to run only if collaborators and tags are given
        # in creation, these are required so these will run
        # in editing, these can be absent if we are not editing these fields
        # so we need to skip these checks if they are not in the partial patch data
        if "collaborators" in data:
            collaborators = data.get("collaborators")
            owner = self.context["owner"]
            if owner in collaborators:
                raise serializers.ValidationError(
                    {"collaborators": "Owner cant be collaborator."}
                )
        if "tags" in data:
            tag_ids = [t.id for t in data.get("tags")]
            # 1: original tag id, 2: scan/translation tag id,
            # manga cant be both original and a scan/translation
            if (1 in tag_ids) and (2 in tag_ids):
                raise serializers.ValidationError(
                    {"tags": "Manga can't be both original and a scan/translation."}
                )
            # manga must be either original or scan/translation
            elif (1 not in tag_ids) and (2 not in tag_ids):
                raise serializers.ValidationError(
                    {"tags": "Manga must be either original or scan/translation."}
                )

        return data

    def create(self, validated_data):
        tags = validated_data.pop("tags", [])
        collaborators = validated_data.pop("collaborators", [])

        img = validated_data["image"]
        img.name = f"{uuid.uuid4().hex}{PurePosixPath(img.name).suffix}"

        validated_data["is_original"] = 1 in tags  # 1: original tag id

        manga = Manga.objects.create(**validated_data)
        manga.tags.set(tags)
        manga.collaborators.set(collaborators)
        return manga

    def update(self, instance, validated_data):
        tags = validated_data.pop("tags", None)
        collaborators = validated_data.pop("collaborators", [])

        for attr, value in validated_data.items():
            if attr == "image":
                value.name = f"{uuid.uuid4().hex}{PurePosixPath(value.name).suffix}"
                instance.image.delete(save=False)
            setattr(instance, attr, value)

        if tags:
            instance.tags.set(tags)
            instance.is_original = 1 in tags  # 1 is the original tag id
        if collaborators:
            instance.collaborators.set(collaborators)

        instance.save()
        return instance


class CreateMangaCommentSerializer(serializers.ModelSerializer):
    comment = serializers.CharField(
        validators=[
            validate_text(
                "comment", min_len=MANGA_MIN_COMMENT_LEN, max_len=MANGA_MAX_COMMENT_LEN
            )
        ]
    )
    parent_comment_id = serializers.IntegerField()

    class Meta:
        model = MangaComment
        fields = ("parent_comment_id", "comment")

    def validate(self, data):
        # -1 means no parent comment
        parent_comment_id = data.get("parent_comment_id", -1)
        if parent_comment_id != -1:
            parent_comment = MangaComment.objects.filter(id=parent_comment_id).first()

            if not parent_comment:
                raise serializers.ValidationError(
                    {"parent_comment_id": "Parent comment not found."}
                )

            current_manga = self.context.get("manga")
            if parent_comment.manga != current_manga:
                raise serializers.ValidationError(
                    {
                        "parent_comment_id": "You cant reply to to a comment from another manga."
                    }
                )

            # put it into validated_data
            data["parent_comment"] = parent_comment

        return data

    def create(self, validated_data):
        manga = self.context["manga"]
        profile = self.context["profile"]

        parent_comment = validated_data.get("parent_comment", None)
        comment = validated_data.get("comment")

        return MangaComment.objects.create(
            manga=manga, profile=profile, parent_comment=parent_comment, comment=comment
        )
