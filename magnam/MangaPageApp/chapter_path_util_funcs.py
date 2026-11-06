from pathlib import PurePosixPath
from django.conf import settings


def get_chapter_upload_folder_path(chapter_obj):
    return PurePosixPath(
            settings.MANGAS_MEDIA_FOLDERNAME,
            chapter_obj.manga.folder_name,
            chapter_obj.folder_name,
        ).as_posix()


def get_manga_upload_folder_path(manga_obj):
    # returns relative path for file uploads: "settings.MANGAS_MEDIA_FOLDERNAME/<uuid>"
    return PurePosixPath(settings.MANGAS_MEDIA_FOLDERNAME, manga_obj.folder_name).as_posix()


def chapter_pdf_upload_to(instance, filename):
    ext = PurePosixPath(filename).suffix or ".pdf"
    return PurePosixPath(get_chapter_upload_folder_path(instance), f"original{ext}").as_posix()
