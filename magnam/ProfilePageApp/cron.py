import logging
from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from django.contrib.auth.models import User
from .models import Profile
from .globals import *
from utils.helper_functions import send_cron_account_deletion_email

logger = logging.getLogger("cron_logger")


def delete_expired_unverified_profiles():
    """
    Notifies users and deletes profiles that:
    - are not verified
    - have a non_verified_since timestamp
    - have been unverified for more than NON_VERIFIED_PROFILE_DELETION_COUNTDOWN_DAYS days
    """
    cutoff = timezone.now() - timedelta(
        days=NON_VERIFIED_PROFILE_DELETION_COUNTDOWN_DAYS
    )

    try:
        profiles = Profile.objects.select_related("user").filter(
            is_verified=False,
            non_verified_since__isnull=False,
            non_verified_since__lt=cutoff,
        )

        deleted_name_mail = []
        user_ids = []

        for profile in profiles:
            email = profile.user.email

            # Send email before deletion while user data is still intact
            if email:
                send_cron_account_deletion_email(email)

            user_ids.append(profile.user.id)
            deleted_name_mail.append(
                f"(User: {profile.user.username}, Email: {email}) "
            )

        count = len(user_ids)

        if count:
            with transaction.atomic():
                # Perform the bulk delete
                User.objects.filter(id__in=user_ids).delete()

            # Log summary and details
            logger.info(f"CRON: Deleted {count} unverified profiles.")
            for info in deleted_name_mail:
                logger.info(f"Cleanup Detail -> {info}")
        else:
            logger.info("CRON: No expired profiles found.")

    except Exception:
        logger.exception("CRON ERROR")
