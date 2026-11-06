from pathlib import Path, PurePosixPath
from tempfile import TemporaryDirectory, NamedTemporaryFile
from shutil import copyfileobj, rmtree
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from ..files import FileStorage
from ..directories import DirectoryStorage
from ..temporary import TemporaryStorage


class LocalFileStorage(FileStorage):
    def save(self, path: str, content):
        if isinstance(content, bytes):
            content = ContentFile(content)
        return default_storage.save(path, content)

    def open(self, path: str, mode="rb"):
        return default_storage.open(path, mode)

    def delete(self, path: str):
        if default_storage.exists(path):
            default_storage.delete(path)

    def exists(self, path: str):
        return default_storage.exists(path)

    def url(self, path: str):
        return default_storage.url(path)

    def size(self, path: str):
        return default_storage.size(path)

    def copy(self, source: str, destination: str):
        with default_storage.open(source, "rb") as src:
            default_storage.save(destination, src)

    def move(self, source: str, destination: str):
        self.copy(source, destination)
        self.delete(source)


class LocalDirectoryStorage(DirectoryStorage):
    def _absolute(self, directory: str) -> Path:
        return Path(default_storage.path(directory))

    def exists(self, directory: str):
        return self._absolute(directory).exists()

    def create(self, directory: str):
        self._absolute(directory).mkdir(parents=True, exist_ok=True)

    def delete(self, directory: str):
        rmtree(self._absolute(directory), ignore_errors=True)

    def clear(self, directory: str):
        path = self._absolute(directory)
        if not path.exists():
            return
        for child in path.iterdir():
            if child.is_dir():
                rmtree(child)
            else:
                child.unlink()

    def list_files(self, directory: str):
        path = self._absolute(directory)
        if not path.exists():
            return []
        return [p.name for p in path.iterdir() if p.is_file()]

    def count_files(self, directory: str):
        return len(self.list_files(directory))

    def list_recursive(self, directory: str):
        path = self._absolute(directory)
        if not path.exists():
            return []
        return [
            str(p.relative_to(path)).replace("\\", "/")
            for p in path.rglob("*")
            if p.is_file()
        ]

    def url(self, directory: str):
        return (
            default_storage.url(PurePosixPath(directory).as_posix()).rstrip("/") + "/"
        )


class LocalTemporaryStorage(TemporaryStorage):
    def download_to_temp(self, storage_path: str):
        suffix = Path(storage_path).suffix
        tmp_name = self.create_temp_file(suffix=suffix)

        with default_storage.open(storage_path, "rb") as src:
            with open(tmp_name, "wb") as dst:
                copyfileobj(src, dst)

        return tmp_name

    def create_temp_directory(self):
        return TemporaryDirectory()

    def cleanup(self, path: str):
        path = Path(path)
        if not path.exists():
            return
        if path.is_dir():
            rmtree(path)
        else:
            path.unlink()

    def create_temp_file(self, suffix: str = "", prefix: str = ""):
        tmp = NamedTemporaryFile(delete=False, suffix=suffix, prefix=prefix)
        tmp.close()
        return tmp.name
