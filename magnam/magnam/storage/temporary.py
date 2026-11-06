from abc import abstractmethod

from .base import BaseStorageService


class TemporaryStorage(BaseStorageService):
    """
    Handles temporary local files.

    This service exists because external libraries
    (OpenCV, MoviePy, PyMuPDF, ffmpeg...)
    require filesystem access.
    """

    @abstractmethod
    def download_to_temp(self, storage_path: str):
        """
        Download a stored file to a temporary local file.

        Returns:
            Temporary filesystem path.
        """

    @abstractmethod
    def create_temp_directory(self):
        """
        Create a temporary working directory.
        """

    @abstractmethod
    def cleanup(self, path: str):
        """
        Delete temporary files/directories.
        """

    @abstractmethod
    def create_temp_file(self, suffix: str, prefix: str):
        """
        Create temporary files.
        """