import logging

from .models import Work
from celery import shared_task
from .globals import *
from .work_path_util_funcs import *
from utils.helper_functions import parse_pdf_into_pages
from pathlib import PurePosixPath
from magnam.storage import directory_storage, temporary_storage

logger = logging.getLogger("pdf_logger")


def process_pdf(work_id):
    work = Work.objects.get(id=work_id)
    work_folder = get_work_upload_folder_path(work)
    pages_folder = PurePosixPath(work_folder, "pages").as_posix()
    pdf_temp_path = None

    try:
        pdf_temp_path = temporary_storage.download_to_temp(work.work_file.name)

        # cleanup
        directory_storage.delete(pages_folder)
        directory_storage.create(pages_folder)

        was_successfull, parse_error = parse_pdf_into_pages(
            pdf_path=pdf_temp_path,
            pages_folder=pages_folder,
            max_pages=WORK_PDF_MAX_PAGE,
        )

        if was_successfull:

            webp_files = [
                f
                for f in directory_storage.list_files(pages_folder)
                if f.endswith(".webp")
            ]

            Work.objects.filter(id=work_id).update(num_of_images=len(webp_files))

        else:

            logger.warning(
                f"Malicious or invalid PDF detected for work {work_id} "
                f"from portfolio {work.portfolio.id}. "
                f"File: {work.work_file.name}. "
                f"Parse error: {parse_error}"
            )

            Work.objects.filter(id=work_id).delete()

            raise RuntimeError(f"Work {work_id} dropped due to validation failure.")

    finally:
        if pdf_temp_path:
            temporary_storage.cleanup(pdf_temp_path)


@shared_task(
    bind=True, autoretry_for=(Work.DoesNotExist,), retry_backoff=True, max_retries=5
)
def process_pdf_task(self, work_id):
    try:
        process_pdf(work_id)
    except Exception as e:
        logger.exception(f"PDF processing failed for work {work_id}: {e}")

        raise
