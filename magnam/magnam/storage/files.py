from abc import abstractmethod

from .base import BaseStorageService


class FileStorage(BaseStorageService):
    """
    Handles operations on individual files.
    """

    @abstractmethod
    def save(self, path: str, content):
        """
        Save a file.

        Returns:
            Final storage path.
        """

    @abstractmethod
    def open(self, path: str, mode="rb"):
        """
        Open a file.
        """

    @abstractmethod
    def delete(self, path: str):
        """
        Delete a file.
        """

    @abstractmethod
    def exists(self, path: str) -> bool:
        """
        Check whether a file exists.
        """

    @abstractmethod
    def url(self, path: str) -> str:
        """
        Return public URL for a file.
        """

    @abstractmethod
    def size(self, path: str) -> int:
        """
        Return file size.
        """

    @abstractmethod
    def copy(self, source: str, destination: str):
        """
        Copy a stored file.
        """

    @abstractmethod
    def move(self, source: str, destination: str):
        """
        Move or rename a file.
        """
