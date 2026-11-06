import uuid
from io import BytesIO
from PIL import Image
from django.core.files.base import ContentFile

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import *

from django.contrib.auth.signals import user_logged_in
from django.contrib.sessions.models import Session
from django.utils import timezone

from utils.helper_functions import get_new_verification_token

import logging

logger = logging.getLogger("profile_logger")


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        img = Image.new("RGB", (32, 32), color="black")
        img_io = BytesIO()
        img.save(img_io, format="PNG")

        image_file = ContentFile(img_io.getvalue(), f"{uuid.uuid4().hex}.png")

        verification_token = get_new_verification_token(PROFILE_VERIFICATION_TOKEN_LEN)

        Profile.objects.create(
            user=instance,
            profile_name=instance.username,
            image=image_file,
            verification_token=verification_token,
            is_verified=False,
        )

        logger.info(f"Profile created for user: {instance.username} {instance.email}")


@receiver(post_save, sender=ProfileMessage)
def notify_receiver(sender, instance, created, **kwargs):
    if not created:
        return

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"profile_{instance.receiver.id}",
        {
            "type": "new_message",
            "message_data": {
                "id": instance.id,
                "sender": instance.sender.id,
                "receiver": instance.receiver.id,
                "message": instance.message,
                "timestamp": instance.timestamp.isoformat(),
                "is_read": instance.is_read,
            },
        },
    )


def logout_other_sessions(sender, request, user, **kwargs):
    """
    Invalidate all other sessions of this user except the current one.
    Triggered automatically whenever login(request, user) is called.
    """
    current_session_key = request.session.session_key

    # Query all active sessions
    sessions = Session.objects.filter(expire_date__gte=timezone.now())

    for session in sessions:
        data = session.get_decoded()
        # Check if session belongs to this user
        if data.get("_auth_user_id") == str(user.id):
            # Skip the current session
            if session.session_key != current_session_key:
                session.delete()  # delete the session, forcing logout


# Connect the signal
user_logged_in.connect(logout_other_sessions)
