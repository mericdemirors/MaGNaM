import uuid
import mimetypes

mimetypes.add_type("image/webp", ".webp")  # because webp is not native

from django.db import models
from django.core.validators import MinLengthValidator, MaxValueValidator

from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver

from ProfilePageApp.models import Profile

from .work_path_util_funcs import *
from .globals import *
from magnam.file_extension_globals import ALLOWED_PDF_EXTENSIONS
from magnam.storage import directory_storage, file_storage


class PortfolioTag(models.Model):
    id = models.BigAutoField(primary_key=True, editable=False)
    label = models.CharField(max_length=PORTFOLIO_TAG_LABEL_LEN, unique=True)

    def __str__(self):
        nl = "\n"
        return f"PortfolioTag {nl.join(map(str, self.__dict__.items()))}"


def portfolio_image_upload_to(instance, filename):
    ext = PurePosixPath(filename).suffix or ".png"
    return PurePosixPath(
        get_portfolio_upload_folder_path(instance), f"{uuid.uuid4().hex}{ext}"
    ).as_posix()


class Portfolio(models.Model):
    id = models.BigAutoField(primary_key=True, editable=False)
    title = models.CharField(
        max_length=PORTFOLIO_MAX_TITLE_LEN,
        validators=[MinLengthValidator(PORTFOLIO_MIN_TITLE_LEN)],
    )
    description = models.TextField(
        max_length=PORTFOLIO_MAX_DESCRIPTION_LEN,
        validators=[MinLengthValidator(PORTFOLIO_MIN_DESCRIPTION_LEN)],
        blank=True,
        default="",
    )
    image = models.ImageField(upload_to=portfolio_image_upload_to)
    owner = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="portfolios"
    )  # profile.portfolios returns portfolios that belong to the profile
    date = models.DateField(auto_now_add=True)
    folder_name = models.CharField(
        max_length=PORTFOLIO_FOLDER_NAME_LEN, editable=False
    )  # name of the folder with unique uuid
    tags = models.ManyToManyField(PortfolioTag, related_name="portfolios")

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        nl = "\n"
        return f"Portfolio {nl.join(map(str, self.__dict__.items()))}"


@receiver(pre_save, sender=Portfolio)
def generate_portfolio_folder(sender, instance, **kwargs):
    # generate an UUID folder name for the first time entry is being saved to db
    # any other save after the first one should not trigger this
    if not instance.pk and not instance.folder_name:
        folder_name = uuid.uuid4().hex
        while sender.objects.filter(folder_name=folder_name).exists():
            folder_name = uuid.uuid4().hex
        instance.folder_name = folder_name


@receiver(post_save, sender=Portfolio)
def create_portfolio_folder(sender, instance, created, **kwargs):
    if created:
        directory_storage.create(get_portfolio_upload_folder_path(instance))


@receiver(post_delete, sender=Portfolio)
def delete_portfolio_folder(sender, instance, **kwargs):
    if instance.image:
        instance.image.delete(save=False)
    folder_path = get_portfolio_upload_folder_path(instance)
    directory_storage.delete(folder_path)


class PortfolioLike(models.Model):
    id = models.BigAutoField(primary_key=True, editable=False)
    portfolio = models.ForeignKey(
        Portfolio, on_delete=models.CASCADE, related_name="likes"
    )
    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="portfolio_likes"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["portfolio", "profile"], name="unique_portfolio_like"
            )
        ]
        ordering = ["-id"]

    def __str__(self):
        nl = "\n"
        return f"PortfolioLike {nl.join(map(str, self.__dict__.items()))}"


class PortfolioComment(models.Model):
    id = models.BigAutoField(primary_key=True, editable=False)
    portfolio = models.ForeignKey(
        Portfolio, on_delete=models.CASCADE, related_name="comments"
    )
    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="portfolio_comments"
    )
    parent_comment = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="child_comments",
    )
    comment = models.CharField(
        max_length=PORTFOLIO_MAX_COMMENT_LEN,
        validators=[MinLengthValidator(PORTFOLIO_MIN_COMMENT_LEN)],
    )

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        nl = "\n"
        return f"PortfolioComment {nl.join(map(str, self.__dict__.items()))}"


# === Work === # === Work === # === Work === # === Work === #


class Work(models.Model):
    id = models.BigAutoField(primary_key=True, editable=False)
    title = models.CharField(
        max_length=WORK_MAX_TITLE_LEN,
        validators=[MinLengthValidator(WORK_MIN_TITLE_LEN)],
        blank=True,
        default="",
    )
    portfolio = models.ForeignKey(
        Portfolio, on_delete=models.CASCADE, related_name="works"
    )

    # folder name is the uuid folder name of the pdf work files
    # other type of work files are handles as normal files so they dont need a folder
    # but we parse the pdfs into individual page images so we need a folder for them
    folder_name = models.CharField(
        max_length=WORK_FOLDER_NAME_LEN, editable=False, default=""
    )
    # num_of_images is only for pdf too
    num_of_images = models.PositiveIntegerField(
        default=0, validators=[MaxValueValidator(WORK_PDF_MAX_PAGE)]
    )

    work_file = models.FileField(upload_to=work_file_upload_to)
    is_pdf = models.BooleanField(default=False, editable=False)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        nl = "\n"
        return f"Work {nl.join(map(str, self.__dict__.items()))}"


@receiver(pre_save, sender=Work)
def prepare_work_pdf_fields(sender, instance, **kwargs):
    filename = instance.work_file.name.lower()
    mime_type, _ = mimetypes.guess_type(filename)

    pdf_suffixes = tuple(f".{ext}" for ext in ALLOWED_PDF_EXTENSIONS)
    is_pdf = mime_type == "application/pdf" or filename.endswith(pdf_suffixes)

    instance.is_pdf = is_pdf

    if is_pdf:  # only pdfs get a folder
        current_folder_name = uuid.uuid4().hex
        while sender.objects.filter(folder_name=current_folder_name).exists():
            current_folder_name = uuid.uuid4().hex

        instance.folder_name = current_folder_name


@receiver(post_delete, sender=Work)
def delete_work_folder(sender, instance, **kwargs):
    if instance.work_file:
        instance.work_file.delete(save=False)
    try:
        if instance.is_pdf:
            folder_path = get_work_upload_folder_path(instance)
            directory_storage.delete(folder_path)
    except Portfolio.DoesNotExist as e:
        # in these cases Portfolio being deleted deletes everything under it, including the work folder that we were about to delete
        pass
