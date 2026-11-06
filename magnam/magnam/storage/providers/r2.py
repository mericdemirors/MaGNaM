# magnam/storage/providers/r2.py

from pathlib import PurePosixPath

from django.conf import settings
import boto3
from botocore.exceptions import ClientError

from ..directories import DirectoryStorage
from .local import LocalTemporaryStorage


class R2ClientMixin:
    """
    Shared R2 client creation.
    """

    def _get_client(self):
        return boto3.client(
            "s3",
            endpoint_url=settings.R2_ENDPOINT_URL,
            aws_access_key_id=settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
            region_name="auto",
        )


class R2DirectoryStorage(DirectoryStorage, R2ClientMixin):

    def __init__(self):
        self.client = self._get_client()
        self.bucket = settings.R2_BUCKET_NAME

    def exists(self, directory: str):
        directory = PurePosixPath(directory).as_posix().rstrip("/") + "/"

        response = self.client.list_objects_v2(
            Bucket=self.bucket, Prefix=directory, MaxKeys=1
        )

        return "Contents" in response

    def create(self, directory: str):
        """
        R2 does not create empty directories.
        Directory exists when objects exist under its prefix.
        """
        return

    def delete(self, directory: str):
        """
        Delete everything under prefix.
        """

        directory = PurePosixPath(directory).as_posix().rstrip("/") + "/"

        paginator = self.client.get_paginator("list_objects_v2")

        objects = []

        for page in paginator.paginate(Bucket=self.bucket, Prefix=directory):
            for obj in page.get("Contents", []):
                objects.append({"Key": obj["Key"]})

        if objects:
            self.client.delete_objects(Bucket=self.bucket, Delete={"Objects": objects})

    def clear(self, directory: str):
        """
        Same as delete for object storage.
        """
        self.delete(directory)

    def list_files(self, directory: str):
        """
        Returns files directly inside directory.
        Does not recurse.
        """

        directory = PurePosixPath(directory).as_posix().rstrip("/") + "/"

        response = self.client.list_objects_v2(Bucket=self.bucket, Prefix=directory)

        files = []

        for obj in response.get("Contents", []):
            relative = obj["Key"][len(directory) :]

            if "/" not in relative:
                files.append(relative)

        return files

    def count_files(self, directory: str):
        return len(self.list_files(directory))

    def list_recursive(self, directory: str):
        """
        Returns all files under prefix.
        """

        directory = PurePosixPath(directory).as_posix().rstrip("/") + "/"

        paginator = self.client.get_paginator("list_objects_v2")

        files = []

        for page in paginator.paginate(Bucket=self.bucket, Prefix=directory):
            for obj in page.get("Contents", []):
                relative = obj["Key"][len(directory) :]
                files.append(relative)

        return files

    def url(self, directory: str):
        directory = PurePosixPath(directory).as_posix().rstrip("/") + "/"

        return f"{settings.R2_PUBLIC_URL.rstrip('/')}/{directory}"


# Temporary files stay local.
# PDF/image/video libraries need real filesystem paths.
R2TemporaryStorage = LocalTemporaryStorage
