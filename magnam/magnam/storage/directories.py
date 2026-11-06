from abc import abstractmethod

from .base import BaseStorageService


class DirectoryStorage(BaseStorageService):
    """
    Handles logical directory operations.

    These map to folders locally and object prefixes in cloud storage.
    """

    @abstractmethod
    def exists(self, directory: str) -> bool:
        """
        Check whether a logical directory exists.
        """

    @abstractmethod
    def create(self, directory: str):
        """
        Create a logical directory.
        """

    @abstractmethod
    def delete(self, directory: str):
        """
        Delete an entire logical directory.
        """

    @abstractmethod
    def clear(self, directory: str):
        """
        Delete contents while keeping the directory.
        """

    @abstractmethod
    def list_files(self, directory: str):
        """
        List files directly inside the directory.
        """

    @abstractmethod
    def list_recursive(self, directory: str):
        """
        List every file under a directory tree.
        """

    @abstractmethod
    def count_files(self, directory: str):
        """
        Count files.
        """

    @abstractmethod
    def url(self, directory: str):
        """
        Returns directory url.
        """
