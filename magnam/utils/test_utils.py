from pathlib import Path
import io
import copy
import shutil
import time
import uuid
import mimetypes

mimetypes.add_type("image/webp", ".webp")  # because webp is not native
import numpy as np
from moviepy import AudioArrayClip, ColorClip

import random
from PIL import Image
from string import ascii_uppercase
from rest_framework.test import APIClient

from reportlab.pdfgen import canvas

from django.conf import settings
from django.test import override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from ProfilePageApp.models import Profile
from django.contrib.auth.models import User
from magnam.file_extension_globals import *
from utils.helper_functions import send_verification_email
from magnam.storage import temporary_storage
import logging


def prepare_independent_test_space(tester, namespace):
    tester._start_time = time.time()
    tester.namespace = namespace
    tester.client = APIClient()

    tester._previous_logging_level = logging.root.manager.disable
    logging.disable(logging.CRITICAL)

    tester.temp_media = (
        Path(settings.TEST_MEDIA_ROOT)
        / f"{tester._testMethodName}_{uuid.uuid4().hex}"
    )

    tester.settings_override = override_settings(MEDIA_ROOT=tester.temp_media)
    tester.settings_override.enable()
    tester.temp_media.mkdir(parents=True, exist_ok=True)

    tester.admin = User.objects.create_superuser(
        username=f"admin{uuid.uuid4().hex}",
        email="admin@test.com",
        password="adminpass",
    )
    send_verification_email(
        user_email=tester.admin, token=tester.admin.profile.verification_token
    )

    tester.user = User.objects.create_user(
        username=f"user{uuid.uuid4().hex}", email="user@test.com", password="userpass"
    )
    send_verification_email(
        user_email=tester.user, token=tester.user.profile.verification_token
    )

def clear_independent_test_space(tester):
    logging.disable(tester._previous_logging_level)
    if hasattr(tester, "settings_override"):
        tester.settings_override.disable()
    if hasattr(tester, "temp_media"):
        shutil.rmtree(tester.temp_media, ignore_errors=True)
    if hasattr(tester, "_start_time"):
        duration = time.time() - tester._start_time
        print(f"\n-> {tester._testMethodName} = {duration:.4f}s")


def get_dummy_profile(seed=None):
    user = User.objects.create_user(
        username=get_dummy_text_string(seed=seed),
        email=f"{get_dummy_text_string(seed=seed)}@test.com",
        password=get_dummy_text_string(seed=seed),
    )
    send_verification_email(
        user_email=user.email, token=user.profile.verification_token
    )
    return Profile.objects.get(user=user)


def get_dummy_text_string(L=16, seed=None):
    rng = random.Random(seed) if seed is not None else random
    return "".join(rng.choice(ascii_uppercase) for _ in range(L))


def get_dummy_image_file(W, H, target_size_bytes, ext="png", seed=None):
    ext = ext.lower().replace(".", "")
    name = f"{get_dummy_text_string(seed=seed)}.{ext}"
    content_type = f"image/{'svg+xml' if ext == 'svg' else ext}"

    if ext == "svg":
        # Pillow cannot create SVGs, so we generate raw XML text
        svg_content = f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}"><rect width="100%" height="100%" fill="blue" /></svg>'
        content = svg_content.encode("utf-8")

        # pad INSIDE XML comments
        if len(content) < target_size_bytes:
            padding_size = int(target_size_bytes - len(content) - len(b"<!-- -->"))
            if padding_size > 0:
                padding = b"A" * padding_size
                content += b"<!--" + padding + b"-->"
    else:
        img = Image.new("RGB", (W, H), color="white")
        img_io = io.BytesIO()
        save_format = "JPEG" if ext in ["jpg", "jpeg"] else ext.upper()
        img.save(img_io, format=save_format)
        content = img_io.getvalue()
        if len(content) < target_size_bytes:
            content += b"\x00" * int(target_size_bytes - len(content))

    return SimpleUploadedFile(name, content, content_type)


def get_dummy_file(
    ext, target_size_bytes=0, W=100, H=100, duration=1, pages=1, seed=None
):
    """Generates a generic dummy file based on extension."""
    ext = ext.lower().replace(".", "")

    if ext in ALLOWED_IMAGE_EXTENSIONS:
        return get_dummy_image_file(W, H, target_size_bytes, ext=ext, seed=seed)

    name = f"{get_dummy_text_string(seed=seed)}.{ext}"
    content_type = mimetypes.guess_type(name)[0] or "application/octet-stream"
    content = b""

    # pdf Generation
    if ext.lower() in ALLOWED_PDF_EXTENSIONS:
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer)
        for i in range(pages):
            p.drawString(100, H - 100 if H else 750, f"Page {i + 1}")
            p.showPage()
        p.save()
        content = buffer.getvalue()

        if len(content) < target_size_bytes:
            padding_size = target_size_bytes - len(content)
            content += b"\n%" + b"a" * int(padding_size - 2)

    # Audio Generation (MP3, WAV)
    elif ext in ALLOWED_AUDIO_EXTENSIONS:
        duration = max(1, duration)
        sample_rate = 44100
        # Generate a simple 440Hz sine wave tone
        t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
        audio_data = 0.5 * np.sin(440 * 2 * np.pi * t)
        audio_array = np.vstack([audio_data, audio_data]).T
        clip = AudioArrayClip(audio_array, fps=sample_rate)

        tmp_name = temporary_storage.create_temp_file(suffix=f".{ext}")
        try:
            clip.write_audiofile(tmp_name, logger=None)
            with open(tmp_name, "rb") as f:
                content = f.read()
        finally:
            temporary_storage.cleanup(tmp_name)

        if len(content) < target_size_bytes:
            content += b"\x00" * int(target_size_bytes - len(content))

    # Video Generation (MP4, MOV, MKV)
    elif ext in ALLOWED_VIDEO_EXTENSIONS:
        duration = max(1, duration)
        clip = ColorClip(size=(W, H), color=(0, 255, 0), duration=duration)
        clip.fps = 24

        tmp_name = temporary_storage.create_temp_file(suffix=f".{ext}")
        try:
            codec = "libx264" if ext in ["mp4", "mkv"] else "mpeg4"
            clip.write_videofile(tmp_name, codec=codec, logger=None, audio=False)
            with open(tmp_name, "rb") as f:
                content = f.read()
        finally:
            temporary_storage.cleanup(tmp_name)

        if len(content) < target_size_bytes:
            content += b"\x00" * int(target_size_bytes - len(content))

    return SimpleUploadedFile(name, content, content_type)


def find_different_fields(old_instance, new_instance):
    fields = []
    for field in old_instance._meta.fields:
        old_value = field.value_from_object(old_instance)
        new_value = field.value_from_object(new_instance)
        if old_value != new_value:
            fields.append(field.name)

    return fields


def send_missing_field(
    tester, url, missing_fields=[], expected_response_code=400, predefined_vals={}
):
    _, vals_to_send_request, _ = tester.get_random_valid_data(
        predefined_vals=predefined_vals
    )
    for f in missing_fields:
        del vals_to_send_request[f]
    response = tester.client.post(url, vals_to_send_request, format="multipart")
    tester.assertEqual(response.status_code, expected_response_code)
    if expected_response_code >= 400:  # check if cause for error is the missing field
        for f in missing_fields:
            tester.assertIn(f, response.data)


def send_invalid_field(
    tester,
    url,
    field,
    invalid_value,
    expected_response_code=400,
    predefined_vals={},
    call="post",
):
    _, vals_to_send_request, _ = tester.get_random_valid_data(
        predefined_vals=predefined_vals
    )
    vals_to_send_request[field] = invalid_value
    if call == "post":
        response = tester.client.post(url, vals_to_send_request, format="multipart")
    elif (
        call == "patch"
    ):  # because we dont have 'CreateProfileView' but we need to do this with 'EditProfileView'
        response = tester.client.patch(url, vals_to_send_request, format="multipart")
    tester.assertEqual(response.status_code, expected_response_code)
    tester.assertIn(field, response.data)


def update_and_assert_single_field(
    tester,
    instance,
    update_api_url,
    field_to_update,
    new_field_value,
    field_assertion_function=None,
    expected_fields_to_differ=[],
    expected_response_code=200,
):
    """Updates a single selected field of an instance and justifies the results of the update

    Args:
        tester (Tester Class Object): Test class thats running the test
        instance (Django Model Object): Instance of the database object thats being tested
        update_api_url (String): API endpoint url for the update
        field_to_update (String): Name of the model field to update
        new_field_value (Anything): New value to update the field with
        field_assertion_function (Function): A two parametered function that checks if arguman 'actual' matches the arguman 'expected'. Defaults to None.
        expected_fields_to_differ (List): NList of values that are expected to be updates besides the 'field_to_update'
        expected_response_code (int, optional): API response code. Defaults to 200.
    """
    response = tester.client.patch(
        update_api_url, {field_to_update: new_field_value}, format="multipart"
    )
    tester.assertEqual(response.status_code, expected_response_code)

    old_instance = copy.deepcopy(instance)
    new_instance = None

    if field_assertion_function is not None:
        instance.refresh_from_db()
        new_instance = copy.deepcopy(instance)
        field_assertion_function(getattr(instance, field_to_update))

        tester.assertEqual(
            find_different_fields(old_instance, new_instance),
            expected_fields_to_differ + [field_to_update],
        )
