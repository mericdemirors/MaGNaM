from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save
from django.db import transaction
from .models import *
from .tasks import process_pdf_task
from django.db.transaction import atomic


@receiver(pre_save, sender=Work)
def detect_pdf_change(sender, instance, **kwargs):

    if not instance.pk:
        instance._pdf_changed = True
        return

    try:
        old = Work.objects.get(pk=instance.pk)
    except Work.DoesNotExist:
        instance._pdf_changed = True
        return

    instance._pdf_changed = instance.is_pdf and (old.work_file != instance.work_file)


@receiver(post_save, sender=Work)
def create_work_folder_and_process_pdf_images(sender, instance, created, **kwargs):
    if getattr(instance, "is_pdf", False) and getattr(instance, "_pdf_changed", False):
        directory_storage.create(get_work_upload_folder_path(instance))
        # wait till DB updates
        transaction.on_commit(lambda: process_pdf_task.delay(instance.id))
