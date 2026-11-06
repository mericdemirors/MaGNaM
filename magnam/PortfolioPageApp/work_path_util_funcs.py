from pathlib import PurePosixPath
import uuid
from django.conf import settings


def get_work_upload_folder_path(work_obj):
    if work_obj.is_pdf:
        return PurePosixPath(
                settings.PORTFOLIOS_MEDIA_FOLDERNAME,
                work_obj.portfolio.folder_name,
                work_obj.folder_name,
            ).as_posix()
    else:
        raise FileNotFoundError("Work has no pdf file/folder")


def get_portfolio_upload_folder_path(portfolio_obj):
    # returns relative path for file uploads: "settings.PORTFOLIOS_MEDIA_FOLDERNAME/<uuid>"
    return PurePosixPath(settings.PORTFOLIOS_MEDIA_FOLDERNAME, portfolio_obj.folder_name).as_posix()


def work_file_upload_to(instance, filename):
    ext = PurePosixPath(filename).suffix or ""
    if ext.lower() == ".pdf":
        return PurePosixPath(
                get_portfolio_upload_folder_path(instance.portfolio),
                instance.folder_name,
                f"original{ext}",
            ).as_posix()
    else:
        unique_file_name = f"{uuid.uuid4().hex}{ext}"
        return PurePosixPath(
                get_portfolio_upload_folder_path(instance.portfolio), unique_file_name
            ).as_posix()
