from django.conf import settings

from .providers.local import (
    LocalFileStorage,
    LocalDirectoryStorage,
    LocalTemporaryStorage,
)

file_storage = LocalFileStorage()


if settings.STORAGE_PROVIDER == "r2":

    from .providers.r2 import R2DirectoryStorage, R2TemporaryStorage

    directory_storage = R2DirectoryStorage()
    temporary_storage = R2TemporaryStorage()

else:

    directory_storage = LocalDirectoryStorage()
    temporary_storage = LocalTemporaryStorage()
