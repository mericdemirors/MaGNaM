import io
import re
import uuid
from pathlib import Path, PurePosixPath
from django.conf import settings
from unittest.mock import MagicMock, patch
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase
from rest_framework import serializers

from utils.file_checks import *
from utils.helper_functions import parse_pdf_into_pages
from reportlab.pdfgen import canvas
from magnam.storage import directory_storage
from django.test import override_settings

# These tests check the correctness of file processing functions:
# parse_pdf_into_pages for pdfs and utils/file_checks.py for the rest
# they are tested to see if they reject the spoofed files correctly


class SpoofedUploadedFile(SimpleUploadedFile):
    def __init__(self, *args, spoofed_size=None, **kwargs):
        super().__init__(*args, **kwargs)
        if spoofed_size is not None:
            self.size = spoofed_size


class SizeCheckTests(SimpleTestCase):
    def setUp(self):
        self.max_size = 5 * 1024 * 1024  # 5 MB

    def test_valid_file_passes_size_check(self):
        content = b"a" * (1 * 1024 * 1024)  # 1 MB
        file = SimpleUploadedFile("small.txt", content, content_type="text/plain")

        # Should not raise
        size_check(file, self.max_size)

    def test_large_file_fails_size_check(self):
        content = b"a" * (6 * 1024 * 1024)  # 6 MB
        file = SimpleUploadedFile("large.txt", content, content_type="text/plain")

        with self.assertRaises(serializers.ValidationError) as ctx:
            size_check(file, self.max_size)

    def test_spoofed_small_metadata_but_large_real_file_fails(self):
        content = b"a" * (6 * 1024 * 1024)  # REAL = 6 MB
        file = SpoofedUploadedFile(
            "spoofed.txt",
            content,
            content_type="text/plain",
            spoofed_size=1 * 1024 * 1024,  # FAKE = 1 MB
        )

        with self.assertRaises(serializers.ValidationError) as ctx:
            size_check(file, self.max_size)

    def test_spoofed_big_metadata_small_real_file_fails(self):
        content = b"a" * (1 * 1024)  # REAL = 1 KB
        file = SpoofedUploadedFile(
            "spoofed.txt",
            content,
            content_type="text/plain",
            spoofed_size=6 * 1024 * 1024,  # FAKE = 6 MB
        )

        with self.assertRaises(serializers.ValidationError) as ctx:
            size_check(file, self.max_size)


class AudioCheckTests(SimpleTestCase):
    def setUp(self):
        self.max_size = 5 * 1024 * 1024  # 5 MB
        self.max_duration = 30  # seconds

    @patch("utils.file_checks.AudioFileClip")
    def test_valid_audio_passes(self, mock_clip_class):
        mock_clip = MagicMock()
        mock_clip.duration = 10
        mock_clip_class.return_value = mock_clip

        content = b"a" * (1 * 1024 * 1024)
        file = SimpleUploadedFile("audio.mp3", content, content_type="audio/")

        audio_check(file, max_duration=self.max_duration, max_file_size=self.max_size)

    @patch("utils.file_checks.AudioFileClip")
    def test_large_duration_audio_fails(self, mock_clip_class):
        mock_clip = MagicMock()
        mock_clip.duration = 120
        mock_clip_class.return_value = mock_clip
        content = b"a" * (1 * 1024 * 1024)

        file = SimpleUploadedFile("audio.mp3", content, content_type="audio/")

        with self.assertRaises(serializers.ValidationError) as ctx:
            audio_check(
                file, max_duration=self.max_duration, max_file_size=self.max_size
            )

    def test_spoofed_small_metadata_big_real_audio_fails(self):
        content = b"a" * (6 * 1024 * 1024)
        file = SpoofedUploadedFile(
            "audio.mp3", content, content_type="audio/", spoofed_size=1 * 1024 * 1024
        )

        with self.assertRaises(serializers.ValidationError) as ctx:
            audio_check(
                file, max_duration=self.max_duration, max_file_size=self.max_size
            )

    def test_spoofed_big_metadata_small_real_audio_fails(self):
        content = b"a" * 1024
        file = SpoofedUploadedFile(
            "audio.mp3", content, content_type="audio/", spoofed_size=6 * 1024 * 1024
        )

        with self.assertRaises(serializers.ValidationError) as ctx:
            audio_check(
                file, max_duration=self.max_duration, max_file_size=self.max_size
            )


class ImageCheckTests(SimpleTestCase):
    def test_valid_image_passes(self):
        file = SpoofedUploadedFile(
            "test.jpg", b"fake-image-bytes", content_type="image/jpeg"
        )

        with patch("utils.file_checks.Image.open") as mock_open:
            mock_img = MagicMock()
            mock_img.size = (800, 600)

            mock_open.return_value.__enter__.return_value = mock_img
            mock_open.return_value = mock_img

            image_check(
                file,
                min_width=100,
                min_height=100,
                max_width=2000,
                max_height=2000,
                max_file_size=5 * 1024 * 1024,
            )

    def test_image_too_large_fails(self):
        file = SpoofedUploadedFile("big.jpg", b"x", content_type="image/jpeg")

        with patch("utils.file_checks.Image.open") as mock_open:
            mock_img = MagicMock()
            mock_img.size = (5000, 4000)

            mock_open.return_value.__enter__.return_value = mock_img
            mock_open.return_value = mock_img

            with self.assertRaises(serializers.ValidationError) as ctx:
                image_check(
                    file, max_width=2000, max_height=2000, max_file_size=5 * 1024 * 1024
                )

    def test_spoofed_small_metadata_big_real_file_fails(self):
        # Real size: 6 MB, Spoofed size: 1 MB
        file = SpoofedUploadedFile(
            "image.jpg",
            b"a" * (6 * 1024 * 1024),
            content_type="image/jpeg",
            spoofed_size=1 * 1024 * 1024,
        )

        with self.assertRaises(serializers.ValidationError) as ctx:
            image_check(file, max_file_size=5 * 1024 * 1024)

    def test_spoofed_large_metadata_small_real_file_fails(self):
        # Real size: 1 KB, Spoofed size: 6 MB
        file = SpoofedUploadedFile(
            "image.jpg",
            b"a" * 1024,
            content_type="image/jpeg",
            spoofed_size=6 * 1024 * 1024,
        )

        with self.assertRaises(serializers.ValidationError) as ctx:
            image_check(file, max_file_size=5 * 1024 * 1024)

    def test_image_exceeds_dimensions_fails(self):
        file = SpoofedUploadedFile("image.jpg", b"fake", content_type="image/jpeg")

        with patch("utils.file_checks.Image.open") as mock_open:
            mock_img = MagicMock()
            mock_img.size = (10000, 10000)

            mock_open.return_value.__enter__.return_value = mock_img
            mock_open.return_value = mock_img

            with self.assertRaises(serializers.ValidationError) as ctx:
                image_check(
                    file, max_width=2000, max_height=2000, max_file_size=5 * 1024 * 1024
                )


class VideoCheckTests(SimpleTestCase):
    def test_valid_video_passes(self):
        file = SpoofedUploadedFile("video.mp4", b"fake-video", content_type="video/mp4")

        with patch("utils.file_checks.VideoFileClip") as mock_clip_class:
            mock_clip = MagicMock()
            mock_clip.duration = 10
            mock_clip.size = (1280, 720)
            mock_clip_class.return_value = mock_clip

            video_check(
                file,
                max_duration=30,
                max_width=1920,
                max_height=1080,
                max_file_size=5 * 1024 * 1024,
            )

    def test_video_duration_exceeds_limit(self):
        file = SpoofedUploadedFile("video.mp4", b"x", content_type="video/mp4")

        with patch("utils.file_checks.VideoFileClip") as mock_clip_class:
            mock_clip = MagicMock()
            mock_clip.duration = 120
            mock_clip.size = (1280, 720)
            mock_clip_class.return_value = mock_clip

            with self.assertRaises(serializers.ValidationError) as ctx:
                video_check(
                    file,
                    max_duration=30,
                    max_width=1920,
                    max_height=1080,
                    max_file_size=5 * 1024 * 1024,
                )

    def test_spoofed_small_metadata_big_real_video_fails(self):
        # Real size: 6 MB, Spoofed size: 1 MB
        file = SpoofedUploadedFile(
            "video.mp4",
            b"a" * (6 * 1024 * 1024),
            content_type="video/mp4",
            spoofed_size=1 * 1024 * 1024,
        )

        with self.assertRaises(serializers.ValidationError) as ctx:
            video_check(file, max_file_size=5 * 1024 * 1024)

    def test_spoofed_big_metadata_small_video_fails(self):
        # Real size: 1 KB, Spoofed size: 6 MB
        file = SpoofedUploadedFile(
            "video.mp4",
            b"a" * 1024,
            content_type="video/mp4",
            spoofed_size=6 * 1024 * 1024,
        )

        with self.assertRaises(serializers.ValidationError) as ctx:
            video_check(file, max_file_size=5 * 1024 * 1024)

    def test_video_too_large_dimensions_fails(self):
        file = SpoofedUploadedFile("video.mp4", b"x", content_type="video/mp4")

        with patch("utils.file_checks.VideoFileClip") as mock_clip_class:
            mock_clip = MagicMock()
            mock_clip.duration = 10
            mock_clip.size = (5000, 4000)
            mock_clip_class.return_value = mock_clip

            with self.assertRaises(serializers.ValidationError) as ctx:
                video_check(
                    file, max_width=1920, max_height=1080, max_file_size=5 * 1024 * 1024
                )


def generate_pdf_stream(
    filename, target_size_bytes=0, W=512, H=512, pages=5, fake_count=None
):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=(W, H))
    for i in range(pages):
        p.drawString(100, H - 100 if H else 750, f"Page {i + 1}")
        p.showPage()
    p.save()
    content = buffer.getvalue()

    # Modify /Count key directly in the raw byte array if requested
    if fake_count is not None:
        content = re.sub(
            rb"/Count\s+\d+", f"/Count {fake_count}".encode("ascii"), content
        )

    # Pad with pdf comments to inflate size accurately
    if len(content) < target_size_bytes:
        padding_size = target_size_bytes - len(content)
        content += b"\n%" + b"a" * int(padding_size - 2)

    return SimpleUploadedFile(filename, content, content_type="application/pdf")


class PdfCheckTests(SimpleTestCase):

    # pdf file with 5 pages, 512x512, file size 1MB (Limits: 2MB, 10 pages) -> PASS
    def test_regular_file_passes_validation(self):
        file = generate_pdf_stream(
            filename="regular_file.pdf", target_size_bytes=1 * 1024 * 1024, pages=5
        )
        pdf_check(file, max_file_size=5 * 1024 * 1024, max_pages=10)

    # pdf file with 5 pages, 512x512, file size 10MB (Limit: 5MB) -> FAIL
    def test_big_file_exceeds_size_limit(self):
        file = generate_pdf_stream(
            filename="big_file.pdf", target_size_bytes=10 * 1024 * 1024, pages=5
        )
        with self.assertRaises(serializers.ValidationError):
            pdf_check(file, max_file_size=5 * 1024 * 1024, max_pages=10)

    # pdf file with 5 pages, 1920x1920 layout -> PASS
    def test_high_res_file_passes_validation(self):
        file = generate_pdf_stream(
            filename="high_res_file.pdf", target_size_bytes=0, W=1920, H=1920, pages=5
        )
        pdf_check(file, max_file_size=5 * 1024 * 1024, max_pages=10)

    # pdf file with 50 pages (Limit: 10 pages) -> FAIL
    def test_long_file_exceeds_page_limit(self):
        file = generate_pdf_stream(
            filename="long_file.pdf", target_size_bytes=0, pages=50
        )
        with self.assertRaises(serializers.ValidationError) as ctx:
            pdf_check(file, max_file_size=5 * 1024 * 1024, max_pages=10)

        # These two should work but there may be some problems with the "pdf with spoofed metadata" generation
        # # Metadata claims 10 pages, but physically it has 5 pages.
        # # pdf_check falls for wrong corrupted metadata and rejects because fake_count=10>7, so FAIL
        # def test_pdf_check_falls_for_spoofed_inflated_metadata_page_number(self):
        #     file = generate_pdf_stream(
        #         filename="page_corrupted_10.pdf",
        #         target_size_bytes=1 * 1024 * 1024,
        #         pages=5,
        #         fake_count=10,
        #     )
        #     with self.assertRaises(serializers.ValidationError):
        #         pdf_check(file, max_file_size=5 * 1024 * 1024, max_pages=7)

        # # Metadata claims 5 pages, but physically it has 10 pages.
        # # pdf_check falls for wrong corrupted metadata and accepts because fake_count=5<7, so PASS
        # # ATTENTION: THIS IS NOT INTENDED BEHAVIOR. WE ARE JUST CONFIRMING THAT pdf_check HAS FLAWS AS EXPECTED
        # # WE NEED TO CONFIRM THESE FLAWS SO WE CAN HANDLE THEM CORRECTLY
        # def test_pdf_check_falls_for_spoofed_deflated_metadata_page_number(self):
        #     file = generate_pdf_stream(
        #         filename="page_corrupted_5.pdf",
        #         target_size_bytes=1 * 1024 * 1024,
        #         pages=10,
        #         fake_count=5,
        #     )
        #     pdf_check(file, max_file_size=5 * 1024 * 1024, max_pages=7)


class OnDiskPdfParseTests(SimpleTestCase):
    def setUp(self):
        super().setUp()

        self.temp_media = Path(settings.TEST_MEDIA_ROOT) / f"on_disk_pdf_parse_tests"

        self.settings_override = override_settings(MEDIA_ROOT=self.temp_media)
        self.settings_override.enable()

        self.temp_media.mkdir(parents=True, exist_ok=True)

        # Storage-relative paths
        self.test_root = PurePosixPath(f"test_{uuid.uuid4().hex}").as_posix()
        self.pages_folder = PurePosixPath(self.test_root, "pages").as_posix()

        directory_storage.create(self.test_root)
        directory_storage.create(self.pages_folder)

    def tearDown(self):
        directory_storage.delete(self.test_root)

        self.settings_override.disable()

        super().tearDown()

    def generate_pdf(
        self, filename, target_size_bytes=0, W=512, H=512, pages=5, fake_count=None
    ):
        # Storage-relative path
        pdf_storage_path = PurePosixPath(self.test_root, filename).as_posix()
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=(W, H))
        for i in range(pages):
            p.drawString(100, H - 100 if H else 750, f"Page {i + 1}")
            p.showPage()
        p.save()
        content = buffer.getvalue()

        if fake_count is not None:
            content = re.sub(
                b"/Count\s+\d+", f"/Count {fake_count}".encode("ascii"), content
            )

        if len(content) < target_size_bytes:
            padding_size = target_size_bytes - len(content)
            content += b"\n%" + b"a" * int(padding_size - 2)

        file_storage.save(pdf_storage_path, content)
        return pdf_storage_path

    def utility_function_to_test_pdf_parsing_with_temp_download(
        self, pdf_storage_path, max_pages=10, pages_folder=None
    ):
        if pages_folder is None:
            pages_folder = self.pages_folder

        pdf_temp_path = temporary_storage.download_to_temp(pdf_storage_path)
        try:
            result = parse_pdf_into_pages(
                pdf_path=pdf_temp_path,
                pages_folder=PurePosixPath(pages_folder).as_posix(),
                max_pages=max_pages,
            )

            return result

        finally:
            temporary_storage.cleanup(pdf_temp_path)

    # file with 5 pages, 512x512, file size 1MB -> Expected: True
    def test_regular_file_should_pass(self):
        pdf_path = self.generate_pdf(
            filename="regular_file.pdf",
            target_size_bytes=1 * 1024 * 1024,
            W=512,
            H=512,
            pages=5,
        )

        result, _ = self.utility_function_to_test_pdf_parsing_with_temp_download(
            pdf_storage_path=pdf_path, max_pages=10
        )

        self.assertTrue(result)

    # pdf file with 5 pages, 512x512, file size 5MB (Bypasses size restrictions) -> Expected: True
    # we dont have size check in pdf parsing, we only check file size in pdf_check util function
    def test_big_file_should_pass(self):
        pdf_path = self.generate_pdf(
            filename="big_file.pdf",
            target_size_bytes=5 * 1024 * 1024,
            W=512,
            H=512,
            pages=5,
        )

        result, _ = self.utility_function_to_test_pdf_parsing_with_temp_download(
            pdf_storage_path=pdf_path, max_pages=10
        )

        self.assertTrue(result)

    # pdf file with 5 pages, 1920x1920 layout.
    # Patches MAX_PDF_PAGE_PIXEL downward to trigger failure -> Expected: False
    def test_high_res_file_fails_on_max_pixel_check(self):
        pdf_path = self.generate_pdf(
            filename="high_res_file.pdf", target_size_bytes=0, W=1920, H=1920, pages=5
        )

        NEW_MAX_PDF_PAGE_PIXEL = 1440

        with patch("utils.helper_functions.MAX_PDF_PAGE_PIXEL", NEW_MAX_PDF_PAGE_PIXEL):
            result, _ = self.utility_function_to_test_pdf_parsing_with_temp_download(
                pdf_storage_path=pdf_path, max_pages=10
            )

        self.assertFalse(result)

    # pdf file with 50 pages (Exceeds maximum configuration limit) -> Expected: False
    def test_long_file_fails_on_max_pages_check(self):
        pdf_path = self.generate_pdf(
            filename="long_file.pdf", target_size_bytes=0, W=512, H=512, pages=50
        )

        # Setting max_pages limit lower (10) than actual content page length (50)
        result, _ = self.utility_function_to_test_pdf_parsing_with_temp_download(
            pdf_storage_path=pdf_path, max_pages=10
        )

        self.assertFalse(result)

    # Spoofed metadata file claims 10 pages, max_pages set to 7 -> Expected: False
    def test_page_corrupted_10_fails_on_max_pages_check(self):
        pdf_path = self.generate_pdf(
            filename="page_corrupted_10.pdf",
            target_size_bytes=1 * 1024 * 1024,
            W=512,
            H=512,
            pages=5,
            fake_count=10,
        )

        # Fails structural metadata limits because 10 > 7
        result, _ = self.utility_function_to_test_pdf_parsing_with_temp_download(
            pdf_storage_path=pdf_path, max_pages=7
        )

        self.assertFalse(result)

    # Spoofed metadata claims 2 pages but physically contains 5.
    # Mismatched verification -> Expected: False
    def test_page_corrupted_2_fails_on_mismatch_check(self):
        pdf_path = self.generate_pdf(
            filename="page_corrupted_2.pdf",
            target_size_bytes=1 * 1024 * 1024,
            W=512,
            H=512,
            pages=5,
            fake_count=2,
        )

        # real_page_count (5) != metadata_page_count (2)
        # causing a validation failure mismatch
        result, _ = self.utility_function_to_test_pdf_parsing_with_temp_download(
            pdf_storage_path=pdf_path, max_pages=10
        )

        self.assertFalse(result)


class TestFileExtensionValidation(SimpleTestCase):
    def test_image_check_rejects_invalid_extension(self):
        # Create an in-memory dummy file with a shell script extension
        invalid_image = SimpleUploadedFile(
            name="malicious_script.sh",
            content=b"#!/bin/bash\necho 'not an image'",
            content_type="text/x-shellscript",
        )

        with self.assertRaises(serializers.ValidationError) as ctx:
            image_check(invalid_image)

        self.assertIn("Extension 'sh' not allowed", str(ctx.exception.detail))

    def test_pdf_check_rejects_invalid_extension(self):
        invalid_pdf = SimpleUploadedFile(
            name="malicious_script.sh",
            content=b"#!/bin/bash\necho 'not a pdf'",
            content_type="text/x-shellscript",
        )

        with self.assertRaises(serializers.ValidationError) as ctx:
            pdf_check(invalid_pdf)

        self.assertIn("Extension 'sh' not allowed", str(ctx.exception.detail))

    def test_video_check_rejects_invalid_extension(self):
        invalid_video = SimpleUploadedFile(
            name="malicious_script.sh",
            content=b"#!/bin/bash\necho 'not a video'",
            content_type="text/x-shellscript",
        )

        with self.assertRaises(serializers.ValidationError) as ctx:
            video_check(invalid_video)

        self.assertIn("Extension 'sh' not allowed", str(ctx.exception.detail))

    def test_audio_check_rejects_invalid_extension(self):
        invalid_audio = SimpleUploadedFile(
            name="malicious_script.sh",
            content=b"#!/bin/bash\necho 'not an audio file'",
            content_type="text/x-shellscript",
        )

        with self.assertRaises(serializers.ValidationError) as ctx:
            audio_check(invalid_audio)

        self.assertIn("Extension 'sh' not allowed", str(ctx.exception.detail))
