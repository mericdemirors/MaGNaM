from pathlib import PurePosixPath
import uuid
from django.utils import timezone

from django.db import models
from django.core.validators import (
    MinLengthValidator,
    MinValueValidator,
    MaxValueValidator,
)
from django.contrib.postgres.indexes import GinIndex

from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver

from ProfilePageApp.models import Profile

from .chapter_path_util_funcs import *
from .globals import *
from magnam.storage import directory_storage, file_storage


class MangaTag(models.Model):
    id = models.BigAutoField(primary_key=True, editable=False)
    label = models.CharField(max_length=MANGA_TAG_LABEL_LEN, unique=True)

    def __str__(self):
        nl = "\n"
        return f"MangaTag {nl.join(map(str, self.__dict__.items()))}"


def manga_image_upload_to(instance, filename):
    ext = PurePosixPath(filename).suffix or ".png"
    return PurePosixPath(
        get_manga_upload_folder_path(instance), f"{uuid.uuid4().hex}{ext}"
    ).as_posix()


class Manga(models.Model):
    id = models.BigAutoField(primary_key=True, editable=False)
    title = models.CharField(
        max_length=MANGA_MAX_TITLE_LEN,
        validators=[MinLengthValidator(MANGA_MIN_TITLE_LEN)],
    )
    description = models.TextField(
        max_length=MANGA_MAX_DESCRIPTION_LEN,
        validators=[MinLengthValidator(MANGA_MIN_DESCRIPTION_LEN)],
    )
    image = models.ImageField(upload_to=manga_image_upload_to)

    # who is the primary owner and has the authority over the manga folder
    # ! we do models.DO_NOTHING because it is handled in the handle_profile_deletion signal
    owner = models.ForeignKey(
        Profile, on_delete=models.DO_NOTHING, related_name="mangas_owned"
    )  # profile.mangas_owned returns mangas_owned that belong to the profile
    # who are second-hand owners that are allowed to take decisions on the sub-folder level such as chapter submit/delete
    collaborators = models.ManyToManyField(
        Profile, related_name="mangas_collaborated", blank=True
    )  # profile.mangas_collaborated returns mangas_collaborated that belong to the profile

    folder_name = models.CharField(
        max_length=MANGA_FOLDER_NAME_LEN, editable=False
    )  # name of the folder with unique uuid
    start_date = models.DateField(auto_now_add=True)
    last_update_date = models.DateField(auto_now=True)

    tags = models.ManyToManyField(MangaTag, related_name="mangas")
    is_original = models.BooleanField(default=False)

    class Meta:
        ordering = ["-id"]

        indexes = [
            GinIndex(
                fields=["title"],
                name="manga_title_trgm_idx",
                opclasses=["gin_trgm_ops"],
            )
        ]

    def __str__(self):
        nl = "\n"
        return f"Manga {nl.join(map(str, self.__dict__.items()))}"


@receiver(pre_save, sender=Manga)
def generate_manga_folder(sender, instance, **kwargs):
    # generate an UUID folder name for the first time entry is being saved to db
    # any other save after the first one should not trigger this
    if not instance.pk and not instance.folder_name:
        folder_name = uuid.uuid4().hex
        while sender.objects.filter(folder_name=folder_name).exists():
            folder_name = uuid.uuid4().hex
        instance.folder_name = folder_name


@receiver(post_save, sender=Manga)
def create_manga_folder(sender, instance, created, **kwargs):
    if created:
        directory_storage.create(get_manga_upload_folder_path(instance))


@receiver(post_delete, sender=Manga)
def delete_manga_folder(sender, instance, **kwargs):
    if instance.image:
        instance.image.delete(save=False)
    folder_path = get_manga_upload_folder_path(instance)
    directory_storage.delete(folder_path)


class MangaRating(models.Model):
    id = models.BigAutoField(primary_key=True, editable=False)
    manga = models.ForeignKey(
        Manga, on_delete=models.CASCADE, related_name="ratings"
    )  # manga.ratings returns ratings that belong to the manga
    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="manga_ratings"
    )  # profile.ratings returns ratings that belong to the profile
    score = models.SmallIntegerField(
        default=0,
        validators=[
            MinValueValidator(MANGA_MIN_RATING),
            MaxValueValidator(MANGA_MAX_RATING),
        ],
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["manga", "profile"], name="unique_manga_rating"
            )
        ]
        ordering = ["-id"]

    def __str__(self):
        nl = "\n"
        return f"MangaRating {nl.join(map(str, self.__dict__.items()))}"


class MangaComment(models.Model):
    id = models.BigAutoField(primary_key=True, editable=False)
    manga = models.ForeignKey(Manga, on_delete=models.CASCADE, related_name="comments")
    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="manga_comments"
    )
    parent_comment = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="child_comments",
    )
    comment = models.CharField(
        max_length=MANGA_MAX_COMMENT_LEN,
        validators=[MinLengthValidator(MANGA_MIN_COMMENT_LEN)],
    )

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        nl = "\n"
        return f"MangaComment {nl.join(map(str, self.__dict__.items()))}"


# === Chapter === # === Chapter === # === Chapter === # === Chapter === #


class Chapter(models.Model):
    id = models.BigAutoField(primary_key=True, editable=False)
    title = models.CharField(
        max_length=CHAPTER_MAX_TITLE_LEN,
        validators=[MinLengthValidator(CHAPTER_MIN_TITLE_LEN)],
    )
    no = models.CharField(
        max_length=CHAPTER_MAX_NO_LEN,
        validators=[MinLengthValidator(CHAPTER_MIN_NO_LEN)],
    )

    manga = models.ForeignKey(
        Manga, on_delete=models.CASCADE, related_name="chapters"
    )  # manga.chapters returns chapters that belong to the manga

    # who is the primary owner and has the authority over the chapter
    # ! we do models.DO_NOTHING because it is handled in the handle_profile_deletion signal
    owner = models.ForeignKey(
        Profile, on_delete=models.DO_NOTHING, related_name="chapters_owned"
    )  # profile.chapters_owned returns chapters_owned that belong to the profile
    # who are the collaborators for the chapters creation such as background artist, tone filler artist etc.
    collaborators = models.ManyToManyField(
        Profile, related_name="chapters_collaborated", blank=True
    )  # profile.chapters_collaborated returns chapters_collaborated that belong to the profile

    folder_name = models.CharField(max_length=CHAPTER_FOLDER_NAME_LEN, editable=False)
    num_of_images = models.PositiveIntegerField(
        default=0, validators=[MaxValueValidator(CHAPTER_PDF_MAX_PAGE)]
    )

    pdf = models.FileField(upload_to=chapter_pdf_upload_to)
    publish_date = models.DateField(auto_now_add=True)
    price = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["manga", "no"], name="unique_manga_chapter_no"
            )
        ]

    def __str__(self):
        nl = "\n"
        return f"Chapter {nl.join(map(str, self.__dict__.items()))}"


@receiver(pre_save, sender=Chapter)
def generate_chapter_folder(sender, instance, **kwargs):
    # generate an UUID folder name for the first time entry is being saved to db
    # any other save after the first one should not trigger this
    if not instance.pk and not instance.folder_name:
        folder_name = uuid.uuid4().hex
        while sender.objects.filter(folder_name=folder_name).exists():
            folder_name = uuid.uuid4().hex

        instance.folder_name = folder_name


@receiver(post_save, sender=Chapter)
def update_manga_timestamp(sender, instance, **kwargs):
    Manga.objects.filter(id=instance.manga_id).update(
        last_update_date=timezone.now().date()
    )


@receiver(post_delete, sender=Chapter)
def delete_chapter_folder(sender, instance, **kwargs):
    if instance.pdf:
        instance.pdf.delete(save=False)
    try:
        folder_path = get_chapter_upload_folder_path(instance)
        directory_storage.delete(folder_path)
    except Manga.DoesNotExist as e:
        # in these cases manga being deleted deletes everything under it, including the chapter folder that we were about to delete
        pass


class BoughtChapter(models.Model):
    id = models.BigAutoField(primary_key=True, editable=False)
    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="bought_chapters"
    )
    chapter = models.ForeignKey(
        Chapter, on_delete=models.CASCADE, related_name="buyers"
    )
    paid_price = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["profile", "chapter"], name="unique_profile_chapter_buy"
            )
        ]

    def __str__(self):
        nl = "\n"
        return f"BoughtChapter {nl.join(map(str, self.__dict__.items()))}"


class ReadChapter(models.Model):
    id = models.BigAutoField(primary_key=True, editable=False)
    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="read_chapters"
    )
    chapter = models.ForeignKey(
        Chapter, on_delete=models.CASCADE, related_name="readers"
    )

    class Meta:
        ordering = ["-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["profile", "chapter"], name="unique_profile_chapter_read"
            )
        ]

    def __str__(self):
        nl = "\n"
        return f"ReadChapter {nl.join(map(str, self.__dict__.items()))}"


class MangaBookmark(models.Model):
    id = models.BigAutoField(primary_key=True, editable=False)
    manga = models.ForeignKey(Manga, on_delete=models.CASCADE, related_name="bookmarks")
    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="manga_bookmarks"
    )
    chapter = models.ForeignKey(
        Chapter, on_delete=models.CASCADE, related_name="bookmarkers"
    )
    page = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["manga", "profile"], name="unique_manga_bookmark"
            )
        ]
        ordering = ["-id"]

    def __str__(self):
        nl = "\n"
        return f"MangaBookmark {nl.join(map(str, self.__dict__.items()))}"
