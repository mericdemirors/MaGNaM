import io
import os
import subprocess
import json
from pathlib import Path, PurePosixPath
from PIL import Image
import pandas as pd
import numpy as np
import cv2
import fitz
from django.db.models import Q
from django.conf import settings
from django.db.models import Count
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from rest_framework import serializers

from pdfminer.high_level import extract_pages
import logging

logging.getLogger("pdfminer").setLevel(logging.WARNING)
profile_logger = logging.getLogger("profile_logger")
cron_logger = logging.getLogger("cron_logger")
from concurrent.futures import ThreadPoolExecutor

from magnam.file_extension_globals import PDF_PAGE_IMAGE_NAME_FORMAT_LEN
from magnam.storage import directory_storage, file_storage


def get_qs_containing_all_tags(queryset, tag_param):
    """
    Takes a comma-separated list of tag IDs and filters the queryset
    so that it contains *all* of the given tags.
    """

    if not tag_param:
        return queryset

    tag_ids = []
    for item in tag_param.split(","):
        try:
            tag_ids.append(int(item.strip()))
        except ValueError:
            continue
    num_tags = len(tag_ids)

    # get all rows containing at least one of the tags
    # count how many of the tags does it contain
    # return the mangas that contain all selected tags
    return (
        queryset.filter(tags__id__in=tag_ids)
        .annotate(matching_tags_count=Count("tags", distinct=True))
        .filter(matching_tags_count=num_tags)
    )


def load_dataframe(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
    elif path.suffix.lower() in {".xlsx", ".xls"}:
        df = pd.read_excel(path)
    else:
        raise ValueError("Only CSV and Excel files are supported")

    df.columns = [c.lower().strip() for c in df.columns]
    return df


def parse_json_list(value):
    if pd.isna(value):
        return []
    if isinstance(value, list):
        return value
    try:
        return json.loads(value)
    except Exception:
        return [v.strip() for v in str(value).split(",")]


def convert_labels_to_ids(df, TagModel, column="tags"):
    # Build label : id mapping
    label_to_id = dict(TagModel.objects.values_list("label", "id"))

    def map_labels(value):
        tag_string_list = parse_json_list(value)
        # Convert labels → ids
        return [label_to_id[label] for label in tag_string_list if label in label_to_id]

    df[column] = df[column].apply(map_labels)
    return df


# Some serializers retrieve the owner from context.request.user.profile
# so we create a dummy class to carry the owner id from dataframe
def fake_request(profile):
    class DummyUser:
        def __init__(self, profile):
            self.profile = profile

    class DummyRequest:
        def __init__(self, profile):
            self.user = DummyUser(profile)

    return DummyRequest(profile)


def apply_registered_filters(query_params, queryset, registered_filters):
    """
    Takes a list of filters to apply on the queryset. Selects the operation based on the filter type
    and applies the filter with given values on the given attribute/arguman
    """
    filter_kwargs = {}

    for f in registered_filters:
        min_val = query_params.get(f["min_prefix"])
        max_val = query_params.get(f["max_prefix"])

        # ---- INTEGER FILTERS ----
        if f["filter_type"] == "int":
            try:
                if min_val:
                    filter_kwargs[f["min_filter_kwarg"]] = int(min_val)
                if max_val:
                    filter_kwargs[f["max_filter_kwarg"]] = int(max_val)
            except ValueError:
                continue  # ignore invalid ints

        # ---- DATE FILTERS ----
        elif f["filter_type"] == "date":
            try:
                if min_val:
                    ts = int(min_val) / 1000
                    filter_kwargs[f["min_filter_kwarg"]] = (
                        timezone.datetime.fromtimestamp(
                            ts, tz=timezone.get_current_timezone()
                        ).date()
                    )
                if max_val:
                    ts = int(max_val) / 1000
                    filter_kwargs[f["max_filter_kwarg"]] = (
                        timezone.datetime.fromtimestamp(
                            ts, tz=timezone.get_current_timezone()
                        ).date()
                    )
            except ValueError:
                continue

    if filter_kwargs:
        queryset = queryset.filter(**filter_kwargs)

    return queryset


def get_page_comments_with_cursor(base_qs, cursor, page_size):
    # Parent comments only
    parent_qs = base_qs.filter(parent_comment__isnull=True)

    # Apply keyset cursor
    if cursor:
        parent_qs = parent_qs.filter(id__lt=cursor)

    # Take last n parents
    parents = list(parent_qs[:page_size])

    if not parents:
        return base_qs.none()

    parent_ids = [p.id for p in parents]

    # return comments that are related to fetched parents
    # there may be some recent comments that respond to a very old comment
    # they are not retrieved because they seem 'unrelated' in this 'fetch the most recents' context
    # they will be fetched when their parent is fetched in further calls
    return base_qs.filter(Q(id__in=parent_ids) | Q(parent_comment_id__in=parent_ids))


# mail utils
def get_new_verification_token(L):
    return get_random_string(
        length=L,
        allowed_chars="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
    )


def send_verification_email(user_email, token):
    if settings.DISABLE_EXTERNAL_CALLS_FOR_TESTING:
        return

    verification_url = f"{settings.FRONTEND_URL}/verify/{token}/"

    subject = "Verify your account"
    message = (
        "Welcome!\n\n"
        "Please verify your account by clicking the link below:\n\n"
        f"{verification_url}\n\n"
        "If you did not create this account, you can ignore this email."
    )

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user_email],
        fail_silently=False,
    )
    profile_logger.info(f"Sending verification email to {user_email}")


def send_security_reset_email(user_email):
    if settings.DISABLE_EXTERNAL_CALLS_FOR_TESTING:
        return

    subject = "Password Reset"
    message = (
        "Hi there!\n\n"
        "We noticed that you logged in to your MaGNaM profile via google."
        "Before this login, your account WAS NOT verified so now we reset the password for security reasons."
        "If you are currenty not verified please verify your account, otherwise we'll have to keep resetting the password for your security."
    )

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user_email],
        fail_silently=False,
    )
    profile_logger.warning(f"Sending security reset email to {user_email}")


def send_cron_account_deletion_email(user_email):
    if settings.DISABLE_EXTERNAL_CALLS_FOR_TESTING:
        return

    subject = "Your account has been deleted"
    message = (
        "Hello,\n\n"
        "Your account was automatically deleted because it was not verified within the required period.\n\n"
        "Every content thats related to your account are either deleted or passed down to another rightfull owner.\n\n"
        "If you wish to use our services in the future, you are welcome to sign up again with a new account."
    )

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user_email],
        fail_silently=False,
    )
    cron_logger.info(f"Sending account deletion email to {user_email}")


# ----- ----- pdf parse utils ----- ----- #
MAX_PDF_PAGE_PIXEL = 10000
PDF_PAGE_RENDER_W = 1200
PDF_PAGE_RENDER_H = 1200
PDF_PAGE_RENDER_QUALITY = 90
PDF_PAGE_RENDER_DPI = 150


def get_metadata_page_count(pdf_path):
    result = subprocess.run(
        ["pdfinfo", pdf_path], capture_output=True, text=True, check=True
    )

    for line in result.stdout.splitlines():
        if line.startswith("Pages:"):
            return int(line.split(":")[1].strip())

    raise RuntimeError("Could not determine metadata page count")


def get_real_page_count(pdf_path, max_pages):
    pages = list(extract_pages(pdf_path))
    page_count = 0
    # we do it like this to protect agains page zip bombs
    for _ in pages:
        page_count += 1
        if page_count > max_pages:
            raise serializers.ValidationError(
                {"pdf": f"Max pdf length is {max_pages} pages."}
            )

    return page_count


def validate_rendered_page(image_bytes):
    img = Image.open(io.BytesIO(image_bytes))
    width, height = img.size
    if (
        width > MAX_PDF_PAGE_PIXEL
        or height > MAX_PDF_PAGE_PIXEL
        or width * height > (MAX_PDF_PAGE_PIXEL**2 / 10)
    ):
        return (
            False,
            f"Page resolution {(width, height)} exceeds max limit {MAX_PDF_PAGE_PIXEL}",
        )
    return (True, "")


def resize_keep_ratio_cv(img):
    h, w = img.shape[:2]

    scale = min(PDF_PAGE_RENDER_W / w, PDF_PAGE_RENDER_H / h, 1.0)

    new_w = int(w * scale)
    new_h = int(h * scale)

    return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)


def encode_webp_cv(img):
    success, encoded = cv2.imencode(
        ".webp", img, [cv2.IMWRITE_WEBP_QUALITY, PDF_PAGE_RENDER_QUALITY]
    )

    if not success:
        return None

    return encoded.tobytes()


def render_single_page(pdf_path, page_number, output_path):
    doc = None
    try:
        doc = fitz.open(pdf_path)
        page = doc.load_page(page_number - 1)

        rect = page.rect
        if rect.width > MAX_PDF_PAGE_PIXEL or rect.height > MAX_PDF_PAGE_PIXEL:
            return (False, "PDF page dimensions are too large to safely render.")

        # Render page
        pix = page.get_pixmap(dpi=PDF_PAGE_RENDER_DPI)

        arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
            (pix.height, pix.width, pix.n)
        )

        # Convert to BGR
        if pix.n == 4:
            arr = cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR)
        else:
            arr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)

        # Resize
        arr = resize_keep_ratio_cv(arr)

        # Encode WEBP in memory
        output_data = encode_webp_cv(arr)

        if not output_data:
            return (False, "Failed to encode WEBP")

        # Validate image
        is_valid, valid_error = validate_rendered_page(output_data)

        if not is_valid:
            return (False, valid_error)

        # Save
        file_storage.save(output_path, output_data)

        return (True, "")

    except Exception as e:
        return (False, str(e))
    finally:
        if doc:
            doc.close()


def parse_pdf_into_pages(
    pdf_path, pages_folder, max_pages, pad_zeros=PDF_PAGE_IMAGE_NAME_FORMAT_LEN
):
    try:
        metadata_page_count = get_metadata_page_count(pdf_path)
        if metadata_page_count > max_pages:
            return (
                False,
                f"Number of pages in the metadata {metadata_page_count} exceeds max limit {max_pages}",
            )

        real_page_count = get_real_page_count(pdf_path, max_pages)
        if real_page_count > max_pages or real_page_count != metadata_page_count:
            return (
                False,
                f"Number of pages in the real_page_count {metadata_page_count} either exceeds max limit {max_pages}, or dont match the page count from metadata {metadata_page_count}",
            )

        futures = []
        last_parsed_page_number = 0
        max_workers = max(1, (os.cpu_count() or 4) // 2)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:

            for page_i in range(1, real_page_count + 1):
                output_path = PurePosixPath(
                    pages_folder, f"{page_i - 1:0{pad_zeros}d}.webp"
                ).as_posix()

                future = executor.submit(
                    render_single_page, pdf_path, page_i, output_path
                )

                futures.append((page_i, future))

            # Collect results
            for page_i, future in futures:
                success, thread_error = future.result()
                if not success:
                    return (False, thread_error)

                last_parsed_page_number = max(last_parsed_page_number, page_i)

        if last_parsed_page_number != real_page_count:
            return (
                False,
                f"Last parsed page {last_parsed_page_number} doesn't match the page count {real_page_count}",
            )

        output_images = [
            f
            for f in directory_storage.list_files(pages_folder)
            if f.lower().endswith(".webp")
        ]

        if len(output_images) != real_page_count:
            return (
                False,
                f"Parsed images count {len(output_images)} doesn't match the page count {real_page_count}",
            )

        return (True, "")

    except Exception as e:
        return (False, str(e))
