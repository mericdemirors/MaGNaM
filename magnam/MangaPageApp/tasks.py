import logging

from .models import Chapter
from celery import shared_task
from .globals import *
from .chapter_path_util_funcs import *
from utils.helper_functions import parse_pdf_into_pages
from pathlib import PurePosixPath
from magnam.storage import directory_storage, temporary_storage

logger = logging.getLogger("pdf_logger")


def process_pdf(chapter_id):
    chapter = Chapter.objects.get(id=chapter_id)
    pages_folder = PurePosixPath(
        get_chapter_upload_folder_path(chapter), "pages"
    ).as_posix()

    pdf_temp_path = None

    try:
        pdf_temp_path = temporary_storage.download_to_temp(chapter.pdf.name)

        logger.info(
            f"Starting PDF processing for chapter {chapter_id} "
            f"(manga={chapter.manga.id}, title={chapter.title})"
        )

        # cleanup old parsed pages
        directory_storage.delete(pages_folder)
        directory_storage.create(pages_folder)

        was_successfull, parse_error = parse_pdf_into_pages(
            pdf_path=pdf_temp_path,
            pages_folder=pages_folder,
            max_pages=CHAPTER_PDF_MAX_PAGE,
        )

        if was_successfull:

            webp_files = [
                f
                for f in directory_storage.list_files(pages_folder)
                if f.endswith(".webp")
            ]

            image_count = len(webp_files)

            Chapter.objects.filter(id=chapter_id).update(num_of_images=image_count)

            logger.info(
                f"PDF processed successfully for chapter {chapter_id}. "
                f"Generated {image_count} pages."
            )

        else:

            logger.warning(
                f"Malicious or invalid PDF detected for chapter {chapter_id} "
                f"from manga {chapter.manga.id}. "
                f"({chapter.no}-{chapter.title}) "
                f"File: {chapter.pdf.name}. "
                f"Parse error: {parse_error}"
            )

            Chapter.objects.filter(id=chapter_id).delete()

            raise RuntimeError(
                f"Chapter {chapter_id} dropped due to validation failure."
            )

    finally:
        if pdf_temp_path:
            temporary_storage.cleanup(pdf_temp_path)


@shared_task(
    bind=True, autoretry_for=(Chapter.DoesNotExist,), retry_backoff=True, max_retries=5
)
def process_pdf_task(self, chapter_id):
    try:
        process_pdf(chapter_id)
    except Exception as e:
        logger.exception(f"PDF processing failed for chapter {chapter_id}: {e}")

        raise
