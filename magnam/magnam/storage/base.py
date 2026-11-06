from abc import ABC


class BaseStorageService(ABC):
    """
    Base class for all storage services.

    Storage paths are always POSIX relative paths.

    Examples:
        magnam_portfolios/abc123/image.webp
        magnam_mangas/xyz789/original.pdf

    These services must never expose filesystem-specific assumptions.
    """
