import uuid
from django.db import models
from django.db.models import Q, F
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinLengthValidator
from django.contrib.postgres.indexes import GinIndex

from utils.helper_functions import get_new_verification_token
from .globals import *
from django.db.models.signals import pre_delete, post_delete
from django.dispatch import receiver
from django.conf import settings

import logging
from pathlib import PurePosixPath

logger = logging.getLogger("profile_logger")


def profile_image_upload_to(instance, filename):
    ext = PurePosixPath(filename).suffix or ".png"
    return PurePosixPath(
        settings.PROFILES_MEDIA_FOLDERNAME, f"{uuid.uuid4().hex}{ext}"
    ).as_posix()


class Profile(models.Model):
    id = models.BigAutoField(primary_key=True, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    profile_name = models.CharField(
        max_length=PROFILE_MAX_NAME_LEN,
        validators=[MinLengthValidator(PROFILE_MIN_NAME_LEN)],
        unique=True,
    )

    # * Every profile has multiple of items in these relations:
    # *     mangas_owned
    # *     mangas_collaborated
    # *     chapters_owned
    # *     chapters_collaborated
    # *     portfolios

    profiles_following = models.ManyToManyField(
        "self", symmetrical=False, blank=True, related_name="followers"
    )
    profiles_blocked = models.ManyToManyField(
        "self", symmetrical=False, blank=True, related_name="blocked_by"
    )
    mangas_following = models.ManyToManyField(
        "MangaPageApp.Manga", blank=True, related_name="followers"
    )

    image = models.ImageField(upload_to=profile_image_upload_to)
    wallet = models.IntegerField(default=0)
    open_date = models.DateField(auto_now_add=True)

    verification_token = models.CharField(
        max_length=PROFILE_VERIFICATION_TOKEN_LEN, null=True, blank=True
    )
    is_verified = models.BooleanField(default=False)
    non_verified_since = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    auth_provider = models.CharField(
        max_length=16,
        choices=[("local", "local"), ("google", "google")],
        default="local",
    )

    class Meta:
        ordering = ["-id"]

        indexes = [
            GinIndex(
                fields=["profile_name"],
                name="profile_name_trgm_idx",
                opclasses=["gin_trgm_ops"],
            )
        ]

    def __str__(self):
        nl = "\n"
        return f"Profile {nl.join(map(str, self.__dict__.items()))}"

    def mark_unverified(self):
        was_verified = self.is_verified

        new_token = get_new_verification_token(PROFILE_VERIFICATION_TOKEN_LEN)
        self.verification_token = new_token
        update_fields = ["verification_token"]

        if self.is_verified:
            self.is_verified = False
            update_fields += ["is_verified"]

        if self.non_verified_since is None:
            self.non_verified_since = timezone.now()
            update_fields += ["non_verified_since"]

        if self.auth_provider != "local":
            self.auth_provider = "local"
            update_fields += ["auth_provider"]

        if was_verified:
            logger.info(
                f"Profile unverified: profile[{self.id}] "
                f"{self.profile_name} {self.user.email}."
            )

        return update_fields, new_token

    def mark_verified(self):
        was_verified = self.is_verified

        self.is_verified = True
        self.verification_token = None
        self.non_verified_since = None
        update_fields = ["is_verified", "verification_token", "non_verified_since"]

        if not was_verified:
            logger.info(
                f"Profile verified: profile[{self.id}] "
                f"{self.profile_name} {self.user.email}."
            )

        return update_fields


@receiver(pre_delete, sender=User)
def log_user_and_profile_deletion(sender, instance, **kwargs):
    try:
        profile = instance.profile
        logger.info(
            f"Deleting User with profile[{profile.id}]: {profile.profile_name} {instance.email}."
        )
    except User.profile.RelatedObjectDoesNotExist:
        logger.info(f"Deleting User: {instance.email} (No profile found)")


@receiver(post_delete, sender=Profile)
def delete_profile_image_on_delete(sender, instance, **kwargs):
    if instance.image:
        instance.image.delete(save=False)


class ProfileMessage(models.Model):
    id = models.BigAutoField(primary_key=True, editable=False)
    sender = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="messages_sent"
    )
    receiver = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="messages_received"
    )
    message = models.CharField(
        max_length=PROFILE_MESSAGE_MAX_LEN,
        validators=[MinLengthValidator(PROFILE_MESSAGE_MIN_LEN)],
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["-id"]
        constraints = [
            models.CheckConstraint(
                condition=~Q(sender=F("receiver")),
                name="message_sender_not_equals_receiver",
            )
        ]

    def __str__(self):
        nl = "\n"
        return f"ProfileMessage {nl.join(map(str, self.__dict__.items()))}"
