from django.dispatch import receiver
from django.db.models.signals import post_save, pre_delete, pre_save
from django.db import transaction
from .models import *
from .tasks import process_pdf_task
from django.db.transaction import atomic


@receiver(pre_save, sender=Chapter)
def detect_pdf_change(sender, instance, **kwargs):
    if not instance.pk:
        instance._pdf_changed = True
        return

    try:
        old = Chapter.objects.get(pk=instance.pk)
    except Chapter.DoesNotExist:
        instance._pdf_changed = True
        return

    instance._pdf_changed = old.pdf != instance.pdf


@receiver(post_save, sender=Chapter)
def create_chapter_folder_and_process_pdf_images(sender, instance, created, **kwargs):
    if created:
        directory_storage.create(get_chapter_upload_folder_path(instance))
    if created or getattr(instance, "_pdf_changed", False):
        # wait till DB updates
        transaction.on_commit(lambda: process_pdf_task.delay(instance.id))


@receiver(pre_delete, sender=Profile)
def handle_profile_deletion(sender, instance, **kwargs):
    to_be_deleted_profile = instance

    with atomic():
        # 1. Remove the profile as a collaborator from all chapters it collaborated on
        for chapter in to_be_deleted_profile.chapters_collaborated.all():
            chapter.collaborators.remove(to_be_deleted_profile)

        # 2. Reassign ownership for chapters owned by the profile.
        for chapter in to_be_deleted_profile.chapters_owned.all():
            manga = chapter.manga
            new_owner = None

            # Try to pass ownership to one of the chapter collaborators (Priority 1)
            new_owner = chapter.collaborators.first()

            if new_owner:  # owned chapters are passed to chapter collaborators
                chapter.owner = new_owner
                chapter.save()
            else:  # if no chapter collaborator -> Try to pass to manga owner (Priority 2)
                manga_owner = manga.owner

                # if no chapter collaborator -> chapter ownership is passed to manga owner
                if manga_owner != to_be_deleted_profile:
                    new_owner = manga_owner
                else:  # if manga owner is the same profile with the to_be_deleted_profile -> chapter ownership is passed to one of the manga collaborators (Priority 3)
                    new_owner = manga.collaborators.exclude(
                        pk=to_be_deleted_profile.pk
                    ).first()

                if new_owner:
                    chapter.owner = new_owner
                    chapter.save()
                else:
                    chapter.delete()

        # 1. Remove the profile as a collaborator from all mangas it collaborated on.
        for manga in to_be_deleted_profile.mangas_collaborated.all():
            manga.collaborators.remove(to_be_deleted_profile)

        # 2. Reassign ownership for mangas owned by the profile.
        for (
            manga
        ) in (
            to_be_deleted_profile.mangas_owned.all()
        ):  # owned mangas are passed to manga collaborators (Priority 1)
            new_owner = manga.collaborators.exclude(pk=to_be_deleted_profile.pk).first()

            if new_owner:
                manga.owner = new_owner
                manga.save()
            else:
                manga.delete()

"""
? There is a slight possible confusion with this setup:

what happens to this:

manga M(owner:MO, collaborators: [MC1, MC2]) is created
MC1 creates a chapter to manga M as chapter C(owner: MC1, collaborators: [CC1, CC2])
MC1 deletes his own profile -> chapter C needs to be iherited -> CC1 gets the chapter C but CC1 is not manga collaborator

Now at this state everything still needs to be okay, only difference compared to a regular setup a chapter owner not being a manga collaborator
being manga collaborator = right to create new chapters (That's all)
sooo, as expected: when you inherit a chapter from a friend you naturally shouldn't get a right to create chapter on that manga

"""