# magnam/storage/backends/r2.py

from storages.backends.s3 import S3Storage
from django.conf import settings


class R2Storage(S3Storage):
    """
    Django storage backend for Cloudflare R2.

    Used as default_storage when STORAGE_PROVIDER=r2.
    """

    bucket_name = settings.R2_BUCKET_NAME

    endpoint_url = settings.R2_ENDPOINT_URL

    access_key = settings.R2_ACCESS_KEY_ID
    secret_key = settings.R2_SECRET_ACCESS_KEY

    region_name = "auto"

    custom_domain = settings.R2_PUBLIC_URL.replace("https://", "").replace(
        "http://", ""
    )

    default_acl = None

    file_overwrite = False

    querystring_auth = False
