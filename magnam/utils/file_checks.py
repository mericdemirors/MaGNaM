from pathlib import PurePosixPath
import mimetypes
import tempfile

mimetypes.add_type("image/webp", ".webp")  # because webp is not native
from pypdf import PdfReader
from moviepy import VideoFileClip, AudioFileClip
import xml.etree.ElementTree as ET
from defusedxml.ElementTree import parse
from defusedxml.ElementTree import fromstring

from PIL import Image, ImageFile, UnidentifiedImageError

ImageFile.LOAD_TRUNCATED_IMAGES = False
MAX_IMAGE_PIXELS = 20_000_000  # ~20 MP safety cap
Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS
from django.core.files.uploadedfile import TemporaryUploadedFile
from rest_framework import serializers
from magnam.file_extension_globals import *
from magnam.storage import file_storage, temporary_storage


def format_mb(size_bytes):
    return round(size_bytes / (1024 * 1024), 2)


def get_real_file_size(file_obj, max_size=None, chunk_size=1024 * 1024):
    current_pos = file_obj.tell()
    total_size = 0

    try:
        file_obj.seek(0)

        for chunk in file_obj.chunks(chunk_size):
            total_size += len(chunk)

            if max_size and total_size > max_size:
                return total_size, True

        return total_size, False

    finally:
        file_obj.seek(current_pos)


def size_check(file, max_file_size):
    max_mb = format_mb(max_file_size)

    # check what metadata says, if its over the limit -> reject
    metadata_size = getattr(file, "size", None)
    if metadata_size is None:
        try:
            metadata_size = file.file.size
        except Exception:
            pass

    if metadata_size is not None and metadata_size > max_file_size:
        metadata_mb = format_mb(metadata_size)
        raise serializers.ValidationError(
            f"Maximum allowed file size is {max_mb} MB. Uploaded file size: {metadata_mb} MB."
        )

    # dont trust the metadata and check the size of the file content
    # if its over the limit -> reject
    try:
        real_size, exceeded = get_real_file_size(file, max_size=max_file_size)
    except Exception:
        raise serializers.ValidationError(
            f"Maximum allowed file size is {max_mb} MB. Uploaded file size: Unkown"
        )

    if exceeded:
        raise serializers.ValidationError(
            f"Maximum allowed file size is {max_mb} MB. Uploaded file size: at least {format_mb(real_size)} MB."
        )


def safe_open_image(file):
    file.seek(0)
    img = Image.open(file)
    img.verify()
    file.seek(0)
    return Image.open(file)


def parse_svg_dimensions(image):
    image.seek(0)
    tree = parse(image)
    root = tree.getroot()

    if not root.tag.endswith("svg"):
        raise ValueError("Invalid SVG root")

    def parse_dim(val):
        if not val:
            return 0
        return float("".join(c for c in val if c.isdigit() or c == "."))

    width = parse_dim(root.get("width"))
    height = parse_dim(root.get("height"))

    if (not width or not height) and root.get("viewBox"):
        vb = root.get("viewBox").split()
        if len(vb) == 4:
            width = float(vb[2])
            height = float(vb[3])

    if not width or not height:
        raise ValueError("Missing SVG dimensions")

    return width, height


def image_check(
    image,
    min_height=0,
    max_height=0,
    min_width=0,
    max_width=0,
    max_file_size=0,
    max_pixels=MAX_IMAGE_PIXELS,  # we usually have max height and width limiting this, this one is just for extra precaution
):
    ext = PurePosixPath(image.name).suffix.lower().lstrip(".")
    mime_type, _ = mimetypes.guess_type(image.name)
    image.content_type = mime_type

    if ext not in ALLOWED_IMAGE_EXTENSIONS or not (
        mime_type and mime_type.startswith("image/")
    ):
        allowed_str = ", ".join(sorted(list(ALLOWED_IMAGE_EXTENSIONS)))
        raise serializers.ValidationError(
            f"Extension '{ext}' not allowed. Valid image types are: {allowed_str}."
        )

    # check size
    size_check(image, max_file_size)

    # check dimensions
    try:
        if ext == "svg":
            width, height = parse_svg_dimensions(image)
        else:
            img = safe_open_image(image)
            width, height = img.size

    except Exception:
        raise serializers.ValidationError("Invalid image file")

    # check resolution bomb
    if width * height > max_pixels:
        raise serializers.ValidationError("Image resolution is too large.")

    if min_width and width < min_width:
        raise serializers.ValidationError(
            f"Image width must be at least {min_width}px height must be at least {min_height}px."
        )
    if min_height and height < min_height:
        raise serializers.ValidationError(
            f"Image width must be at least {min_width}px height must be at least {min_height}px."
        )
    if max_width and width > max_width:
        raise serializers.ValidationError(
            f"Image width must be at most {max_width}px height must be at most {max_height}px."
        )
    if max_height and height > max_height:
        raise serializers.ValidationError(
            f"Image width must be at most {max_width}px height must be at most {max_height}px."
        )

    image.seek(0)


def pdf_check(pdf_file, max_file_size=0, max_pages=100):
    ext = PurePosixPath(pdf_file.name).suffix.lower().lstrip(".")
    mime_type, _ = mimetypes.guess_type(pdf_file.name)

    if ext not in ALLOWED_PDF_EXTENSIONS or mime_type != "application/pdf":
        allowed_str = ", ".join(sorted(list(ALLOWED_PDF_EXTENSIONS)))
        raise serializers.ValidationError(
            f"Extension '{ext}' not allowed. Valid pdf types are: {allowed_str}."
        )

    size_check(pdf_file, max_file_size)

    # Validate pdf structure and page length
    try:
        pdf_file.seek(0)
        reader = PdfReader(pdf_file)  # Will raise if invalid pdf
        # Check page count
        if len(reader.pages) > max_pages:
            raise serializers.ValidationError(f"Max pdf length is {max_pages} pages.")

    except serializers.ValidationError:
        raise
    except Exception as e:
        raise serializers.ValidationError("Uploaded file is not a valid pdf")

    pdf_file.seek(0)  # reset pointer

    """ 
        Here is another version which is slower because it parses the pdf bytes instead of trusting the metadata
        
        # with a path

            from pdfminer.high_level import extract_pages
            pages = list(extract_pages(file_path))
            print(f"Total physical pages found: {len(pages)}")
            # part can be used to detect hate comment or explicit text in the future when needed
            for e, page in enumerate(pages):
                print(f"Page {e} bounding box: {page.bbox}")
                for element in page:
                    if hasattr(element, "get_text"):
                        print(f"Page {e} Content: {element.get_text().strip()}")
            
        # with in memory file (code is NOT tested)

            from pdfminer.pdfparser import PDFParser
            from pdfminer.pdfdocument import PDFDocument
            from pdfminer.pdfpage import PDFPage
            # Initialize the pdfminer parser and document from the file stream
            parser = PDFParser(pdf_file)
            document = PDFDocument(parser)
            # Get an iterator of the physical pages. 
            # PDFPage.create_pages crawls the physical objects, ignoring the metadata in case its spoofed
            physical_pages = PDFPage.create_pages(document)
            # Count the pages efficiently without rendering layout text
            page_count = 0
            for _ in physical_pages:
                page_count += 1
                if page_count > max_pages:
                    raise serializers.ValidationError(
                        f"Max pdf length is {max_pages} pages."
                    )

        * for now, I'm using the pypdf one
        * I trust the metadata here to speed up the upload process for users
        * and then I check the saved file with pdfminer before parsing it to page images
        * at that point, if metadata doesn't match the page count from pdfminer we abort and delete the instance
    """


def video_check(
    video_file,
    max_duration=0,
    min_height=0,
    max_height=0,
    min_width=0,
    max_width=0,
    max_file_size=0,
):
    ext = PurePosixPath(video_file.name).suffix.lower().lstrip(".")
    mime_type, _ = mimetypes.guess_type(video_file.name)

    # Note: Some system mimetypes systems map video formats to application/ octets,
    # but standard mp4/mov/mkv reliably surface as video/
    if ext not in ALLOWED_VIDEO_EXTENSIONS or not (
        mime_type and mime_type.startswith("video/")
    ):
        allowed_str = ", ".join(sorted(list(ALLOWED_VIDEO_EXTENSIONS)))
        raise serializers.ValidationError(
            f"Extension '{ext}' not allowed. Valid video types are: {allowed_str}."
        )

    size_check(video_file, max_file_size)
    video_file.seek(0)

    tmp_name = None
    clip = None

    try:
        if isinstance(video_file, TemporaryUploadedFile):
            clip = VideoFileClip(video_file.temporary_file_path())
        else:
            suffix = PurePosixPath(video_file.name).suffix

            tmp_name = temporary_storage.create_temp_file(suffix=suffix)

            with open(tmp_name, "wb") as tmp:
                for chunk in video_file.chunks():
                    tmp.write(chunk)

            clip = VideoFileClip(tmp_name)

        duration = clip.duration
        width, height = clip.size

    except Exception:
        raise serializers.ValidationError("Uploaded file is not a valid video.")

    finally:
        if clip:
            try:
                clip.close()
            except Exception:
                pass

        if tmp_name:
            try:
                temporary_storage.cleanup(tmp_name)
            except Exception:
                pass

        video_file.seek(0)

    if max_duration and duration > max_duration:
        raise serializers.ValidationError(
            f"Video duration ({duration:.1f}s) exceeds max allowed duration of {max_duration}s."
        )

    if min_width and width < min_width:
        raise serializers.ValidationError(
            f"Video width must be at least {min_width}px height must be at least {min_height}px."
        )
    if min_height and height < min_height:
        raise serializers.ValidationError(
            f"Video width must be at least {min_width}px height must be at least {min_height}px."
        )
    if max_width and width > max_width:
        raise serializers.ValidationError(
            f"Video width must be at most {max_width}px height must be at most {max_height}px."
        )
    if max_height and height > max_height:
        raise serializers.ValidationError(
            f"Video width must be at most {max_width}px height must be at most {max_height}px."
        )

    video_file.seek(0)


def audio_check(audio_file, max_duration=0, max_file_size=0):
    ext = PurePosixPath(audio_file.name).suffix.lower().lstrip(".")
    mime_type, _ = mimetypes.guess_type(audio_file.name)

    if ext not in ALLOWED_AUDIO_EXTENSIONS or not (
        mime_type and mime_type.startswith("audio/")
    ):
        allowed_str = ", ".join(sorted(list(ALLOWED_AUDIO_EXTENSIONS)))
        raise serializers.ValidationError(
            f"Extension '{ext}' not allowed. Valid audio types are: {allowed_str}."
        )

    size_check(audio_file, max_file_size)
    audio_file.seek(0)

    tmp_name = None
    clip = None

    try:
        if isinstance(audio_file, TemporaryUploadedFile):
            clip = AudioFileClip(audio_file.temporary_file_path())
        else:
            suffix = PurePosixPath(audio_file.name).suffix
            tmp_name = temporary_storage.create_temp_file(suffix=suffix)

            with open(tmp_name, "wb") as tmp:
                for chunk in audio_file.chunks():
                    tmp.write(chunk)

            clip = AudioFileClip(tmp_name)
        duration = clip.duration
    except Exception:
        raise serializers.ValidationError("Uploaded file is not a valid audio file.")
    finally:
        if clip:
            try:
                clip.close()
            except Exception:
                pass

        if tmp_name:
            try:
                temporary_storage.cleanup(tmp_name)
            except Exception:
                pass

    if max_duration and duration > max_duration:
        raise serializers.ValidationError(
            f"Audio duration ({duration:.1f}s) exceeds max allowed duration of {max_duration}s."
        )

    audio_file.seek(0)
