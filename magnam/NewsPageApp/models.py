import uuid

from django.db import models
from django.core.validators import MinLengthValidator
from django.db.models.signals import post_delete
from django.dispatch import receiver
from .globals import *
from django.conf import settings
from pathlib import PurePosixPath


def news_image_upload_to(instance, filename):
    ext = PurePosixPath(filename).suffix or ".png"
    return PurePosixPath(
        settings.NEWS_MEDIA_FOLDERNAME, f"{uuid.uuid4().hex}{ext}"
    ).as_posix()


class News(models.Model):
    id = models.BigAutoField(primary_key=True, editable=False)
    title = models.CharField(
        max_length=NEWS_MAX_TITLE_LEN,
        validators=[MinLengthValidator(NEWS_MIN_TITLE_LEN)],
    )
    description = models.TextField(
        max_length=NEWS_MAX_DESCRIPTION_LEN,
        validators=[MinLengthValidator(NEWS_MIN_DESCRIPTION_LEN)],
        blank=True,
        default="",
    )
    image = models.ImageField(upload_to=news_image_upload_to)
    links = models.JSONField(blank=True, default=list)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        nl = "\n"
        return f"News {nl.join(map(str, self.__dict__.items()))}"


@receiver(post_delete, sender=News)
def delete_news_image(sender, instance, **kwargs):
    if instance.image:
        instance.image.delete(save=False)