import uuid
import mimetypes

mimetypes.add_type("image/webp", ".webp")  # because webp is not native
from pathlib import Path

import pandas as pd

from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction

from PortfolioPageApp.models import Portfolio, Work
from PortfolioPageApp.serializers import CreateWorkSerializer
from utils.helper_functions import load_dataframe, parse_json_list
from utils.file_checks import *
from PortfolioPageApp.globals import *


class Command(BaseCommand):
    help = (
        "Batch CREATE / PATCH (skipped) / DELETE Works from CSV or Excel Use it with "
        "python manage.py populate_batch_works data.xlsx or python manage.py populate_batch_works data.csv"
    )

    def add_arguments(self, parser):
        parser.add_argument("file_path", type=str)

    def process_row(self, row):
        action = str(row.get("action", "")).upper()
        work_id = row.get("id")

        if action == "DELETE":
            self.handle_delete(work_id)
        elif action == "PATCH":
            self.stderr.write("PATCH not supported for Work — skipped")
        elif action == "CREATE":
            self.handle_create(row)
        else:
            raise ValueError(f"Invalid action: {action}")

    def handle_delete(self, work_id):
        if pd.isna(work_id):
            raise ValueError("DELETE requires id")

        try:
            work = Work.objects.get(id=int(work_id))
        except Work.DoesNotExist:
            self.stderr.write(f"Work {work_id} not found")
            return

        work.delete()
        self.stdout.write(f"Deleted Work {work_id}")

    def handle_create(self, row):
        portfolio = row.get("portfolio")
        if pd.isna(portfolio):
            raise ValueError("CREATE requires portfolio")

        try:
            portfolio = Portfolio.objects.get(id=int(portfolio))
        except Portfolio.DoesNotExist:
            raise ValueError(f"Portfolio {portfolio} does not exist")

        # work_files verifications are done here because we do them in the view instead of the serializer
        work_files = parse_json_list(row.get("work_files"))
        if not work_files:
            raise ValueError("CREATE requires work_files")

        if portfolio.works.count() + len(work_files) >= MAX_WORK_COUNT_PER_PORTFOLIO:
            raise ValueError(
                f"Portfolio already has {MAX_WORK_COUNT_PER_PORTFOLIO} works, cant upload {len(work_files)} more"
            )

        # file checks are done below as we do them seperately in the CreateWorkView
        serializer = CreateWorkSerializer(
            data={"title": row.get("title")}, partial=True
        )
        serializer.is_valid(raise_exception=True)

        title = serializer.validated_data.get("title", "")

        successes = 0
        errors = []

        for index, work_name in enumerate(work_files):
            try:
                if not pd.isna(work_name) and work_name:
                    work_path = (self.dataset_root / str(work_name)).resolve()

                if not work_path.exists():
                    raise ValueError("File not found")

                with work_path.open("rb") as f:
                    django_file = File(f, name=work_path.name)
                    self.validate_file(django_file)

                    # create the object without the work_file so it is initialized
                    work = Work(portfolio=portfolio, title=title)

                    # set the metadata like folder_name to be used in the work_file_upload_to function
                    ext = django_file.name.lower()
                    if ext.endswith(".pdf"):
                        work.is_pdf = True
                        work.folder_name = uuid.uuid4().hex
                        while Work.objects.filter(
                            folder_name=work.folder_name
                        ).exists():
                            work.folder_name = uuid.uuid4().hex

                    # now file can be uploaded to the correct path with folder_name (if work_file is pdf)
                    work.work_file = django_file

                    work.save()

                    successes += 1

            except Exception as e:
                errors.append({"index": index, "file": work_name, "error": str(e)})

        self.stdout.write(f"Created {successes} Works for Portfolio {portfolio.id}")

        if errors:
            self.stderr.write(f"Skipped {len(errors)} invalid files:", errors)

    def validate_file(self, file):
        content_type = getattr(file, "content_type", None)
        if not content_type:
            content_type, _ = mimetypes.guess_type(file.name)
            file.content_type = content_type

        ext = file.name.lower()

        if content_type and content_type.startswith("image/"):
            image_check(
                file,
                min_height=WORK_IMAGE_MIN_H,
                min_width=WORK_IMAGE_MIN_W,
                max_height=WORK_IMAGE_MAX_H,
                max_width=WORK_IMAGE_MAX_W,
                max_file_size=WORK_IMAGE_MAX_SIZE,
            )
        elif content_type == "application/pdf" or ext.endswith(".pdf"):
            pdf_check(
                file, max_file_size=WORK_PDF_MAX_SIZE, max_pages=WORK_PDF_MAX_PAGE
            )

        elif content_type and content_type.startswith("video/"):
            video_check(
                file,
                max_duration=WORK_VIDEO_MAX_DURATION,
                max_file_size=WORK_VIDEO_MAX_SIZE,
                min_width=WORK_VIDEO_MIN_W,
                min_height=WORK_VIDEO_MIN_H,
                max_width=WORK_VIDEO_MAX_W,
                max_height=WORK_VIDEO_MAX_H,
            )

        elif content_type and content_type.startswith("audio/"):
            audio_check(
                file,
                max_duration=WORK_AUDIO_MAX_DURATION,
                max_file_size=WORK_AUDIO_MAX_SIZE,
            )

        else:
            raise ValueError("Unsupported file type")

    @transaction.atomic
    def handle(self, *args, **options):
        file_path = Path(options["file_path"]).resolve()

        if not file_path.exists():
            self.stderr.write("File not found")
            return

        # folder containing the population info excel file and population media
        self.dataset_root = file_path.parent

        df = load_dataframe(file_path)

        df["title"] = df["title"].fillna("")

        required_cols = {"action"}
        if not required_cols.issubset(df.columns):
            self.stderr.write("Missing required columns")
            return

        for idx, row in df.iterrows():
            try:
                self.process_row(row)
            except Exception as e:
                self.stderr.write(f"Row {idx}: {e}")

        self.stdout.write(self.style.SUCCESS("Process completed"))
