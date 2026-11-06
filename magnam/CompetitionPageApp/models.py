import uuid

from django.db import models
from django.core.validators import MinLengthValidator
from django.db.models.signals import post_delete
from django.dispatch import receiver

from MangaPageApp.models import Chapter
from PortfolioPageApp.models import Portfolio
from .globals import *
from django.conf import settings
from pathlib import PurePosixPath


class CompetitionTag(models.Model):
    id = models.BigAutoField(primary_key=True, editable=False)
    label = models.CharField(max_length=COMPETITION_TAG_LABEL_LEN, unique=True)

    def __str__(self):
        nl = "\n"
        return f"CompetitionTag {nl.join(map(str, self.__dict__.items()))}"


def competition_image_upload_to(instance, filename):
    ext = PurePosixPath(filename).suffix or ".png"
    return PurePosixPath(
        settings.COMPETITIONS_MEDIA_FOLDERNAME, f"{uuid.uuid4().hex}{ext}"
    ).as_posix()


class Competition(models.Model):
    id = models.BigAutoField(primary_key=True, editable=False)
    title = models.CharField(
        max_length=COMPETITION_MAX_TITLE_LEN,
        validators=[MinLengthValidator(COMPETITION_MIN_TITLE_LEN)],
    )
    description = models.TextField(
        max_length=COMPETITION_MAX_DESCRIPTION_LEN,
        validators=[MinLengthValidator(COMPETITION_MIN_DESCRIPTION_LEN)],
    )
    image = models.ImageField(upload_to=competition_image_upload_to)
    links = models.JSONField(blank=True, default=list)

    start_date = models.DateField()
    price = models.PositiveIntegerField(default=0)
    end_date = models.DateField()

    tags = models.ManyToManyField(CompetitionTag, related_name="competitions")

    chapter_submits = models.ManyToManyField(
        Chapter, related_name="competition_submits", blank=True
    )  # chapter.competition_submits returns competitions that chapter is submitted
    portfolio_submits = models.ManyToManyField(
        Portfolio, related_name="competition_submits", blank=True
    )  # portfolio.competition_submits returns competitions that portfolio is submitted
    chapter_wins = models.ManyToManyField(
        Chapter, related_name="competition_wins", blank=True
    )  # chapter.competition_wins returns competitions that chapter has won
    portfolio_wins = models.ManyToManyField(
        Portfolio, related_name="competition_wins", blank=True
    )  # portfolio.competition_wins returns competitions that portfolio has won

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        nl = "\n"
        return f"Competition {nl.join(map(str, self.__dict__.items()))}"


@receiver(post_delete, sender=Competition)
def delete_news_image(sender, instance, **kwargs):
    if instance.image:
        instance.image.delete(save=False)
